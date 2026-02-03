from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from bot.core.order_types import OrderRequest
from bot.strategy.scalping_logic import TradePlan, Signal
from bot.webhook.listener import create_app


class _FakeRouter:
    def __init__(self):
        self.last_signal = None

    def route(self, signal, context):
        self.last_signal = signal
        entry = OrderRequest(
            symbol="OPT",
            exchange="NFO",
            side=signal.side,
            quantity=1,
            order_type="MARKET",
            product_type="INTRADAY",
        )
        return TradePlan(entry=entry, stop_loss_price=123.0)


class _FakeOrderManager:
    def __init__(self):
        self.orders = []

    def place_order(self, request):
        self.orders.append(("entry", request))
        return {"ok": True, "type": "entry"}

    def place_stop_loss(self, request):
        self.orders.append(("sl", request))
        return {"ok": True, "type": "sl"}


class _FakeTradingControl:
    def __init__(self):
        self._enabled = True

    def status(self):
        return type("State", (), {"enabled": self._enabled, "updated_at": "now", "reason": None})()

    def enable(self, reason=None):
        self._enabled = True
        return self.status()

    def disable(self, reason=None):
        self._enabled = False
        return self.status()


def _payload(timestamp):
    return {
        "strategy": "SCALP_ATM",
        "symbol": "NIFTY",
        "side": "BUY",
        "timeframe": "1m",
        "price": 22000,
        "timestamp": timestamp,
    }


def test_webhook_accepts_fresh_signal():
    router = _FakeRouter()
    order_manager = _FakeOrderManager()
    control = _FakeTradingControl()
    app = create_app(router, order_manager, signal_ttl_seconds=30, spot_price_provider=lambda s, p: p, trading_control=control)
    client = TestClient(app)

    timestamp = datetime.now(timezone.utc).isoformat()
    response = client.post("/signal", json=_payload(timestamp))

    assert response.status_code == 200
    body = response.json()
    assert body["entry"]["ok"] is True
    assert body["stop_loss"]["ok"] is True
    assert "target" in body
    assert len(order_manager.orders) == 2


def test_webhook_rejects_stale_signal():
    router = _FakeRouter()
    order_manager = _FakeOrderManager()
    control = _FakeTradingControl()
    app = create_app(router, order_manager, signal_ttl_seconds=30, spot_price_provider=lambda s, p: p, trading_control=control)
    client = TestClient(app)

    timestamp = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    response = client.post("/signal", json=_payload(timestamp))

    assert response.status_code == 400
    assert response.json()["detail"] == "Stale signal"
