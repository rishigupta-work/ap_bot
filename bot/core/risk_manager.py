from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from bot.core.order_types import OrderRequest
from bot.core.position_manager import PositionManager
from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class RiskLimits:
    max_trades_per_day: int
    max_daily_loss: float
    risk_per_trade_pct: float
    capital: float | None = None


class RiskManager:
    def __init__(self, limits: RiskLimits, state_path: Path, position_manager: PositionManager) -> None:
        self._limits = limits
        self._state_path = state_path
        self._position_manager = position_manager
        self._logger = setup_logger(self.__class__.__name__)

    def _load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return {"date": date.today().isoformat(), "trades": 0, "daily_loss": 0.0}
        with self._state_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save_state(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._state_path.open("w", encoding="utf-8") as file:
            json.dump(state, file)

    def _reset_if_new_day(self, state: dict[str, Any]) -> dict[str, Any]:
        today = date.today().isoformat()
        if state.get("date") != today:
            return {"date": today, "trades": 0, "daily_loss": 0.0}
        return state

    def validate_order(self, request: OrderRequest) -> bool:
        state = self._reset_if_new_day(self._load_state())
        if request.order_tag == "STOP_LOSS":
            return True
        if request.order_tag == "TARGET":
            return True
        if state["trades"] >= self._limits.max_trades_per_day:
            self._logger.warning("Max trades per day reached")
            return False
        if state["daily_loss"] >= self._limits.max_daily_loss:
            self._logger.warning("Max daily loss reached")
            return False
        if self._limits.capital is not None:
            reference_price = request.reference_price or request.price
            if reference_price is not None:
                allowed = self._limits.capital * (self._limits.risk_per_trade_pct / 100)
                notional = reference_price * request.quantity
                if notional > allowed:
                    self._logger.warning(
                        "Order notional exceeds risk per trade",
                        extra={"notional": notional, "allowed": allowed},
                    )
                    return False
        if self._position_manager.has_open_position(request.symbol):
            self._logger.warning("Open position exists for symbol", extra={"symbol": request.symbol})
            return False
        return True

    def record_trade(self, request: OrderRequest, response: dict[str, Any]) -> None:
        if request.order_tag == "STOP_LOSS":
            self._logger.info("Stop loss order recorded", extra={"symbol": request.symbol, "order": response})
            return
        if request.order_tag == "TARGET":
            self._logger.info("Target order recorded", extra={"symbol": request.symbol, "order": response})
            return
        state = self._reset_if_new_day(self._load_state())
        state["trades"] += 1
        if isinstance(response, dict) and "pnl" in response:
            try:
                pnl_value = float(response["pnl"])
                if pnl_value < 0:
                    state["daily_loss"] += abs(pnl_value)
            except (TypeError, ValueError):
                self._logger.warning("Invalid pnl in response", extra={"pnl": response.get("pnl")})
        self._save_state(state)
        self._logger.info("Trade recorded", extra={"symbol": request.symbol, "order": response})
