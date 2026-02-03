from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import uvicorn
import yaml

from bot.core.dhan_client import DhanClient, DhanCredentials
from bot.core.instrument_cache import InstrumentCache
from bot.core.order_manager import OrderManager
from bot.core.position_manager import PositionManager
from bot.core.risk_manager import RiskLimits, RiskManager
from bot.core.trading_control import TradingControl
from bot.strategy.atm_option_selector import AtmOptionSelector
from bot.strategy.scalping_logic import ScalpingLogic
from bot.strategy.signal_router import SignalRouter
from bot.strategy.strategies import ScalpAtmStrategy
from bot.utils.logger import setup_logger
from bot.webhook.listener import create_app


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def start_position_monitor(client: DhanClient, position_manager: PositionManager) -> threading.Thread:
    logger = setup_logger("PositionMonitor")

    def _loop() -> None:
        while True:
            try:
                positions = client.get_positions()
                position_manager.record_from_broker(positions)
            except Exception as exc:  # noqa: BLE001 - logs and continues
                logger.error("Position monitor error", extra={"error": str(exc)})
            time.sleep(1)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread


def main() -> None:
    base_path = Path(__file__).resolve().parent
    config_path = base_path / "config"

    dhan_config = load_yaml(config_path / "dhan.yaml")
    risk_config = load_yaml(config_path / "risk.yaml")
    strategy_config = load_yaml(config_path / "strategy.yaml")
    trading_config = load_yaml(config_path / "trading.yaml")

    credentials = DhanCredentials(
        client_id=dhan_config["client_id"],
        access_token=dhan_config["access_token"],
        base_url=dhan_config["base_url"],
    )
    client = DhanClient(credentials)

    instrument_cache = InstrumentCache(base_path / "state" / "instruments.json")
    instruments = instrument_cache.load()
    if not instruments:
        instruments = client.get_instruments()
        instrument_cache.save(instruments)

    position_manager = PositionManager(base_path / "state" / "positions.json")
    risk_limits = RiskLimits(
        max_trades_per_day=risk_config["max_trades_per_day"],
        max_daily_loss=risk_config["max_daily_loss"],
        risk_per_trade_pct=risk_config["risk_per_trade_pct"],
        capital=risk_config.get("capital"),
    )
    risk_manager = RiskManager(risk_limits, base_path / "state" / "risk.json", position_manager)
    trading_control = TradingControl(base_path / "state" / "trading.json")
    if trading_config.get("enabled", True):
        trading_control.enable(reason="startup")
    else:
        trading_control.disable(reason="startup")
    order_manager = OrderManager(
        client,
        risk_manager,
        trading_control,
        execution_mode=trading_config.get("execution_mode", "paper"),
    )

    selector = AtmOptionSelector(instruments, strategy_config["index_strike_steps"])
    scalping_logic = ScalpingLogic(
        sl_points=risk_config["sl_points"]["scalping"],
        target_points=risk_config["target_points"]["scalping"],
    )
    strategies = {
        "SCALP_ATM": ScalpAtmStrategy(selector=selector, logic=scalping_logic),
    }
    router = SignalRouter(set(strategy_config["allowed_strategies"]), strategies)

    start_position_monitor(client, position_manager)

    def spot_price_provider(symbol: str, fallback_price: float) -> float:
        return fallback_price

    app = create_app(
        router=router,
        order_manager=order_manager,
        signal_ttl_seconds=strategy_config["signal_ttl_seconds"],
        spot_price_provider=spot_price_provider,
        trading_control=trading_control,
    )

    uvicorn.run(app, host="0.0.0.0", port=strategy_config["webhook_port"])


if __name__ == "__main__":
    main()
