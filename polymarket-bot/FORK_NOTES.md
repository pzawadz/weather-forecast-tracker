# Fork Analysis - polymarket-weather-bot

Forked from: https://github.com/idlepraxis/polymarket-weather-bot
Date: 2026-04-09
Purpose: Adapt US-only weather bot for global markets using Open-Meteo + weather-forecast-tracker

---

## Original Structure

```
polymarket-weather-bot/
├── archive/                    # Legacy docs, Kalshi code
├── scripts/                    # Debug scripts, one-off analyses
├── bot/
│   ├── analysis/              # wallet_analyzer.py (one-off tool)
│   ├── application/           # ✅ KEEP - bot_runner.py, extreme_value_strategy.py
│   ├── backtesting/           # ✅ KEEP - engine.py, database.py
│   ├── cli/                   # ✅ KEEP - CLI interface
│   ├── connectors/            # ⚠️  REWRITE - weather.py, polymarket.py
│   ├── database/              # ✅ KEEP - trade_history.py
│   └── utils/                 # ✅ KEEP - config.py, logger.py, models.py
└── tests/                     # Some Kalshi-specific tests
```

---

## Files to DELETE

### Entire Directories
- `archive/` — Legacy Kalshi code, not needed
- `scripts/` — Debug scripts, one-off analyses

### Individual Files
- `tests/test_kalshi_*.py` — Kalshi-specific tests
- `bot/analysis/wallet_analyzer.py` — One-off analysis tool

---

## Files to REWRITE

### bot/connectors/weather.py
**Current:** US-only, NWS-based (3 sources: NWS, Open-Meteo US, WeatherAPI fallback)
**New:** Global, Open-Meteo multi-model + optional weather-forecast-tracker integration

### bot/connectors/polymarket.py
**Current:** Custom CLOB implementation (~20KB)
**New:** Use official py-clob-client SDK

### bot/application/extreme_value_strategy.py
**Current:** Static sigma (7.0°F), Fahrenheit-only, US cities
**New:** Dynamic sigma (base + model spread), Celsius support, region calibration

---

## Files to CREATE

### New Connectors
- `bot/connectors/open_meteo.py` — Multi-model ensemble fetcher
- `bot/connectors/tracker.py` — Optional weather-forecast-tracker integration

### Configuration
- `config/locations.json` — City definitions (European + US)
- `config/calibration.json` — Sigma values per region

### Calibration
- `bot/calibrate.py` — Weekly sigma recalibration script

---

## Dependencies to REMOVE

From requirements.txt:
- ❌ Kalshi-related packages
- ❌ Commented-out Web3 packages (will use uncommented py-clob-client)
- ❌ Custom CLOB dependencies

---

## Dependencies to ADD

From requirements.txt:
- ✅ py-clob-client>=0.34.4 (uncomment, already in file)
- ✅ httpx>=0.27.0 (for async requests)
- ✅ scipy>=1.11.0 (extreme value distributions)

---

## Strategy Modifications Needed

### Dynamic Sigma
**Current:**
```python
sigma = 7.0  # Static for all forecasts
```

**New:**
```python
sigma = base_sigma + (model_spread / 2.0)
# base_sigma = 4.0°F for Europe, 5.0°F for US
# model_spread = max(models) - min(models)
```

### Temperature Units
**Current:** Fahrenheit-only
**New:** Detect from market question, support both °F and °C

### Region Calibration
**New:** Load from `config/calibration.json`:
```json
{
  "europe": {"base_sigma_f": 3.5, "base_sigma_c": 2.0},
  "us": {"base_sigma_f": 5.0, "base_sigma_c": 2.8}
}
```

---

## Risk Controls to KEEP

From existing bot (proven in production):
- ✅ Max 25 trades/day
- ✅ Max 20 trades/scan
- ✅ $5 max per single market
- ✅ 5% max daily bankroll exposure
- ✅ Skip sub-3-cent markets
- ✅ Per-city concentration limits

---

## Risk Controls to ADD

New safety measures:
- ✅ Circuit breaker: pause if daily P&L < -$50
- ✅ Max position per market: $10
- ✅ Min market liquidity: $500
- ✅ Simulation mode: MUST be true until calibration complete
- ✅ Max forecast horizon: 5 days
- ✅ Min model count: 3 models must agree

---

## Implementation Order

Phase 1: Fork & Cleanup (this phase)
  1. ✅ Clone repository
  2. ⏳ Delete dead code
  3. ⏳ Clean requirements.txt
  4. ⏳ Update .env.example
  5. ⏳ Create config/ directory

Phase 2: Replace Weather Connector
  1. Create bot/connectors/open_meteo.py
  2. Create bot/connectors/tracker.py
  3. Rewrite bot/connectors/weather.py

Phase 3: Replace Execution Layer
  1. Rewrite bot/connectors/polymarket.py
  2. Remove Web3 dependencies
  3. Update bot/utils/config.py

---

## Testing Strategy

### Unit Tests
- test_open_meteo.py — Mock API, test ensemble
- test_strategy.py — Test edge calculation
- test_market_parser.py — Test city extraction

### Integration Tests
- test_weather_pipeline.py — Live Open-Meteo API
- test_tracker_integration.py — Read from tracker DB

### Backtesting
- Use bot/backtesting/engine.py with tracker's historical data

---

## Notes

- Original bot has $25K+ profit track record (real trading)
- Extreme value strategy is proven, keep it
- Key innovation: dynamic sigma from model agreement
- Europe markets likely more profitable (better models: ECMWF, ICON)
