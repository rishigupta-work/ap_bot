import pytest

from bot.strategy.signal_router import SignalRouter, SignalContext
from bot.strategy.scalping_logic import Signal, TradePlan
from bot.core.order_types import OrderRequest


class _FakeStrategy:
    def __init__(self):
        self.called_with = None
        self.name = "SCALP_ATM"

    def build_trade(self, signal, spot_price):
        self.called_with = (signal, spot_price)
        entry = OrderRequest(
            symbol="OPT",
            exchange="NFO",
            side=signal.side,
            quantity=1,
            order_type="MARKET",
            product_type="INTRADAY",
        )
        return TradePlan(entry=entry, stop_loss_price=1.0)


def test_signal_router_routes_scalp_atm():
    strategy = _FakeStrategy()
    router = SignalRouter({"SCALP_ATM"}, {"SCALP_ATM": strategy})
    signal = Signal(
        strategy="SCALP_ATM",
        symbol="NIFTY",
        side="BUY",
        timeframe="1m",
        price=22000,
        timestamp="2026-02-03T10:00:00+00:00",
    )

    plan = router.route(signal, SignalContext(spot_price=22000))

    assert plan.entry.symbol == "OPT"
    assert strategy.called_with == (signal, 22000)


def test_signal_router_rejects_unknown_strategy():
    router = SignalRouter(set(), {})
    signal = Signal(
        strategy="UNKNOWN",
        symbol="NIFTY",
        side="BUY",
        timeframe="1m",
        price=22000,
        timestamp="2026-02-03T10:00:00+00:00",
    )

    with pytest.raises(ValueError):
        router.route(signal, SignalContext(spot_price=22000))
