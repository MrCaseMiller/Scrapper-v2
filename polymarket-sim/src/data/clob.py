"""CLOB API client for orderbook and price data."""

import asyncio
from datetime import datetime
from typing import Optional
import httpx

from ..engine.models import Orderbook, OrderbookLevel


class CLOBClient:
    """Client for Polymarket CLOB API (orderbook and prices)."""

    def __init__(
        self,
        base_url: str = "https://clob.polymarket.com",
        timeout: int = 10,
        max_retries: int = 3,
        retry_backoff: float = 2.0
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.client = httpx.AsyncClient(timeout=timeout)

        # In-memory cache for orderbooks
        self._orderbook_cache: dict[str, tuple[Orderbook, datetime]] = {}
        self._price_cache: dict[str, tuple[float, datetime]] = {}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.retry_backoff ** attempt
                await asyncio.sleep(wait_time)

        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts")

    async def get_orderbook(
        self,
        token_id: str,
        market_id: str = "",
        use_cache: bool = True,
        cache_ttl: int = 5
    ) -> Optional[Orderbook]:
        """
        Fetch orderbook for a token.

        Args:
            token_id: Token ID
            market_id: Market ID (optional, for reference)
            use_cache: Whether to use cached data
            cache_ttl: Cache TTL in seconds

        Returns:
            Orderbook object or None
        """
        # Check cache
        if use_cache and token_id in self._orderbook_cache:
            cached_book, cached_at = self._orderbook_cache[token_id]
            age = (datetime.utcnow() - cached_at).total_seconds()
            if age < cache_ttl:
                return cached_book

        try:
            data = await self._request("/book", params={"token_id": token_id})
            orderbook = self._parse_orderbook(data, token_id, market_id)

            # Cache it
            self._orderbook_cache[token_id] = (orderbook, datetime.utcnow())

            return orderbook
        except Exception as e:
            return None

    def _parse_orderbook(self, data: dict, token_id: str, market_id: str) -> Orderbook:
        """Parse orderbook data from API response."""
        bids = []
        asks = []

        # Parse bids (buy orders)
        for bid_data in data.get("bids", []):
            try:
                price = float(bid_data.get("price", 0))
                size = float(bid_data.get("size", 0))
                if price > 0 and size > 0:
                    bids.append(OrderbookLevel(price=price, size=size))
            except (ValueError, TypeError):
                continue

        # Parse asks (sell orders)
        for ask_data in data.get("asks", []):
            try:
                price = float(ask_data.get("price", 0))
                size = float(ask_data.get("size", 0))
                if price > 0 and size > 0:
                    asks.append(OrderbookLevel(price=price, size=size))
            except (ValueError, TypeError):
                continue

        # Sort bids descending, asks ascending
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        return Orderbook(
            token_id=token_id,
            market_id=market_id,
            bids=bids,
            asks=asks,
            timestamp=datetime.utcnow()
        )

    async def get_price(
        self,
        token_id: str,
        side: str = "buy",
        use_cache: bool = True,
        cache_ttl: int = 5
    ) -> Optional[float]:
        """
        Fetch current price for a token.

        Args:
            token_id: Token ID
            side: "buy" or "sell"
            use_cache: Whether to use cached data
            cache_ttl: Cache TTL in seconds

        Returns:
            Price as float or None
        """
        cache_key = f"{token_id}:{side}"

        # Check cache
        if use_cache and cache_key in self._price_cache:
            cached_price, cached_at = self._price_cache[cache_key]
            age = (datetime.utcnow() - cached_at).total_seconds()
            if age < cache_ttl:
                return cached_price

        try:
            data = await self._request("/price", params={
                "token_id": token_id,
                "side": side
            })

            price = float(data.get("price", 0))
            if price > 0:
                self._price_cache[cache_key] = (price, datetime.utcnow())
                return price

            return None
        except Exception:
            return None

    async def get_mid_price(self, token_id: str, market_id: str = "") -> Optional[float]:
        """
        Get mid price from orderbook.

        Args:
            token_id: Token ID
            market_id: Market ID (optional)

        Returns:
            Mid price or None
        """
        orderbook = await self.get_orderbook(token_id, market_id)
        if orderbook:
            return orderbook.mid_price
        return None

    async def get_best_bid(self, token_id: str, market_id: str = "") -> Optional[float]:
        """Get best bid price."""
        orderbook = await self.get_orderbook(token_id, market_id)
        if orderbook:
            return orderbook.best_bid
        return None

    async def get_best_ask(self, token_id: str, market_id: str = "") -> Optional[float]:
        """Get best ask price."""
        orderbook = await self.get_orderbook(token_id, market_id)
        if orderbook:
            return orderbook.best_ask
        return None

    async def get_liquidity_at_price(
        self,
        token_id: str,
        price: float,
        side: str,
        market_id: str = ""
    ) -> float:
        """
        Calculate available liquidity at or better than given price.

        Args:
            token_id: Token ID
            price: Target price
            side: "buy" or "sell"
            market_id: Market ID

        Returns:
            Total size available at or better than price
        """
        orderbook = await self.get_orderbook(token_id, market_id)
        if not orderbook:
            return 0.0

        total_size = 0.0

        if side == "buy":
            # For buy orders, we want asks at or below our price
            for ask in orderbook.asks:
                if ask.price <= price:
                    total_size += ask.size
                else:
                    break  # Asks are sorted ascending
        else:
            # For sell orders, we want bids at or above our price
            for bid in orderbook.bids:
                if bid.price >= price:
                    total_size += bid.size
                else:
                    break  # Bids are sorted descending

        return total_size

    async def calculate_vwap(
        self,
        token_id: str,
        size: float,
        side: str,
        market_id: str = ""
    ) -> Optional[float]:
        """
        Calculate volume-weighted average price for a given size.

        Args:
            token_id: Token ID
            size: Target size to fill
            side: "buy" or "sell"
            market_id: Market ID

        Returns:
            VWAP or None if insufficient liquidity
        """
        orderbook = await self.get_orderbook(token_id, market_id)
        if not orderbook:
            return None

        levels = orderbook.asks if side == "buy" else orderbook.bids
        remaining = size
        total_cost = 0.0

        for level in levels:
            if remaining <= 0:
                break

            filled = min(remaining, level.size)
            total_cost += filled * level.price
            remaining -= filled

        if remaining > 0:
            # Insufficient liquidity
            return None

        return total_cost / size

    def clear_cache(self):
        """Clear all cached data."""
        self._orderbook_cache.clear()
        self._price_cache.clear()
