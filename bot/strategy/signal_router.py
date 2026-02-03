from __future__ import annotations

from dataclasses import dataclass

from bot.strategy.atm_option_selector import AtmOptionSelector
from bot.strategy.scalping_logic import ScalpingLogic, Signal, TradePlan
from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class SignalContext:
    spot_price: float


class SignalRouter:
    def __init__(
        self,
        allowed_strategies: set[str],
        selector: AtmOptionSelector,
        scalping_logic: ScalpingLogic,
    ) -> None:
        self._allowed_strategies = allowed_strategies
        self._selector = selector
        self._scalping_logic = scalping_logic
        self._logger = setup_logger(self.__class__.__name__)

    def route(self, signal: Signal, context: SignalContext) -> TradePlan:
        if signal.strategy not in self._allowed_strategies:
            raise ValueError("Unknown strategy")
        if signal.strategy == "SCALP_ATM":
            selection = self._selector.select(signal.symbol, context.spot_price, signal.side)
            return self._scalping_logic.build_trade(signal, selection)
        self._logger.error("Strategy not implemented", extra={"strategy": signal.strategy})
        raise ValueError("Strategy not implemented")
