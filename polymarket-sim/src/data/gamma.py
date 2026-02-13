"""Gamma API client for market discovery."""

import asyncio
from datetime import datetime
from typing import Optional
import httpx

from ..engine.models import Market
from ..storage.db import Database


class GammaClient:
    """Client for Polymarket Gamma API (market discovery)."""

    def __init__(
        self,
        base_url: str = "https://gamma-api.polymarket.com",
        timeout: int = 10,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        cache_ttl: int = 60,
        db: Optional[Database] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.cache_ttl = cache_ttl
        self.db = db
        self.client = httpx.AsyncClient(timeout=timeout)

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

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False
    ) -> list[Market]:
        """
        Fetch markets from Gamma API.

        Args:
            limit: Maximum number of markets to fetch
            offset: Offset for pagination
            active: Include active markets
            closed: Include closed markets

        Returns:
            List of Market objects
        """
        params = {
            "limit": limit,
            "offset": offset,
            "active": active,
            "closed": closed
        }

        data = await self._request("/markets", params)
        markets = []

        for item in data:
            try:
                market = self._parse_market(item)
                markets.append(market)

                # Cache to database if available
                if self.db:
                    await self.db.save_market(market)
            except (KeyError, ValueError) as e:
                # Skip markets with invalid data
                continue

        return markets

    async def get_market(self, market_id: str) -> Optional[Market]:
        """
        Fetch single market by ID.

        Args:
            market_id: Market ID (slug)

        Returns:
            Market object or None
        """
        # Check cache first if DB available
        if self.db:
            cached = await self.db.get_market(market_id)
            if cached:
                # Check if cache is fresh
                age = (datetime.utcnow() - cached.updated_at).total_seconds()
                if age < self.cache_ttl:
                    return cached

        try:
            data = await self._request(f"/markets/{market_id}")
            market = self._parse_market(data)

            # Cache to database
            if self.db:
                await self.db.save_market(market)

            return market
        except Exception:
            return None

    def _parse_market(self, data: dict) -> Market:
        """Parse market data from API response."""
        # Polymarket Gamma API returns markets with various field names
        # This handles common variations

        market_id = data.get("id") or data.get("condition_id") or data.get("market_slug")
        question = data.get("question") or data.get("title") or data.get("description", "")

        # Parse end date
        end_date_str = data.get("end_date_iso") or data.get("endDate") or data.get("end_date")
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                end_date = datetime.utcnow()
        else:
            end_date = datetime.utcnow()

        # Get token IDs
        # Polymarket uses condition_id + outcome for token IDs
        tokens = data.get("tokens", [])
        yes_token_id = ""
        no_token_id = ""

        if tokens and len(tokens) >= 2:
            yes_token_id = tokens[0].get("token_id", "")
            no_token_id = tokens[1].get("token_id", "")
        elif "clobTokenIds" in data:
            clob_tokens = data["clobTokenIds"]
            if isinstance(clob_tokens, list) and len(clob_tokens) >= 2:
                yes_token_id = clob_tokens[0]
                no_token_id = clob_tokens[1]

        # Active status
        active = data.get("active", True)
        if "closed" in data:
            active = not data["closed"]

        # Resolution
        resolved = data.get("resolved", False)
        resolution = None
        if resolved:
            outcome = data.get("outcome")
            if outcome is not None:
                resolution = "YES" if outcome == "Yes" or outcome == 1 else "NO"

        return Market(
            market_id=str(market_id),
            question=question,
            end_date=end_date,
            yes_token_id=yes_token_id,
            no_token_id=no_token_id,
            active=active,
            resolved=resolved,
            resolution=resolution,
            category=data.get("category"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    async def check_resolution(self, market_id: str) -> Optional[str]:
        """
        Check if market has resolved and return outcome.

        Args:
            market_id: Market ID

        Returns:
            "YES", "NO", or None if not resolved
        """
        market = await self.get_market(market_id)
        if market and market.resolved and market.resolution:
            return market.resolution
        return None

    async def get_active_markets_cached(self) -> list[Market]:
        """Get active markets from cache (database)."""
        if not self.db:
            return await self.get_markets(active=True, closed=False)

        return await self.db.get_active_markets()
