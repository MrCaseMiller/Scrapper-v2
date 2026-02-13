"""News & LLM-Driven Directional Betting Strategy.

Uses Large Language Models to analyze news feeds and estimate "true probability"
of market outcomes, then bets directionally when market is mispriced.

How it works:
1. Ingest live news from multiple sources (X/Twitter, Reuters, Perplexity, etc.)
2. Feed news context + market question to LLM
3. LLM estimates probability based on available information
4. If LLM probability differs significantly from market → take position

Example:
  Market: "Will Fed raise rates in March?" @ 60% (0.60)

  Recent news:
  - "Inflation hits 3-year high"
  - "Fed chair signals hawkish stance"
  - "Employment data stronger than expected"

  LLM analysis: "Based on economic indicators, 85% probability of rate hike"

  Edge: 85% - 60% = 25% mispricing
  Action: BUY YES shares (expect price to rise to 85%)

Risk Management:
1. Only trade when edge > minimum threshold (e.g., 15%)
2. Position sizing based on confidence
3. Time decay - older news less valuable
4. Multiple LLM consensus (use 2-3 models, average predictions)
5. Stop loss if market moves against us

News Sources Integration:
- Twitter/X API (breaking news, sentiment)
- RSS feeds (Reuters, AP, Bloomberg)
- Perplexity API (research queries)
- Custom scrapers (Reddit, prediction market forums)
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from collections import deque
import json

from .base import Strategy
from ..engine.models import Order, OrderSide, MarketSide, Market


class LLMDirectional(Strategy):
    """
    LLM-driven directional betting strategy.

    Analyzes news and estimates true probability using LLMs.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)

        # LLM configuration
        self.llm_provider = config.get("llm_provider", "openai")  # openai, anthropic, etc.
        self.model_name = config.get("model_name", "gpt-4")
        self.use_consensus = config.get("use_consensus", True)  # Use multiple models
        self.consensus_models = config.get("consensus_models", ["gpt-4", "claude-3-opus"])

        # News source configuration
        self.news_sources = config.get("news_sources", ["twitter", "reuters", "perplexity"])
        self.news_lookback_hours = config.get("news_lookback_hours", 24)
        self.news_refresh_minutes = config.get("news_refresh_minutes", 5)

        # Trading parameters
        self.min_edge_pct = config.get("min_edge_pct", 15.0)  # 15% minimum edge
        self.max_position_size = config.get("max_position_size", 300.0)
        self.min_position_size = config.get("min_position_size", 50.0)
        self.confidence_threshold = config.get("confidence_threshold", 0.7)  # 70%+

        # Risk management
        self.stop_loss_pct = config.get("stop_loss_pct", 0.15)  # 15% stop loss
        self.take_profit_pct = config.get("take_profit_pct", 0.30)  # 30% take profit
        self.max_hold_hours = config.get("max_hold_hours", 48)  # Max 2 days

        # State tracking
        self.news_cache: Dict[str, deque] = {}  # {market_id: news_items}
        self.llm_predictions: Dict[str, dict] = {}  # {market_id: prediction_info}
        self.positions: Dict[str, dict] = {}  # {market_id: position_info}
        self.last_analysis: Dict[str, datetime] = {}  # {market_id: timestamp}

        # Performance
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0.0

    async def on_market_update(
        self,
        market: Market,
        current_price: float,
        orderbook: dict = None
    ) -> List[Order]:
        """
        Analyze market with LLM and generate directional orders.

        Args:
            market: Market object
            current_price: Current market price
            orderbook: Order book data

        Returns:
            List of orders based on LLM analysis
        """
        orders = []

        # Check if we should re-analyze
        if not self._should_analyze(market.market_id):
            # Check existing positions for exit signals
            if market.market_id in self.positions:
                return await self._check_exit(market, current_price)
            return orders

        # Fetch recent news
        news_items = await self._fetch_news(market)

        if not news_items:
            print(f"⚠️  No news available for {market.question[:50]}...")
            return orders

        # Get LLM probability estimate
        llm_probability, confidence = await self._analyze_with_llm(
            market, news_items, current_price
        )

        if llm_probability is None:
            return orders

        # Store prediction
        self.llm_predictions[market.market_id] = {
            "timestamp": datetime.utcnow(),
            "llm_prob": llm_probability,
            "market_prob": current_price,
            "confidence": confidence,
            "news_count": len(news_items)
        }

        # Calculate edge
        edge = abs(llm_probability - current_price)
        edge_pct = edge * 100

        # Check if we should trade
        if edge_pct < self.min_edge_pct:
            print(f"📊 Edge too small: {edge_pct:.1f}% < {self.min_edge_pct}%")
            return orders

        if confidence < self.confidence_threshold:
            print(f"📊 Confidence too low: {confidence:.1%} < {self.confidence_threshold:.1%}")
            return orders

        # Check if already have position
        if market.market_id in self.positions:
            return orders

        # Determine direction
        direction = "YES" if llm_probability > current_price else "NO"
        market_side = MarketSide.YES if direction == "YES" else MarketSide.NO
        token_id = market.yes_token_id if direction == "YES" else market.no_token_id

        # Calculate position size based on edge and confidence
        position_size = self._calculate_position_size(edge_pct, confidence)

        # Create order
        order = Order(
            market_id=market.market_id,
            token_id=token_id,
            side=OrderSide.BUY,
            market_side=market_side,
            size=position_size,
            price=current_price if direction == "YES" else (1 - current_price),
            order_type="MARKET"
        )

        orders.append(order)

        # Track position
        self.positions[market.market_id] = {
            "entry_time": datetime.utcnow(),
            "entry_price": current_price,
            "direction": direction,
            "size": position_size,
            "llm_prob": llm_probability,
            "edge_pct": edge_pct,
            "confidence": confidence,
            "news_summary": self._summarize_news(news_items[:3])
        }

        print(f"🤖 LLM Trade: {direction} on {market.question[:50]}...")
        print(f"   Market: {current_price:.1%}, LLM: {llm_probability:.1%}, Edge: {edge_pct:.1f}%")
        print(f"   Confidence: {confidence:.1%}, Size: ${position_size:.2f}")
        print(f"   News: {self.positions[market.market_id]['news_summary']}")

        return orders

    async def _check_exit(self, market: Market, current_price: float) -> List[Order]:
        """Check if we should exit current position."""
        orders = []
        position = self.positions.get(market.market_id)

        if not position:
            return orders

        should_exit = False
        exit_reason = ""

        # Calculate P&L
        entry_price = position["entry_price"]
        pnl_pct = ((current_price - entry_price) / entry_price) * 100

        if position["direction"] == "NO":
            pnl_pct = -pnl_pct  # Inverse for NO positions

        # Exit reason 1: Take profit
        if pnl_pct > self.take_profit_pct * 100:
            should_exit = True
            exit_reason = "Take profit hit"

        # Exit reason 2: Stop loss
        elif pnl_pct < -self.stop_loss_pct * 100:
            should_exit = True
            exit_reason = "Stop loss hit"

        # Exit reason 3: Max hold time
        time_held = (datetime.utcnow() - position["entry_time"]).seconds / 3600
        if time_held > self.max_hold_hours:
            should_exit = True
            exit_reason = "Max hold time reached"

        # Exit reason 4: Re-analysis shows no edge
        # Re-fetch news and re-analyze
        news_items = await self._fetch_news(market)
        if news_items:
            new_llm_prob, new_confidence = await self._analyze_with_llm(
                market, news_items, current_price
            )

            if new_llm_prob is not None:
                new_edge = abs(new_llm_prob - current_price) * 100

                if new_edge < self.min_edge_pct / 2:  # Edge disappeared
                    should_exit = True
                    exit_reason = "Edge disappeared (re-analysis)"

        if should_exit:
            # Create exit order
            direction = position["direction"]
            market_side = MarketSide.YES if direction == "YES" else MarketSide.NO
            token_id = market.yes_token_id if direction == "YES" else market.no_token_id

            order = Order(
                market_id=market.market_id,
                token_id=token_id,
                side=OrderSide.SELL,
                market_side=market_side,
                size=position["size"],
                price=current_price,
                order_type="MARKET"
            )

            orders.append(order)

            # Calculate actual P&L
            actual_pnl = position["size"] * (pnl_pct / 100)
            self.total_pnl += actual_pnl
            self.trade_count += 1

            if actual_pnl > 0:
                self.win_count += 1

            print(f"📤 Exit LLM position: {exit_reason}")
            print(f"   Entry: ${entry_price:.3f}, Exit: ${current_price:.3f}")
            print(f"   P&L: ${actual_pnl:+.2f} ({pnl_pct:+.1f}%)")
            print(f"   Win rate: {self.win_count}/{self.trade_count}")

            del self.positions[market.market_id]

        return orders

    def _should_analyze(self, market_id: str) -> bool:
        """Check if we should re-run LLM analysis."""
        if market_id not in self.last_analysis:
            return True

        time_since_analysis = (datetime.utcnow() - self.last_analysis[market_id]).seconds / 60

        return time_since_analysis >= self.news_refresh_minutes

    async def _fetch_news(self, market: Market) -> List[dict]:
        """
        Fetch recent news relevant to this market.

        In production, this would call:
        - Twitter API for relevant tweets
        - RSS feeds for news articles
        - Perplexity API for research
        - Custom scrapers

        For now, returns mock news structure.
        """
        # TODO: Integrate real news sources

        # Mock news for demonstration
        mock_news = [
            {
                "source": "twitter",
                "timestamp": datetime.utcnow() - timedelta(minutes=5),
                "content": "Breaking: Relevant event occurred",
                "credibility": 0.8
            },
            {
                "source": "reuters",
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "content": "Analysis suggests outcome is likely",
                "credibility": 0.95
            }
        ]

        # In production:
        # news = await self.news_fetcher.get_news(
        #     query=market.question,
        #     sources=self.news_sources,
        #     since=datetime.utcnow() - timedelta(hours=self.news_lookback_hours)
        # )

        # Cache news
        if market.market_id not in self.news_cache:
            self.news_cache[market.market_id] = deque(maxlen=50)

        for item in mock_news:
            self.news_cache[market.market_id].append(item)

        return mock_news

    async def _analyze_with_llm(
        self,
        market: Market,
        news_items: List[dict],
        current_price: float
    ) -> tuple[Optional[float], float]:
        """
        Analyze market with LLM.

        Args:
            market: Market object
            news_items: Recent news
            current_price: Current market price

        Returns:
            (llm_probability, confidence) or (None, 0.0)
        """
        self.last_analysis[market.market_id] = datetime.utcnow()

        # Build prompt
        prompt = self._build_analysis_prompt(market, news_items, current_price)

        # Call LLM(s)
        if self.use_consensus:
            # Get predictions from multiple models
            probabilities = []

            for model in self.consensus_models:
                prob = await self._call_llm(prompt, model)
                if prob is not None:
                    probabilities.append(prob)

            if not probabilities:
                return None, 0.0

            # Average probabilities
            llm_probability = sum(probabilities) / len(probabilities)

            # Confidence based on agreement
            # High agreement → high confidence
            variance = sum((p - llm_probability) ** 2 for p in probabilities) / len(probabilities)
            confidence = max(0.5, 1.0 - variance * 10)  # Lower variance = higher confidence

        else:
            llm_probability = await self._call_llm(prompt, self.model_name)

            if llm_probability is None:
                return None, 0.0

            # Single model - moderate confidence
            confidence = 0.75

        return llm_probability, confidence

    def _build_analysis_prompt(
        self,
        market: Market,
        news_items: List[dict],
        current_price: float
    ) -> str:
        """Build LLM analysis prompt."""
        news_text = "\n".join([
            f"- [{item['source']}] {item['content']}"
            for item in news_items[:10]
        ])

        prompt = f"""You are an expert analyst evaluating prediction markets.

Market Question: {market.question}
Current Market Price: {current_price:.1%} (market consensus probability)
End Date: {market.end_date}

Recent News (last {self.news_lookback_hours} hours):
{news_text}

Based on the available information, estimate the TRUE PROBABILITY of YES outcome.

Consider:
1. News credibility and recency
2. Historical patterns
3. Base rates for similar events
4. Time until resolution
5. Information asymmetry

Respond with ONLY a decimal probability (0.0 to 1.0).
Example: 0.75

Your probability estimate:"""

        return prompt

    async def _call_llm(self, prompt: str, model: str) -> Optional[float]:
        """
        Call LLM API and parse probability.

        In production, this would call OpenAI, Anthropic, etc.

        Returns:
            Probability (0.0-1.0) or None
        """
        # TODO: Integrate real LLM APIs

        # Mock LLM response for demonstration
        # In production:
        # if self.llm_provider == "openai":
        #     response = await openai.ChatCompletion.create(
        #         model=model,
        #         messages=[{"role": "user", "content": prompt}],
        #         temperature=0.2
        #     )
        #     probability_text = response.choices[0].message.content.strip()
        # elif self.llm_provider == "anthropic":
        #     ...

        # Mock: Return random probability for now
        import random
        mock_probability = random.uniform(0.3, 0.8)

        try:
            # Parse LLM response
            # probability = float(probability_text)
            probability = mock_probability

            # Validate range
            if 0.0 <= probability <= 1.0:
                return probability

        except (ValueError, AttributeError):
            pass

        return None

    def _calculate_position_size(self, edge_pct: float, confidence: float) -> float:
        """Calculate position size using Kelly-like criterion."""
        # Kelly fraction based on edge and confidence
        # f = (confidence * edge) / 100

        kelly_fraction = (confidence * edge_pct) / 100

        # Use fractional Kelly (1/3) for safety
        kelly_fraction *= 0.33

        # Scale to position size
        size_range = self.max_position_size - self.min_position_size
        position_size = self.min_position_size + (size_range * kelly_fraction)

        return round(min(self.max_position_size, position_size), 2)

    def _summarize_news(self, news_items: List[dict]) -> str:
        """Create brief news summary."""
        if not news_items:
            return "No recent news"

        summaries = [item['content'][:50] + "..." for item in news_items[:2]]
        return " | ".join(summaries)

    async def on_resolution(self, market_id: str, outcome: str):
        """Market resolved - calculate final P&L."""
        if market_id in self.positions:
            position = self.positions[market_id]

            # Did we win?
            won = position["direction"] == outcome

            pnl = position["size"] if won else -position["size"]
            self.total_pnl += pnl
            self.trade_count += 1

            if won:
                self.win_count += 1

            print(f"{'✅ WIN' if won else '❌ LOSS'}: LLM predicted {position['direction']}, actual {outcome}")
            print(f"   LLM prob: {position['llm_prob']:.1%}, Edge: {position['edge_pct']:.1f}%")
            print(f"   P&L: ${pnl:+.2f}")

            del self.positions[market_id]

    def get_stats(self) -> dict:
        """Get strategy statistics."""
        return {
            "strategy": "LLMDirectional",
            "trade_count": self.trade_count,
            "win_count": self.win_count,
            "win_rate": self.win_count / max(1, self.trade_count),
            "total_pnl": round(self.total_pnl, 2),
            "avg_pnl_per_trade": round(self.total_pnl / max(1, self.trade_count), 2),
            "active_positions": len(self.positions),
            "markets_analyzed": len(self.llm_predictions)
        }
