# Weather Forecast Tracker + Polymarket Bot

**Two-component weather prediction system:**
1. **Weather Forecasting** - Multi-model ensemble forecasts with bias correction (PRODUCTION)
2. **Polymarket Trading Bot** - Automated weather betting using forecast data (READY FOR TESTING)

[![Dashboard](https://img.shields.io/badge/dashboard-live-brightgreen)](https://d2175rmfwid55c.cloudfront.net)
[![Weather](https://img.shields.io/badge/weather-production-brightgreen)]()
[![Bot](https://img.shields.io/badge/polymarket_bot-testing-yellow)]()

---

## 📊 Weather Forecasting System (PRODUCTION)

Automated weather forecast collection and accuracy tracking for **4 European cities** with ensemble predictions optimized for betting strategies.

### 🌍 Locations
- **Warsaw 🇵🇱** (52.23°N, 21.01°E) - 7 models including IMGW HYBRID
- **Paris 🇫🇷** (48.86°N, 2.35°E) - 6 global models
- **Munich 🇩🇪** (48.14°N, 11.58°E) - 6 global models  
- **London 🇬🇧** (51.51°N, -0.13°W) - 6 global models

### ✨ Features

- ✅ **Multi-model ensemble**: 6-7 weather models per city
- ✅ **Global models**: ECMWF IFS (9km), ICON-EU (7km), ICON Global (13km), GFS (13km), Meteo France, GEM
- ✅ **Polish model**: IMGW HYBRID (2.5-4km, Warsaw only) - **best resolution**
- ✅ **Automated collection**: Every 4 hours
- ✅ **Same-day observations**: Smart collection after 18:00 UTC (12-18h faster feedback)
- ✅ **Ensemble predictions**: Median + mean consensus (TOP 3)
- ✅ **Bias correction**: 7-day rolling average per model
- ✅ **Betting analysis**: 18h/24h/48h lead time comparison (optimal Polymarket timing)
- ✅ **Web dashboard**: Real-time forecasts + accuracy tracking
- ✅ **Performance**: ~0.4s per city (parallel API requests)

### 🎯 Current Accuracy (2026-04-09)

```
🇵🇱 Warsaw:  Ensemble 0.05°C error (EXCELLENT!)
🇫🇷 Paris:   Ensemble 0.37°C error (EXCELLENT!)
🇩🇪 Munich:  Ensemble 0.90°C error (GOOD)
🇬🇧 London:  Ensemble 0.93°C error (GOOD)

100% success rate for Polymarket range betting (±1°C) ✅
```

### 📈 Dashboard

**Live:** https://d2175rmfwid55c.cloudfront.net

Features:
- Current forecasts (all models + ensemble)
- **Betting Performance** section (18h/24h/48h lead time analysis)
- Forecast evolution timeline
- Model performance comparison
- Accuracy over time
- Temperature pattern analysis

---

## 💰 Polymarket Bot (READY FOR TESTING)

**Status:** ✅ Phases 1-4 complete, simulation ready (2026-04-10)

Automated trading bot for temperature markets on Polymarket using **global weather forecasts** and **extreme value strategy**.

**Location:** [`polymarket-bot/`](polymarket-bot/) subdirectory

### ✨ Key Features

- **Global coverage:** Warsaw, Berlin, London, Paris, NYC, LA, Chicago, Miami, Houston, Phoenix
- **Multi-model forecasts:** ECMWF, ICON, GFS, Meteo France, GEM (5 models via Open-Meteo)
- **Dynamic sigma:** Adapts to model agreement (higher confidence when models agree)
- **Bias correction:** Optional integration with weather-forecast-tracker DB
- **Proven strategy:** Extreme value betting (forked from idlepraxis, $25K+ track record)
- **Risk controls:** Circuit breakers, position limits, simulation mode

### 🧪 Test Results (2026-04-11)

```
Warsaw: 51.7°F, sigma 4.6°F, P(>50°F) = 64.6% ✅
Berlin: 13.7°C, sigma 3.1°C, P(18-20°C) = 6.4% ✅
London: 12.5°C, sigma 3.0°C, P(<15°C) = 79.8% ✅
NYC: 61.9°F, sigma 6.5°F, P(>60°F) = 61.4% ✅
```

### 🚀 Quick Start

```bash
cd polymarket-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (copy .env.example to .env)
cp .env.example .env
nano .env

# Test
python test_open_meteo.py
python test_strategy_e2e.py

# Run (simulation mode)
python bot.py
```

### 📚 Documentation

- **[polymarket-bot/README.md](polymarket-bot/README.md)** - Complete bot documentation
- **[polymarket-bot/REFACTOR_SUMMARY.md](polymarket-bot/REFACTOR_SUMMARY.md)** - Phases 1-4 refactoring docs
- **[polymarket-bot/FORK_NOTES.md](polymarket-bot/FORK_NOTES.md)** - Implementation plan
- **[docs/polymarket/](docs/polymarket/)** - Original architecture docs (microservices plan)

### 🎯 Strategy

```python
BUY YES: Price < 12¢ + forecast edge > 5%
BUY NO: YES price > 50¢ + forecast edge > 5%
Position: $1.50-$5.00 per trade
Risk: Circuit breaker at -$50 daily loss
```

### ⚠️ Status

```
✅ Phases 1-4 complete (fork, weather, execution, strategy)
✅ Tests passing (parsing, forecasts, probability)
🔄 Phase 5-8 TODO (calibration, monitoring, testing)
⏸️ Live trading ON HOLD until fully tested
```

**Next:** Paper trading in simulation mode for 30 days before live deployment.

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10+
pip3 install requests beautifulsoup4 lxml streamlit plotly pandas
```

### Installation

```bash
git clone https://github.com/pzawadz/weather-forecast-tracker.git
cd weather-forecast-tracker
```

### Usage

#### Collect forecasts for all cities:
```bash
python3 weather_tracker.py forecast-all
```

#### Collect observations for all cities:
```bash
python3 weather_tracker.py observe-all
```

#### Run dashboard locally:
```bash
streamlit run dashboard.py --server.port=8502
```

### Production Deployment

**Current deployment:** Ireland EC2 (172.31.13.147, eu-west-1)

```bash
# SSH to server
ssh -i ~/.ssh/id_ed25519 ubuntu@172.31.13.147

# Dashboard service
sudo systemctl status weather-dashboard.service
sudo systemctl restart weather-dashboard.service

# Logs
tail -f logs/forecast.log
tail -f logs/observe.log
```

**Cron schedule:**
```bash
0 */4 * * *  # Forecasts every 4 hours
0 8 * * *    # Observations (morning)
0 20 * * *   # Observations (evening, same-day collection)
```

---

## 📁 Project Structure

```
weather-forecast-tracker/
├── weather_tracker.py           # Main collector
├── dashboard.py                 # Streamlit dashboard
├── config.py                    # Centralized configuration
├── db_helpers.py                # Database utilities
├── imgw_api_scraper.py          # IMGW HYBRID scraper
├── polymarket/                  # Polymarket bot (planned)
│   ├── client.py                # CLOB API client
│   └── __init__.py
├── docs/
│   ├── polymarket/
│   │   ├── POLYMARKET.md        # Initial research (14KB)
│   │   ├── POLYMARKET_ARCHITECTURE.md  # Full architecture (20KB) ⭐
│   │   ├── BETTING_GUIDE.md
│   │   └── BETTING_PERFORMANCE_GUIDE.md
│   ├── weather/
│   │   ├── ARCHITECTURE.md      # Weather system architecture
│   │   ├── MULTILOCATION_DEPLOYMENT.md
│   │   ├── SMART_OBSERVATION.md
│   │   ├── IMGW_DEPLOYMENT.md
│   │   └── [+ 6 more docs]
│   └── deployment/
│       ├── PRODUCTION.md
│       ├── QUICKSTART.md
│       └── [+ 3 more docs]
├── infra/
│   └── cloudformation-dashboard-eu.yaml
├── logs/
│   ├── forecast.log
│   └── observe.log
├── weather_forecasts.db         # SQLite database
├── ROADMAP.md
└── README.md                    # This file
```

---

## 🗄️ Database Schema

### `forecasts` table
```sql
CREATE TABLE forecasts (
    model TEXT NOT NULL,
    forecast_time TIMESTAMP NOT NULL,
    target_date DATE NOT NULL,
    hours_ahead INTEGER NOT NULL,
    temp_max REAL NOT NULL,
    location TEXT NOT NULL DEFAULT 'warsaw',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_forecasts_target ON forecasts(target_date, location);
CREATE INDEX idx_forecasts_model ON forecasts(model, forecast_time);
CREATE INDEX idx_forecasts_location ON forecasts(location, target_date);
```

### `observations` table
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    temp_max REAL NOT NULL,
    location TEXT NOT NULL DEFAULT 'warsaw',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, location)
);

CREATE INDEX idx_observations_date ON observations(date, location);
```

### `model_bias` table
```sql
CREATE TABLE model_bias (
    model TEXT NOT NULL,
    date DATE NOT NULL,
    bias REAL NOT NULL,
    hours_ahead INTEGER NOT NULL,
    location TEXT NOT NULL DEFAULT 'warsaw',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model, date, hours_ahead, location)
);

CREATE INDEX idx_bias_date ON model_bias(date, hours_ahead);
CREATE INDEX idx_bias_model ON model_bias(model, location, date);
```

---

## 🌐 API Sources

### Weather Data

**Open-Meteo Forecast API:**
- ECMWF IFS 0.25° (9km)
- ICON-EU (7km) - Central Europe optimized
- ICON Global (13km)
- GFS Global (13km)
- Meteo France Seamless
- GEM Global (Canada)

**IMGW API (Poland only):**
- HYBRID 1.0 (UM 4km + AROME 2.5km combined)
- Best resolution: 2.5-4km (3x better than ICON-EU)
- Endpoint: `https://meteo.imgw.pl/api/v1/forecast/fcapi`

**Open-Meteo Historical API:**
- Actual temperature observations
- Endpoint: `https://archive-api.open-meteo.com/v1/archive`

### Polymarket (Planned)

**Gamma API:** Market discovery  
**CLOB API:** Trading (authenticated)  
**Data API:** Positions & analytics  
**Bridge API:** Deposits/withdrawals  
**Relayer API:** Gasless on-chain transactions  
**WebSocket:** Real-time orderbook + fills

---

## 📊 Performance Metrics

### Collection Speed (Parallel)
```
Warsaw:  0.40s (7 models)
Paris:   0.28s (6 models)
Munich:  0.28s (6 models)
London:  0.28s (6 models)

Total: ~1.5s for all 4 cities (24 API calls)
10x-120x faster than sequential collection
```

### Database Performance
```
Forecast queries: 50-200ms (with indexes)
Dashboard load: ~5s (5 min cache)
Database size: ~500KB per week
```

### Accuracy Stats (Apr 7-9, 2026)
```
Average ensemble error: 0.56°C
Best single model: ICON-EU (Warsaw, 0.0°C)
Worst outlier: ECMWF (Paris, -3.5°C)
Polymarket bet success: 100% (4/4 cities)
```

---

## 🔄 Continuous Improvement

### Recently Added (Apr 2026)
- ✅ Multi-location support (4 cities)
- ✅ IMGW HYBRID integration (Polish model)
- ✅ Smart observation (same-day collection after 18:00 UTC)
- ✅ Betting Performance dashboard section
- ✅ Timeline chart (actual vs 18h/24h/48h forecasts)
- ✅ Architecture refactoring (config.py, db_helpers.py, indexes)
- ✅ Dashboard caching (5 min TTL, 10x speedup)

### Roadmap
- [ ] Phase 2: ML ensemble model (8-12h effort)
- [ ] Alerts & notifications (Telegram/email, 3-5h)
- [ ] Additional Polish models (ALARO 4km)
- [ ] REST API endpoint (4-6h)
- [ ] Polymarket bot implementation (14 weeks, ON HOLD until June)

---

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

### Reporting Issues
- Weather data inaccuracies
- Dashboard bugs
- Architecture feedback

### Feature Requests
- New cities/models
- Additional analytics
- Dashboard improvements

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🔗 Links

- **Dashboard:** https://d2175rmfwid55c.cloudfront.net
- **GitHub:** https://github.com/pzawadz/weather-forecast-tracker
- **Architecture:** [docs/polymarket/POLYMARKET_ARCHITECTURE.md](docs/polymarket/POLYMARKET_ARCHITECTURE.md)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)

---

## 📞 Contact

**Questions?** Open an issue on GitHub.

**Status Updates:**
- Weather system: ✅ PRODUCTION (eu-west-1)
- Dashboard: ✅ LIVE (CloudFront)
- Polymarket bot: ⏸️ ON HOLD (resumes June 2026)

---

**Last Updated:** 2026-04-09  
**Version:** 1.0.0 (Weather System) / 0.1.0 (Polymarket Planning)
