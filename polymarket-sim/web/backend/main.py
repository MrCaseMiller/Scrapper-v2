"""FastAPI backend for Polymarket Simulation Trader web app."""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
import json

from .config import get_settings
from .auth import (
    UserSignup, UserLogin, Token, TokenData,
    signup_user, login_user, get_current_user
)
from .database import (
    init_db, get_user_portfolio, get_user_positions,
    get_recent_fills, get_resting_orders
)
from pydantic import BaseModel

settings = get_settings()

app = FastAPI(
    title="Polymarket Simulation Trader",
    description="Paper trading platform for Polymarket prediction markets",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class PortfolioResponse(BaseModel):
    balance: float
    total_deposited: float
    realized_pnl: float
    total_fees_paid: float
    positions_value: float
    total_value: float
    unrealized_pnl: float
    total_pnl: float
    total_return_pct: float
    num_positions: int


class PositionResponse(BaseModel):
    token_id: str
    market_id: str
    market_side: str
    shares: float
    avg_entry_price: float
    current_price: float
    cost_basis: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class FillResponse(BaseModel):
    fill_id: str
    order_id: str
    market_id: str
    token_id: str
    side: str
    market_side: str
    shares: float
    price: float
    size: float
    fee: float
    timestamp: str


class OrderResponse(BaseModel):
    order_id: str
    market_id: str
    token_id: str
    side: str
    market_side: str
    size: float
    price: float
    status: str
    created_at: str
    expires_at: str | None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)


manager = ConnectionManager()


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Authentication endpoints
@app.post("/api/auth/signup", response_model=Token)
async def signup(user_data: UserSignup):
    """
    Sign up new user with email confirmation.

    Sends confirmation email via Supabase.
    """
    return await signup_user(user_data.email, user_data.password)


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user."""
    return await login_user(user_data.email, user_data.password)


@app.get("/api/auth/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user info."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email
    }


# Portfolio endpoints
@app.get("/api/portfolio", response_model=PortfolioResponse)
async def get_portfolio(current_user: TokenData = Depends(get_current_user)):
    """Get user's portfolio."""
    portfolio = await get_user_portfolio(current_user.user_id)

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get positions to calculate values
    positions = await get_user_positions(current_user.user_id)

    positions_value = sum(
        pos.shares * pos.current_price for pos in positions
    )

    total_value = portfolio.balance + positions_value
    unrealized_pnl = sum(
        (pos.shares * pos.current_price) - (pos.shares * pos.avg_entry_price)
        for pos in positions
    )

    total_pnl = portfolio.realized_pnl + unrealized_pnl
    total_return_pct = (
        ((total_value - portfolio.total_deposited) / portfolio.total_deposited) * 100
        if portfolio.total_deposited > 0 else 0.0
    )

    return PortfolioResponse(
        balance=portfolio.balance,
        total_deposited=portfolio.total_deposited,
        realized_pnl=portfolio.realized_pnl,
        total_fees_paid=portfolio.total_fees_paid,
        positions_value=positions_value,
        total_value=total_value,
        unrealized_pnl=unrealized_pnl,
        total_pnl=total_pnl,
        total_return_pct=total_return_pct,
        num_positions=len(positions)
    )


@app.get("/api/positions", response_model=List[PositionResponse])
async def get_positions(current_user: TokenData = Depends(get_current_user)):
    """Get user's positions."""
    positions = await get_user_positions(current_user.user_id)

    return [
        PositionResponse(
            token_id=pos.token_id,
            market_id=pos.market_id,
            market_side=pos.market_side,
            shares=pos.shares,
            avg_entry_price=pos.avg_entry_price,
            current_price=pos.current_price,
            cost_basis=pos.shares * pos.avg_entry_price,
            market_value=pos.shares * pos.current_price,
            unrealized_pnl=(pos.shares * pos.current_price) - (pos.shares * pos.avg_entry_price),
            unrealized_pnl_pct=(
                (((pos.shares * pos.current_price) - (pos.shares * pos.avg_entry_price)) /
                 (pos.shares * pos.avg_entry_price) * 100)
                if pos.shares * pos.avg_entry_price > 0 else 0.0
            )
        )
        for pos in positions
    ]


@app.get("/api/fills", response_model=List[FillResponse])
async def get_fills(
    limit: int = 10,
    current_user: TokenData = Depends(get_current_user)
):
    """Get user's recent fills."""
    fills = await get_recent_fills(current_user.user_id, limit)

    return [
        FillResponse(
            fill_id=fill.fill_id,
            order_id=fill.order_id,
            market_id=fill.market_id,
            token_id=fill.token_id,
            side=fill.side,
            market_side=fill.market_side,
            shares=fill.shares,
            price=fill.price,
            size=fill.size,
            fee=fill.fee,
            timestamp=fill.timestamp.isoformat()
        )
        for fill in fills
    ]


@app.get("/api/orders", response_model=List[OrderResponse])
async def get_orders(current_user: TokenData = Depends(get_current_user)):
    """Get user's resting orders."""
    orders = await get_resting_orders(current_user.user_id)

    return [
        OrderResponse(
            order_id=order.order_id,
            market_id=order.market_id,
            token_id=order.token_id,
            side=order.side,
            market_side=order.market_side,
            size=order.size,
            price=order.price,
            status=order.status,
            created_at=order.created_at.isoformat(),
            expires_at=order.expires_at.isoformat() if order.expires_at else None
        )
        for order in orders
    ]


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time portfolio updates."""
    await manager.connect(user_id, websocket)

    try:
        while True:
            # Keep connection alive and send periodic updates
            data = await websocket.receive_text()

            # Echo back (can be used for heartbeat)
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
