# DhanHQ Scalping & ATM Options Bot — Software Overview

## Objective
This bot provides a **deterministic, Windows-compatible** implementation scaffold for executing **scalping strategies on ATM index options** using **DhanHQ API** and **webhook-driven signals**. The design prioritizes **risk containment and debuggability** over optimization or low-latency behavior.

## Operating Constraints (Non-Negotiable)
- **Broker:** DhanHQ API only
- **Language:** Python 3.10+
- **OS:** Windows (local machine)
- **Execution:** Single long-running process
- **Deployment:** No cloud/Docker/Linux (for now)
- **Strategy:** Scalping, ATM index options only
- **Signal Ingestion:** Webhooks
- **Priority:** Risk containment > profitability

## Module Structure (Required)
```
bot/
├── config/
│   ├── dhan.yaml
│   ├── risk.yaml
│   └── strategy.yaml
│
├── core/
│   ├── dhan_client.py
│   ├── instrument_cache.py
│   ├── order_manager.py
│   ├── position_manager.py
│   └── risk_manager.py
│
├── strategy/
│   ├── signal_router.py
│   ├── scalping_logic.py
│   └── atm_option_selector.py
│
├── webhook/
│   └── listener.py
│
├── utils/
│   ├── logger.py
│   ├── time_utils.py
│   └── retry.py
│
└── main.py
```

## Startup Sequence
1. Load configuration files (Dhan, risk, strategy).
2. Authenticate with DhanHQ.
3. Download/cache instrument master (daily).
4. Initialize logging and state storage.
5. Start FastAPI webhook server.
6. Start position monitoring loop.

## Runtime Flow (End-to-End)
```
Webhook Signal
    ↓
Schema Validation
    ↓
Signal Router
    ↓
ATM Instrument Resolution
    ↓
Risk Validation
    ↓
Order Placement
    ↓
SL Placement
    ↓
Position Monitoring
    ↓
Exit Handling
```
No step may be skipped.

## Webhook Design
### Technology
- FastAPI
- Uvicorn
- Single configurable port

### Payload Schema (Strict)
```json
{
  "strategy": "SCALP_ATM",
  "symbol": "NIFTY",
  "side": "BUY",
  "timeframe": "1m",
  "price": 22540.0,
  "timestamp": "YYYY-MM-DDTHH:MM:SS"
}
```
Rules:
- Reject missing or extra keys.
- Reject stale timestamps.
- Reject unknown strategies.

## Strategy Requirements
### Strategy Type
- **Scalping** only.
- **ATM index options** only.

### Strategy Logic Boundaries
- Strategy logic **must not** call DhanHQ directly.
- All order placement must pass through **risk_manager**.
- Keep one module = one responsibility, no circular imports.

## ATM Option Selection Rules
Deterministic steps:
1. Fetch current spot price.
2. Round to nearest valid strike (50 or 100).
3. Select nearest weekly expiry.
4. **CE** for BUY signals; **PE** for SELL signals.
5. Validate instrument tradability and lot size.

All selection is derived from the cached instrument master. No guesswork.

## Risk Management Requirements
### Hard Limits
- Max trades per day
- Max daily loss (₹)
- Max loss per trade (%)
- One open position per symbol

### Example Configuration
```yaml
max_trades_per_day: 5
max_daily_loss: 2000
risk_per_trade_pct: 0.5
sl_points:
  scalping: 15
```
If any rule fails → **no order**, log only.

## Order Management Rules (DhanHQ-Specific)
- Entry: **Market** order only.
- Stop Loss: **SL-M** order immediately after entry.
- No bracket or OCO assumptions.
- Verify order status before proceeding (to be implemented).
- Handle partial fills explicitly (to be implemented).

### Order State Machine
```
PENDING → TRADED → SL_PLACED → EXITED
```

## Position Monitoring Loop
- Runs every **1 second** (independent of webhook handling).
- Tracks open positions.
- Detects SL hits.
- Enforces time-based exits (to be implemented).
- Handles manual exits (to be implemented).
- Updates persistent state.

## Logging & Persistence
- Rotating file logs (Windows safe).
- JSON trade logs.
- CSV tradebook (to be implemented).
- No memory-only state; bot must recover after restart.

## Configuration Files
### `bot/config/dhan.yaml`
Stores credentials and base URL for DhanHQ.

### `bot/config/risk.yaml`
Defines trade limits and stop-loss points.

### `bot/config/strategy.yaml`
Defines webhook port, signal TTL, allowed strategies, and strike steps.

## Implementation Notes
- `main.py` bootstraps the system and starts the webhook and monitoring loop.
- `core/` modules encapsulate broker I/O, caching, and risk checks.
- `strategy/` modules remain deterministic and broker-agnostic.
- `webhook/` handles inbound signals, schema validation, and trade routing.

## Future Extensions (Out of Scope)
- VPS/Linux migration
- Async order handling
- Multi-strategy execution
- Greeks-based option selection
- Portfolio-level risk

## Summary
This software layout enforces strict module boundaries, deterministic selection logic, and risk-first order handling to ensure safe scalping execution on ATM index options using DhanHQ.
