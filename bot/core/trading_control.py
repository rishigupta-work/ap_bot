from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class TradingControlState:
    enabled: bool
    updated_at: str
    reason: str | None = None


class TradingControl:
    def __init__(self, state_path: Path) -> None:
        self._state_path = state_path
        self._logger = setup_logger(self.__class__.__name__)

    def _default_state(self) -> TradingControlState:
        return TradingControlState(enabled=True, updated_at=self._now_iso(), reason=None)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_state(self) -> TradingControlState:
        if not self._state_path.exists():
            return self._default_state()
        with self._state_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return TradingControlState(
            enabled=bool(payload.get("enabled", True)),
            updated_at=str(payload.get("updated_at", self._now_iso())),
            reason=payload.get("reason"),
        )

    def _save_state(self, state: TradingControlState) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._state_path.open("w", encoding="utf-8") as file:
            json.dump(
                {"enabled": state.enabled, "updated_at": state.updated_at, "reason": state.reason},
                file,
            )

    def status(self) -> TradingControlState:
        return self._load_state()

    def enable(self, reason: str | None = None) -> TradingControlState:
        state = TradingControlState(enabled=True, updated_at=self._now_iso(), reason=reason)
        self._save_state(state)
        self._logger.info("Trading enabled", extra={"reason": reason})
        return state

    def disable(self, reason: str | None = None) -> TradingControlState:
        state = TradingControlState(enabled=False, updated_at=self._now_iso(), reason=reason)
        self._save_state(state)
        self._logger.warning("Trading disabled", extra={"reason": reason})
        return state
