from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bot.utils.logger import setup_logger


@dataclass
class Position:
    symbol: str
    quantity: int
    side: str
    entry_price: float
    status: str


class PositionManager:
    def __init__(self, state_path: Path) -> None:
        self._state_path = state_path
        self._logger = setup_logger(self.__class__.__name__)

    def load(self) -> list[Position]:
        if not self._state_path.exists():
            return []
        with self._state_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return [Position(**item) for item in data]

    def save(self, positions: list[Position]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._state_path.open("w", encoding="utf-8") as file:
            json.dump([position.__dict__ for position in positions], file)

    def has_open_position(self, symbol: str) -> bool:
        positions = self.load()
        for position in positions:
            if position.symbol == symbol and position.status != "EXITED":
                return True
        return False

    def update_positions(self, positions: list[Position]) -> None:
        self.save(positions)
        self._logger.info("Positions updated", extra={"count": len(positions)})

    def record_from_broker(self, payload: list[dict[str, Any]]) -> list[Position]:
        positions = []
        for item in payload:
            positions.append(
                Position(
                    symbol=item.get("symbol", ""),
                    quantity=int(item.get("quantity", 0)),
                    side=item.get("side", ""),
                    entry_price=float(item.get("entry_price", 0.0)),
                    status=item.get("status", ""),
                )
            )
        self.update_positions(positions)
        return positions
