from __future__ import annotations

from dataclasses import dataclass

from bot.strategy.scalping_logic import Signal, TradePlan
from bot.strategy.strategies import Strategy
from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class SignalContext:
    spot_price: float


class SignalRouter:
    def __init__(
        self,
        allowed_strategies: set[str],
        strategies: dict[str, Strategy],
    ) -> None:
        self._allowed_strategies = allowed_strategies
        self._strategies = strategies
        self._logger = setup_logger(self.__class__.__name__)

    def route(self, signal: Signal, context: SignalContext) -> TradePlan:
        if signal.strategy not in self._allowed_strategies:
            raise ValueError("Unknown strategy")
        strategy = self._strategies.get(signal.strategy)
        if strategy is not None:
            return strategy.build_trade(signal, context.spot_price)
        self._logger.error("Strategy not implemented", extra={"strategy": signal.strategy})
        raise ValueError("Strategy not implemented")
