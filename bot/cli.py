from __future__ import annotations

import argparse
from pathlib import Path

from bot.core.trading_control import TradingControl


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trading control CLI (enable/disable/status).")
    parser.add_argument(
        "action",
        choices=("enable", "disable", "status"),
        help="Action to perform.",
    )
    parser.add_argument(
        "--reason",
        help="Optional reason for enabling/disabling trading.",
    )
    parser.add_argument(
        "--state-path",
        default=str(Path(__file__).resolve().parent / "state" / "trading.json"),
        help="Path to trading control state file.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    control = TradingControl(Path(args.state_path))
    if args.action == "enable":
        state = control.enable(reason=args.reason)
    elif args.action == "disable":
        state = control.disable(reason=args.reason)
    else:
        state = control.status()

    print(f"enabled={state.enabled} updated_at={state.updated_at} reason={state.reason}")


if __name__ == "__main__":
    main()
