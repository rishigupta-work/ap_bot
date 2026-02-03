from __future__ import annotations

from typing import Any

from bot.core.dhan_client import DhanClient
from bot.core.order_types import OrderRequest
from bot.core.risk_manager import RiskManager
from bot.core.trading_control import TradingControl
from bot.utils.logger import setup_logger


class OrderManager:
    def __init__(
        self,
        client: DhanClient,
        risk_manager: RiskManager,
        trading_control: TradingControl,
        execution_mode: str = "paper",
    ) -> None:
        self._client = client
        self._risk_manager = risk_manager
        self._trading_control = trading_control
        self._execution_mode = execution_mode
        self._logger = setup_logger(self.__class__.__name__)

    def place_order(self, request: OrderRequest) -> dict[str, Any] | None:
        if request.order_tag not in {"STOP_LOSS", "TARGET", "EXIT"}:
            if not self._trading_control.status().enabled:
                self._logger.warning("Trading disabled by manual control")
                return None
        if not self._risk_manager.validate_order(request):
            self._logger.warning("Order rejected by risk manager", extra={"symbol": request.symbol})
            return None
        if self._execution_mode.lower() == "paper":
            response = {
                "ok": True,
                "mode": "paper",
                "symbol": request.symbol,
                "side": request.side,
                "quantity": request.quantity,
                "order_type": request.order_type,
                "product_type": request.product_type,
                "price": request.price,
                "order_tag": request.order_tag,
            }
            self._risk_manager.record_trade(request, response)
            return response
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
