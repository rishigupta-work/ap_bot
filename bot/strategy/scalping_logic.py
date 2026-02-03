from __future__ import annotations

from dataclasses import dataclass

from bot.core.order_manager import OrderRequest
from bot.strategy.atm_option_selector import AtmSelection


@dataclass(frozen=True)
class Signal:
    strategy: str
    symbol: str
    side: str
    timeframe: str
    price: float
    timestamp: str


@dataclass(frozen=True)
class TradePlan:
    entry: OrderRequest
    stop_loss_price: float


class ScalpingLogic:
    def __init__(self, sl_points: float) -> None:
        self._sl_points = sl_points

    def build_trade(self, signal: Signal, selection: AtmSelection) -> TradePlan:
        entry = OrderRequest(
            symbol=selection.symbol,
            exchange=selection.exchange,
            side=signal.side,
            quantity=selection.lot_size,
            order_type="MARKET",
            product_type="INTRADAY",
        )
        stop_loss_price = max(signal.price - self._sl_points, 0.0)
        return TradePlan(entry=entry, stop_loss_price=stop_loss_price)
