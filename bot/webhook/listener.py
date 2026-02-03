from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator

from bot.core.order_manager import OrderManager, OrderRequest
from bot.strategy.scalping_logic import Signal, TradePlan
from bot.strategy.signal_router import SignalRouter, SignalContext
from bot.utils.logger import setup_logger


class WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str
    symbol: str
    side: str
    timeframe: str
    price: float
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Invalid timestamp format") from exc
        return value


def create_app(
    router: SignalRouter,
    order_manager: OrderManager,
    signal_ttl_seconds: int,
    spot_price_provider: callable,
) -> FastAPI:
    logger = setup_logger("Webhook")
    app = FastAPI()

    @app.post("/signal")
    def handle_signal(payload: WebhookPayload) -> dict[str, Any]:
        signal = Signal(**payload.model_dump())
        timestamp = datetime.fromisoformat(signal.timestamp).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if (now - timestamp).total_seconds() > signal_ttl_seconds:
            raise HTTPException(status_code=400, detail="Stale signal")
        spot_price = spot_price_provider(signal.symbol, signal.price)
        trade_plan = router.route(signal, SignalContext(spot_price=spot_price))
        entry_response = order_manager.place_order(trade_plan.entry)
        if entry_response is None:
            raise HTTPException(status_code=400, detail="Risk checks failed")
        sl_request = _build_stop_loss(trade_plan)
        sl_response = order_manager.place_stop_loss(sl_request)
        logger.info("Signal executed", extra={"signal": payload.model_dump()})
        return {
            "entry": entry_response,
            "stop_loss": sl_response,
        }

    return app


def _build_stop_loss(trade_plan: TradePlan) -> OrderRequest:
    side = "SELL" if trade_plan.entry.side == "BUY" else "BUY"
    return OrderRequest(
        symbol=trade_plan.entry.symbol,
        exchange=trade_plan.entry.exchange,
        side=side,
        quantity=trade_plan.entry.quantity,
        order_type="SL-M",
        product_type=trade_plan.entry.product_type,
        price=trade_plan.stop_loss_price,
        order_tag="STOP_LOSS",
    )
