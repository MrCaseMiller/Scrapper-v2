"""WebSocket client for real-time price updates."""

import asyncio
import json
from datetime import datetime
from typing import Callable, Optional
import websockets
from websockets.exceptions import WebSocketException


class WebSocketClient:
    """WebSocket client for Polymarket real-time updates."""

    def __init__(
        self,
        ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market",
        reconnect_delay: float = 5.0,
        ping_interval: float = 30.0
    ):
        self.ws_url = ws_url
        self.reconnect_delay = reconnect_delay
        self.ping_interval = ping_interval

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribed_markets: set[str] = set()
        self.running = False

        # Callbacks
        self.on_price_update: Optional[Callable] = None
        self.on_trade: Optional[Callable] = None
        self.on_orderbook: Optional[Callable] = None

    async def connect(self):
        """Establish WebSocket connection."""
        try:
            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=self.ping_interval
            )
            self.running = True
            return True
        except Exception as e:
            return False

    async def disconnect(self):
        """Close WebSocket connection."""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def subscribe(self, market_id: str, asset_id: str = ""):
        """
        Subscribe to market updates.

        Args:
            market_id: Market ID to subscribe to
            asset_id: Optional asset/token ID
        """
        if not self.ws:
            return

        subscribe_msg = {
            "type": "subscribe",
            "market": market_id
        }

        if asset_id:
            subscribe_msg["asset_id"] = asset_id

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            self.subscribed_markets.add(market_id)
        except Exception as e:
            pass

    async def unsubscribe(self, market_id: str):
        """Unsubscribe from market updates."""
        if not self.ws:
            return

        unsubscribe_msg = {
            "type": "unsubscribe",
            "market": market_id
        }

        try:
            await self.ws.send(json.dumps(unsubscribe_msg))
            self.subscribed_markets.discard(market_id)
        except Exception:
            pass

    async def listen(self):
        """
        Listen for WebSocket messages.
        This should be run as a background task.
        """
        while self.running:
            if not self.ws:
                # Try to reconnect
                connected = await self.connect()
                if not connected:
                    await asyncio.sleep(self.reconnect_delay)
                    continue

                # Re-subscribe to previously subscribed markets
                for market_id in list(self.subscribed_markets):
                    await self.subscribe(market_id)

            try:
                message = await self.ws.recv()
                await self._handle_message(message)
            except WebSocketException:
                # Connection lost, reconnect
                self.ws = None
                await asyncio.sleep(self.reconnect_delay)
            except Exception:
                await asyncio.sleep(0.1)

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "price_update":
                await self._handle_price_update(data)
            elif msg_type == "trade":
                await self._handle_trade(data)
            elif msg_type == "book":
                await self._handle_orderbook(data)
            elif msg_type == "error":
                pass  # Log error if needed
        except json.JSONDecodeError:
            pass

    async def _handle_price_update(self, data: dict):
        """Handle price update message."""
        if self.on_price_update:
            try:
                update = {
                    "market_id": data.get("market"),
                    "token_id": data.get("asset_id"),
                    "price": float(data.get("price", 0)),
                    "timestamp": datetime.utcnow()
                }
                await self.on_price_update(update)
            except Exception:
                pass

    async def _handle_trade(self, data: dict):
        """Handle trade message."""
        if self.on_trade:
            try:
                trade = {
                    "market_id": data.get("market"),
                    "token_id": data.get("asset_id"),
                    "price": float(data.get("price", 0)),
                    "size": float(data.get("size", 0)),
                    "side": data.get("side"),
                    "timestamp": datetime.utcnow()
                }
                await self.on_trade(trade)
            except Exception:
                pass

    async def _handle_orderbook(self, data: dict):
        """Handle orderbook update message."""
        if self.on_orderbook:
            try:
                book = {
                    "market_id": data.get("market"),
                    "token_id": data.get("asset_id"),
                    "bids": data.get("bids", []),
                    "asks": data.get("asks", []),
                    "timestamp": datetime.utcnow()
                }
                await self.on_orderbook(book)
            except Exception:
                pass

    def set_price_update_callback(self, callback: Callable):
        """Set callback for price updates."""
        self.on_price_update = callback

    def set_trade_callback(self, callback: Callable):
        """Set callback for trades."""
        self.on_trade = callback

    def set_orderbook_callback(self, callback: Callable):
        """Set callback for orderbook updates."""
        self.on_orderbook = callback
