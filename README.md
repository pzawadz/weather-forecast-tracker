# Weather Forecast Tracker + Polymarket Bot

**Multi-location weather forecasting system with automated betting capabilities (planned)**

[![Production](https://img.shields.io/badge/dashboard-live-brightgreen)](https://d2175rmfwid55c.cloudfront.net)
[![Status](https://img.shields.io/badge/weather-production-brightgreen)]()
[![Status](https://img.shields.io/badge/polymarket-planning-yellow)]()

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

## 💰 Polymarket Bot (PLANNED)

**Status:** ⏸️ ON HOLD until June 2026 (weather betting season)

Automated trading bot for temperature-based prediction markets using weather forecast accuracy.

### 📐 Architecture

**[Complete Microservices Architecture](docs/polymarket/POLYMARKET_ARCHITECTURE.md)** (20KB detailed plan)

9 independent services:
1. **Discovery Service** - Find temperature markets
2. **Strategy Service** - Edge calculation + Kelly sizing
3. **Trading Service** - Order placement (EIP-712 + HMAC auth)
4. **Risk Management** - Position limits + circuit breakers
5. **Monitoring Service** - Prometheus + Grafana + Telegram alerts
6. **WebSocket Service** - Real-time orderbook + fills
7. **Relayer Service** - On-chain operations (split/merge/redeem)
8. **Data Persistence** - PostgreSQL + Redis
9. **Orchestrator** - Service discovery + workflow engine

### 🚨 Geographic Restriction

**Poland has "close-only" status on Polymarket:**
- ❌ Cannot open NEW positions from Poland
- ✅ Can close existing positions
- ❌ VPN usage prohibited

**Solution:** Bot will be deployed to **AWS us-east-1** (no restrictions)

### 📅 Timeline

```
Phase 1-2: Foundation (4 weeks)
Phase 3-6: Core Trading (6 weeks)  
Phase 7-8: Orchestration + Testing (3 weeks)
Phase 9-10: Deployment + Live (1 week)

Total: ~14 weeks to live trading
Cost: ~$120/month AWS infrastructure
```

### 🔒 Security

- Two-level auth: EIP-712 + HMAC-SHA256
- Heartbeat mechanism (60s, critical!)
- Circuit breakers (daily loss, consecutive losses)
- Position limits ($10 max bet, $100 max exposure for Phase 3)
- AWS Secrets Manager for credentials
- VPC private subnets + NAT Gateway

### 📊 Expected Performance

```
Target Win Rate: > 55%
Target ROI: > 10% per month
Risk Controls:
  - Max bet: $10 (Phase 3)
  - Max daily bets: 3
  - Max daily loss: $50 (circuit breaker)
  - Max consecutive losses: 3 (pause trading)
```

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
