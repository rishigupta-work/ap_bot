# DhanHQ Scalping and ATM Options Bot - Software Overview

## Objective
This bot provides a deterministic, Windows-compatible scaffold for executing webhook-driven strategies on NSE equities and ATM index options using the DhanHQ API. The design prioritizes risk containment, manual control, and debuggability over optimization or low-latency behavior.

## Operating Constraints (Non-Negotiable)
- Broker: DhanHQ API only
- Language: Python 3.10+
- OS: Windows (local machine)
- Execution: Single long-running process
- Deployment: Windows now, Linux-ready
- Strategy: Strategy framework (pluggable); current scalping ATM module included
- Signal ingestion: Webhooks
- Priority: Risk containment > profitability

## Module Structure (Required)
```
bot/
|-- config/
|   |-- dhan.yaml
|   |-- risk.yaml
|   |-- strategy.yaml
|   |-- trading.yaml
|
|-- core/
|   |-- dhan_client.py
|   |-- instrument_cache.py
|   |-- order_manager.py
|   |-- position_manager.py
|   |-- risk_manager.py
|   |-- trading_control.py
|
|-- strategy/
|   |-- signal_router.py
|   |-- scalping_logic.py
|   |-- atm_option_selector.py
|   |-- strategies.py
|
|-- webhook/
|   |-- listener.py
|
|-- utils/
|   |-- logger.py
|   |-- time_utils.py
|   |-- retry.py
|
|-- main.py
```

## Startup Sequence
1. Load configuration files (Dhan, risk, strategy).
2. Authenticate with DhanHQ.
3. Download/cache instrument master (daily).
4. Initialize logging and state storage.
5. Start FastAPI webhook server.
6. Start position monitoring loop.
7. Enable/disable trading via manual control endpoints.

## Runtime Flow (End-to-End)
```
Webhook Signal
    |
Schema Validation
    |
Signal Router
    |
ATM Instrument Resolution
    |
Risk Validation
    |
Order Placement
    |
SL Placement
    |
Target Placement (if configured)
    |
Position Monitoring
    |
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
- Strategy framework with pluggable modules.
- Current module: scalping on ATM index options.

### Strategy Logic Boundaries
- Strategy logic must not call DhanHQ directly.
- All order placement must pass through risk_manager.
- Keep one module = one responsibility, no circular imports.

## Scalping Reality Check (Latency)
- This is not HFT.
- Expect 200 to 500 ms latency with broker APIs.
- Tick-by-tick scalping is not viable.
- 30-second, 1-minute, or LTP-based scalping is viable.

## Testing Architecture (Simple and Safe)
```
WebSocket (LTP)
    |
Price Buffer (in-memory)
    |
pandas-ta indicators
    |
Signal Engine
    |
Risk Checks
    |
Dhan Order API
    |
Logs and Alerts
```

## Windows Testing Stack (Approved)
- OS: Windows (temporary)
- Language: Python
- Broker: DhanHQ API
- Data: WebSocket live ticks
- Indicators: pandas-ta
- Style: Scalping and ATM options

Rule: No real money yet, or minimum quantity only.

## Indicators (Scalping Friendly)
Use fast indicators only:
- EMA (5, 9, 21)
- VWAP
- RSI (7 or 9)
- Supertrend (fast)
- ATR (for SL)

Avoid heavy indicators for scalping (MACD histogram, Ichimoku).

## ATM Option Selection Rules
Deterministic steps:
1. Fetch current spot price.
2. Round to nearest valid strike (50 or 100).
3. Select nearest weekly expiry.
4. CE for BUY signals; PE for SELL signals.
5. Validate instrument tradability and lot size.

All selection is derived from the cached instrument master. No guesswork.

## Risk Management Requirements
### Hard Limits
- Max trades per day
- Max daily loss (INR)
- Max loss per trade (percent)
- One open position per symbol
- Kill switch after max loss
- Manual on/off trading control

### Example Configuration
```yaml
max_trades_per_day: 5
max_daily_loss: 5000
risk_per_trade_pct: 0.5
capital: null
sl_points:
  scalping: 15
target_points:
  scalping: 30
```
If any rule fails -> no order, log only.

## Order Management Rules (DhanHQ-Specific)
- Entry: Market order only.
- Stop loss: SL-M order immediately after entry.
- Target: LIMIT order immediately after entry (when configured).
- No bracket or OCO assumptions.
- Verify order status before proceeding (to be implemented).
- Handle partial fills explicitly (to be implemented).

### Order State Machine
```
PENDING -> TRADED -> SL_PLACED -> EXITED
```

## Position Monitoring Loop
- Runs every 1 second (independent of webhook handling).
- Tracks open positions.
- Detects SL hits.
- Enforces time-based exits (to be implemented).
- Handles manual exits (to be implemented).
- Updates persistent state.

## Logging and Persistence
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

### `bot/config/trading.yaml`
Defines execution mode (`paper` or `live`) and initial enabled state.

## Testing Mode Checklist
- Run paper trades (log-only).
- Validate entry and exit timestamps.
- Match Dhan order response with the signal.
- Check slippage.
- Simulate API failure and recovery.

## Not In Scope (Yet)
- Tick-by-tick scalping
- Multi-leg option strategies
- Async order handling
- Greeks-based option selection
- VPS/Linux migration

## Summary
This software layout enforces strict module boundaries, deterministic ATM selection logic, and risk-first order handling to ensure safe scalping execution on ATM index options using DhanHQ.
