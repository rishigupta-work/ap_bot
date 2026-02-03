from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bot.core.dhan_client import DhanClient
from bot.core.risk_manager import RiskManager
from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    exchange: str
    side: str
    quantity: int
    order_type: str
    product_type: str
    price: float | None = None
    order_tag: str | None = None


class OrderManager:
    def __init__(self, client: DhanClient, risk_manager: RiskManager) -> None:
        self._client = client
        self._risk_manager = risk_manager
        self._logger = setup_logger(self.__class__.__name__)

    def place_order(self, request: OrderRequest) -> dict[str, Any] | None:
        if not self._risk_manager.validate_order(request):
            self._logger.warning("Order rejected by risk manager", extra={"symbol": request.symbol})
            return None
        payload = {
            "symbol": request.symbol,
            "exchange": request.exchange,
            "side": request.side,
            "quantity": request.quantity,
            "order_type": request.order_type,
            "product_type": request.product_type,
            "price": request.price,
        }
        response = self._client.place_order(payload)
        self._risk_manager.record_trade(request, response)
        return response

    def place_stop_loss(self, request: OrderRequest) -> dict[str, Any] | None:
        if request.order_tag != "STOP_LOSS":
            raise ValueError("Stop loss order must include order_tag=STOP_LOSS")
        return self.place_order(request)
