from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class AtmSelection:
    symbol: str
    exchange: str
    lot_size: int


class AtmOptionSelector:
    def __init__(self, instruments: list[dict[str, Any]], strike_steps: dict[str, int]) -> None:
        self._instruments = instruments
        self._strike_steps = strike_steps
        self._logger = setup_logger(self.__class__.__name__)

    def select(self, index_symbol: str, spot_price: float, side: str) -> AtmSelection:
        step = self._strike_steps.get(index_symbol)
        if step is None:
            raise ValueError(f"No strike step configured for {index_symbol}")
        strike = round(spot_price / step) * step
        option_type = "CE" if side == "BUY" else "PE"
        expiry = self._nearest_expiry(index_symbol)
        for instrument in self._instruments:
            if (
                instrument.get("symbol") == index_symbol
                and instrument.get("expiry") == expiry
                and float(instrument.get("strike", 0)) == float(strike)
                and instrument.get("option_type") == option_type
                and instrument.get("tradable", True)
            ):
                return AtmSelection(
                    symbol=instrument["trading_symbol"],
                    exchange=instrument.get("exchange", "NFO"),
                    lot_size=int(instrument.get("lot_size", 0)),
                )
        self._logger.error("ATM option not found", extra={"symbol": index_symbol, "strike": strike})
        raise ValueError("ATM option not found")

    def _nearest_expiry(self, index_symbol: str) -> str:
        expiries = sorted(
            {
                instrument.get("expiry")
                for instrument in self._instruments
                if instrument.get("symbol") == index_symbol
            }
        )
        if not expiries:
            raise ValueError(f"No expiries found for {index_symbol}")
        today = datetime.utcnow().date()
        future_expiries = [e for e in expiries if datetime.fromisoformat(e).date() >= today]
        if not future_expiries:
            return expiries[-1]
        return future_expiries[0]
