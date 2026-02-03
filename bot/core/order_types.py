from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    exchange: str
    side: str
    quantity: int
    order_type: str
    product_type: str
    price: float | None = None
    reference_price: float | None = None
    order_tag: str | None = None
