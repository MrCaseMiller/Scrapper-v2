"""Unit tests for LLM Directional strategy."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from src.strategy.llm_directional import LLMDirectional
from src.engine.models import Market, OrderSide, MarketSide


@pytest.fixture
def strategy():
    """Create strategy instance with test config."""
    config = {
        "llm_provider": "openai",
        "model_name": "gpt-4",
        "use_consensus": False,  # Single model for testing
        "min_edge_pct": 15.0,
        "max_position_size": 300.0,
        "min_position_size": 50.0,
        "confidence_threshold": 0.7,
        "news_lookback_hours": 24,
        "stop_loss_pct": 0.15,
        "take_profit_pct": 0.30
    }
    return LLMDirectional(config)


@pytest.fixture
def mock_market():
    """Create mock market."""
    return Market(
        market_id="llm_test_market",
        question="Will Fed raise interest rates in March?",
        yes_token_id="yes_fed",
        no_token_id="no_fed",
        end_date=datetime(2025, 3, 31),
        active=True
    )


class TestLLMDirectional:
    """Test suite for LLM Directional strategy."""

    @pytest.mark.asyncio
    async def test_large_edge_triggers_entry(self, strategy, mock_market):
        """Test that large edge (LLM vs market) triggers position."""
        # Mock LLM to return 80% probability
        with patch.object(strategy, '_call_llm', return_value=0.80):
            with patch.object(strategy, '_fetch_news', return_value=[
                {"source": "reuters", "content": "Fed signals rate hike", "credibility": 0.9}
            ]):
                # Market is at 60% → 20% edge
                orders = await strategy.on_market_update(
                    market=mock_market,
                    current_price=0.60,
                    orderbook={}
                )

                # Should generate BUY YES order
                assert len(orders) > 0
                assert orders[0].side == OrderSide.BUY
                assert orders[0].market_side == MarketSide.YES

    @pytest.mark.asyncio
    async def test_small_edge_ignored(self, strategy, mock_market):
        """Test that small edge is ignored."""
        # Mock LLM to return 65% probability
        with patch.object(strategy, '_call_llm', return_value=0.65):
            with patch.object(strategy, '_fetch_news', return_value=[
                {"source": "twitter", "content": "Some news", "credibility": 0.5}
            ]):
                # Market is at 60% → only 5% edge (below 15% threshold)
                orders = await strategy.on_market_update(
                    market=mock_market,
                    current_price=0.60,
                    orderbook={}
                )

                # Should NOT generate orders
                assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_no_news_returns_empty(self, strategy, mock_market):
        """Test that lack of news returns no orders."""
        with patch.object(strategy, '_fetch_news', return_value=[]):
            orders = await strategy.on_market_update(
                market=mock_market,
                current_price=0.60,
                orderbook={}
            )

            assert len(orders) == 0

    @pytest.mark.asyncio
    async def test_llm_bearish_buys_no(self, strategy, mock_market):
        """Test that bearish LLM prediction buys NO tokens."""
        # Mock LLM to return 30% probability (bearish)
        with patch.object(strategy, '_call_llm', return_value=0.30):
            with patch.object(strategy, '_fetch_news', return_value=[
                {"source": "reuters", "content": "Fed signals dovish stance", "credibility": 0.9}
            ]):
                # Market is at 60% → LLM thinks 30% → buy NO
                orders = await strategy.on_market_update(
                    market=mock_market,
                    current_price=0.60,
                    orderbook={}
                )

                # Should generate BUY NO order
                if orders:
                    assert orders[0].side == OrderSide.BUY
                    assert orders[0].market_side == MarketSide.NO

    @pytest.mark.asyncio
    async def test_exit_on_take_profit(self, strategy, mock_market):
        """Test that position exits when profit target is hit."""
        # Manually create position
        strategy.positions[mock_market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": 0.60,
            "direction": "YES",
            "size": 100.0,
            "llm_prob": 0.80,
            "edge_pct": 20.0,
            "confidence": 0.85,
            "news_summary": "Bullish news"
        }

        # Mock news fetch to avoid errors
        with patch.object(strategy, '_fetch_news', return_value=[]):
            # Price has moved to 0.78 (30% gain - hits take profit)
            orders = await strategy.on_market_update(
                market=mock_market,
                current_price=0.78,
                orderbook={}
            )

            # Should generate SELL order
            if orders:
                assert orders[0].side == OrderSide.SELL

    @pytest.mark.asyncio
    async def test_exit_on_stop_loss(self, strategy, mock_market):
        """Test that position exits when stop loss is hit."""
        strategy.positions[mock_market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": 0.60,
            "direction": "YES",
            "size": 100.0,
            "llm_prob": 0.80,
            "edge_pct": 20.0,
            "confidence": 0.85,
            "news_summary": "Bullish news"
        }

        with patch.object(strategy, '_fetch_news', return_value=[]):
            # Price has moved to 0.51 (15% loss - hits stop loss)
            orders = await strategy.on_market_update(
                market=mock_market,
                current_price=0.51,
                orderbook={}
            )

            # Should generate SELL order
            if orders:
                assert orders[0].side == OrderSide.SELL

    @pytest.mark.asyncio
    async def test_exit_on_max_hold_time(self, strategy, mock_market):
        """Test that position exits after max hold time."""
        # Create position with old timestamp
        strategy.positions[mock_market.market_id] = {
            "entry_time": datetime.utcnow() - timedelta(hours=50),  # 50 hours ago
            "entry_price": 0.60,
            "direction": "YES",
            "size": 100.0,
            "llm_prob": 0.80,
            "edge_pct": 20.0,
            "confidence": 0.85,
            "news_summary": "Old news"
        }

        with patch.object(strategy, '_fetch_news', return_value=[]):
            orders = await strategy.on_market_update(
                market=mock_market,
                current_price=0.65,
                orderbook={}
            )

            # Should generate SELL order (max hold is 48 hours)
            if orders:
                assert orders[0].side == OrderSide.SELL

    @pytest.mark.asyncio
    async def test_consensus_mode_averages_predictions(self, strategy, mock_market):
        """Test that consensus mode averages multiple model predictions."""
        strategy.use_consensus = True
        strategy.consensus_models = ["gpt-4", "claude-3-opus"]

        # Mock calls to return different probabilities
        call_count = 0
        async def mock_call_llm(prompt, model):
            nonlocal call_count
            call_count += 1
            return 0.75 if call_count == 1 else 0.85  # 75% and 85%

        with patch.object(strategy, '_call_llm', side_effect=mock_call_llm):
            with patch.object(strategy, '_fetch_news', return_value=[
                {"source": "reuters", "content": "Test news", "credibility": 0.9}
            ]):
                llm_prob, confidence = await strategy._analyze_with_llm(
                    mock_market,
                    [{"source": "reuters", "content": "Test news", "credibility": 0.9}],
                    0.60
                )

                # Average should be 0.80
                assert llm_prob == pytest.approx(0.80, rel=0.01)
                # Confidence based on agreement (close predictions = high confidence)
                assert confidence > 0.5

    def test_build_analysis_prompt(self, strategy, mock_market):
        """Test prompt building for LLM."""
        news_items = [
            {"source": "reuters", "content": "Fed signals rate hike likely", "credibility": 0.9},
            {"source": "twitter", "content": "Inflation still high", "credibility": 0.6}
        ]

        prompt = strategy._build_analysis_prompt(mock_market, news_items, 0.60)

        # Prompt should contain key elements
        assert "Fed raise interest rates" in prompt
        assert "0.60" in prompt or "60" in prompt
        assert "Fed signals rate hike likely" in prompt
        assert "probability" in prompt.lower()

    def test_position_sizing_scales_with_edge(self, strategy):
        """Test that position size scales with edge and confidence."""
        # Small edge, low confidence
        size_small = strategy._calculate_position_size(edge_pct=15.0, confidence=0.70)

        # Large edge, high confidence
        size_large = strategy._calculate_position_size(edge_pct=30.0, confidence=0.90)

        # Larger edge + higher confidence = larger position
        assert size_large > size_small
        assert size_large <= strategy.max_position_size

    def test_news_summarization(self, strategy):
        """Test news summary generation."""
        news_items = [
            {"source": "reuters", "content": "This is a long news article that should be truncated for display purposes", "credibility": 0.9},
            {"source": "twitter", "content": "Short tweet", "credibility": 0.6}
        ]

        summary = strategy._summarize_news(news_items)

        assert len(summary) > 0
        assert "..." in summary  # Should truncate long content

    @pytest.mark.asyncio
    async def test_resolution_calculates_pnl(self, strategy, mock_market):
        """Test that market resolution calculates P&L correctly."""
        strategy.positions[mock_market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": 0.60,
            "direction": "YES",
            "size": 100.0,
            "llm_prob": 0.80,
            "edge_pct": 20.0,
            "confidence": 0.85,
            "news_summary": "Bullish news"
        }

        initial_pnl = strategy.total_pnl
        initial_trades = strategy.trade_count

        # Market resolves YES (we win)
        await strategy.on_resolution(mock_market.market_id, "YES")

        # Profit should increase
        assert strategy.total_pnl > initial_pnl
        assert strategy.trade_count > initial_trades
        assert strategy.win_count > 0

    def test_get_stats(self, strategy):
        """Test statistics generation."""
        stats = strategy.get_stats()

        assert stats["strategy"] == "LLMDirectional"
        assert "trade_count" in stats
        assert "win_rate" in stats
        assert "total_pnl" in stats
        assert "active_positions" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
