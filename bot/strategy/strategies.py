from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from bot.strategy.atm_option_selector import AtmOptionSelector
from bot.strategy.scalping_logic import Signal, TradePlan, ScalpingLogic


class Strategy(Protocol):
    name: str

    def build_trade(self, signal: Signal, spot_price: float) -> TradePlan: ...


@dataclass(frozen=True)
class ScalpAtmStrategy:
    selector: AtmOptionSelector
    logic: ScalpingLogic
    name: str = "SCALP_ATM"

    def build_trade(self, signal: Signal, spot_price: float) -> TradePlan:
        selection = self.selector.select(signal.symbol, spot_price, signal.side)
        return self.logic.build_trade(signal, selection)
