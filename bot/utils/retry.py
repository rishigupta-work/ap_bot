from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def retry(
    func: Callable[[], T],
    retries: int = 3,
    delay_seconds: float = 1.0,
) -> T:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001 - explicit retry policy
            last_error = exc
            time.sleep(delay_seconds)
    if last_error is None:
        raise RuntimeError("Retry failed without exception")
    raise last_error
