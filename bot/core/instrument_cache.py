from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bot.utils.logger import setup_logger


class InstrumentCache:
    def __init__(self, cache_path: Path) -> None:
        self._cache_path = cache_path
        self._logger = setup_logger(self.__class__.__name__)

    def load(self) -> list[dict[str, Any]]:
        if not self._cache_path.exists():
            return []
        with self._cache_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, instruments: list[dict[str, Any]]) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_path.open("w", encoding="utf-8") as file:
            json.dump(instruments, file)
        self._logger.info("Instrument master cached", extra={"count": len(instruments)})
