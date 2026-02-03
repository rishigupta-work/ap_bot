import pytest

from bot.strategy.scalping_logic import ScalpingLogic, Signal
from bot.strategy.atm_option_selector import AtmSelection


def test_scalping_logic_builds_trade_plan():
    logic = ScalpingLogic(sl_points=15, target_points=30)
    signal = Signal(
        strategy="SCALP_ATM",
        symbol="NIFTY",
        side="BUY",
        timeframe="1m",
        price=22000,
        timestamp="2026-02-03T10:00:00+00:00",
    )
    selection = AtmSelection(symbol="NIFTY26FEB22000CE", exchange="NFO", lot_size=50)

    plan = logic.build_trade(signal, selection)

    assert plan.entry.symbol == "NIFTY26FEB22000CE"
    assert plan.entry.exchange == "NFO"
    assert plan.entry.side == "BUY"
    assert plan.entry.quantity == 50
    assert plan.entry.order_type == "MARKET"
    assert plan.entry.product_type == "INTRADAY"
    assert plan.stop_loss_price == 21985
    assert plan.target_price == 22030
