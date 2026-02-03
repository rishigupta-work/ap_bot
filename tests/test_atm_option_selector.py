from datetime import datetime, timedelta

import pytest

from bot.strategy.atm_option_selector import AtmOptionSelector


def _today_iso():
    return datetime.utcnow().date().isoformat()


def test_atm_option_selector_picks_nearest_expiry_and_strike():
    expiry_today = _today_iso()
    instruments = [
        {
            "symbol": "NIFTY",
            "expiry": expiry_today,
            "strike": 22000,
            "option_type": "CE",
            "trading_symbol": "NIFTY26FEB22000CE",
            "lot_size": 50,
            "exchange": "NFO",
            "tradable": True,
        },
        {
            "symbol": "NIFTY",
            "expiry": expiry_today,
            "strike": 22000,
            "option_type": "PE",
            "trading_symbol": "NIFTY26FEB22000PE",
            "lot_size": 50,
            "exchange": "NFO",
            "tradable": True,
        },
    ]
    selector = AtmOptionSelector(instruments, {"NIFTY": 50})

    selection = selector.select("NIFTY", spot_price=22010, side="BUY")

    assert selection.symbol == "NIFTY26FEB22000CE"
    assert selection.exchange == "NFO"
    assert selection.lot_size == 50


def test_atm_option_selector_raises_when_missing_symbol():
    selector = AtmOptionSelector([], {"NIFTY": 50})

    with pytest.raises(ValueError):
        selector.select("NIFTY", spot_price=22010, side="BUY")
