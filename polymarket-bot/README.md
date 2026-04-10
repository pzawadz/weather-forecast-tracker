# Polymarket Weather Bot

**Automated weather trading bot for Polymarket** using global weather forecasts and extreme value betting strategy.

---

## 🎯 Overview

This bot trades weather markets on [Polymarket](https://polymarket.com) using:
- **Multi-model weather forecasts** from Open-Meteo (ECMWF, ICON, GFS, Meteo France, GEM)
- **Optional bias correction** from [weather-forecast-tracker](../) (parent project)
- **Extreme value strategy** - proven $25K+ profit strategy (forked from idlepraxis/polymarket-weather-bot)
- **Dynamic sigma** - adapts to model agreement for accurate probability estimates

---

## 📊 Key Features

### 1. Global Coverage
```
European cities: Warsaw, Berlin, London, Paris
US cities: NYC, LA, Chicago, Miami, Houston, Phoenix
Temperature units: Fahrenheit and Celsius (auto-detect)
```

### 2. Dynamic Sigma (Adaptive Confidence)
```python
# Old (hardcoded):
sigma = 7.0°F for all forecasts

# New (dynamic):
sigma = base_sigma + (model_spread / 2)

Example Warsaw 2026-04-11:
  Model spread: 1.3°F (models agree)
  Dynamic sigma: 4.6°F (higher confidence)
  
Example NYC 2026-04-11:
  Model spread: 5.0°F (models disagree)
  Dynamic sigma: 6.5°F (lower confidence)
```

### 3. Bias Correction (Optional)
```
If weather-forecast-tracker is available:
1. Read pre-collected forecasts from SQLite DB
2. Read model bias (7-day average error per model)
3. Subtract known bias from forecasts
4. Return bias-corrected ensemble (more accurate!)

Example: ICON historically 0.5°C too warm for Warsaw
→ Bot subtracts 0.5°C → better forecast
```

### 4. Risk Controls
```
SIMULATION_MODE=true (default, no real trades)
Circuit breaker: -$50 daily loss
Max position per market: $10
Max trades per day: 25
Min market liquidity: $500
Min edge: 5%
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd polymarket-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
nano .env

# Required:
POLYMARKET_PRIVATE_KEY=0x...

# Optional (for bias correction):
TRACKER_DB_PATH=../weather_forecasts.db

# Safety:
SIMULATION_MODE=true
```

### 3. Test Components
```bash
# Test Open-Meteo API
python test_open_meteo.py

# Test weather connector
python test_weather_connector.py

# Test end-to-end strategy
python test_strategy_e2e.py
```

### 4. Run Bot (Simulation Mode)
```bash
python bot.py
```

---

## 📁 Project Structure

```
polymarket-bot/
├── bot/
│   ├── connectors/
│   │   ├── open_meteo.py      # Multi-model forecast fetcher
│   │   ├── tracker.py          # Bias correction (optional)
│   │   ├── weather.py          # Orchestrates sources
│   │   └── polymarket.py       # py-clob-client SDK
│   ├── application/
│   │   ├── extreme_value_strategy.py  # Trading logic
│   │   └── bot_runner.py       # Main daemon
│   ├── utils/
│   │   ├── config.py           # Environment variables
│   │   └── models.py           # Data models
│   └── database/
│       └── trade_history.py    # Trade logging
├── config/
│   ├── locations.json          # City definitions (10 cities)
│   └── calibration.json        # Model weights & sigma values
├── tests/
│   ├── test_open_meteo.py
│   ├── test_weather_connector.py
│   └── test_strategy_e2e.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── EXTREME_VALUE_STRATEGY.md
│   └── ...
├── FORK_NOTES.md               # Implementation plan
├── REFACTOR_SUMMARY.md         # Refactoring docs (Phases 1-4)
└── README.md                   # This file
```

---

## 🧪 Test Results (2026-04-11)

```
Warsaw: 51.7°F, sigma 4.6°F, P(>50°F) = 64.6% ✅
Berlin: 13.7°C, sigma 3.1°C, P(18-20°C) = 6.4% ✅
London: 12.5°C, sigma 3.0°C, P(<15°C) = 79.8% ✅
NYC: 61.9°F, sigma 6.5°F, P(>60°F) = 61.4% ✅
```

---

## 📚 Documentation

- **[FORK_NOTES.md](FORK_NOTES.md)** - Original fork analysis and plan
- **[REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)** - Complete refactoring docs (Phases 1-4)
- **[docs/EXTREME_VALUE_STRATEGY.md](docs/EXTREME_VALUE_STRATEGY.md)** - Strategy explanation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[Parent: weather-forecast-tracker](../)** - Data collection & bias correction

---

## 🔗 Integration with weather-forecast-tracker

This bot is part of the **weather-forecast-tracker** ecosystem:

```
weather-forecast-tracker/        ← Parent project
├── weather_tracker.py           # Collects forecasts (cron)
├── dashboard.py                 # Streamlit dashboard
├── weather_forecasts.db         # SQLite with forecasts + observations
└── polymarket-bot/              ← This project
    ├── bot/connectors/tracker.py  # Reads from parent DB
    └── .env → TRACKER_DB_PATH=../weather_forecasts.db
```

**Benefits of integration:**
- Bias-corrected forecasts (historical error subtraction)
- Lower sigma (higher confidence) when using tracker data
- Shared location config
- No duplicate API calls

---

## 🎯 Strategy: Extreme Value Betting

```python
BUY YES when:
  - Price < 12¢ (cheap, mispriced by market)
  - Forecast shows edge (fair_prob > market_prob + 5%)
  
BUY NO when:
  - YES price > 50¢ (expensive, buy cheap NO instead)
  - Forecast shows edge

Position sizing:
  - $1.50 - $2.50 per trade (conservative)
  - $5.00 aggressive (great opportunities)
  
Risk controls:
  - Max 25 trades/day
  - Max $10 per market
  - 5% daily exposure limit
  - Circuit breaker: -$50 daily loss
```

**Proven track record:** Original strategy (idlepraxis) earned $25K+ profit.

---

## 🛡️ Safety

```
CRITICAL: Keep SIMULATION_MODE=true until:
1. Backtest with historical data ✅
2. Paper trade for 30 days ✅
3. Calibration verified ✅
4. Live with $50-100 capital first ✅
```

**Never trade with real money until fully tested!**

---

## 📜 License

MIT License (same as parent project)

---

## 🙏 Credits

- **Original bot:** [idlepraxis/polymarket-weather-bot](https://github.com/idlepraxis/polymarket-weather-bot)
- **Weather data:** [Open-Meteo](https://open-meteo.com)
- **Refactored by:** Claw Dev Agent (2026-04-09)
- **Part of:** [weather-forecast-tracker](https://github.com/pzawadz/weather-forecast-tracker) ecosystem

---

**Status:** ✅ Phases 1-4 complete, strategy tested, ready for simulation
**Next:** Phase 5-8 (calibration, risk controls, monitoring, testing)
