# Polymarket Integration - Architecture & Implementation Plan

**Created:** 2026-04-09  
**Status:** Planning Phase  
**Target:** Automated weather betting based on forecast accuracy

---

## 1. Overview

Integrate weather forecast system with Polymarket to:
1. Find relevant weather markets (temperature ranges)
2. Analyze odds vs forecast confidence
3. Place automated bets based on ensemble predictions
4. Track performance and P&L

---

## 2. Polymarket API Research

### 2.1 Key Endpoints (Public)

**Base URL:** `https://gamma-api.polymarket.com`

#### Market Discovery:
```
GET /markets
- Search markets by keywords ("weather", "temperature", city names)
- Filter by active/closed
- Get market metadata (question, outcomes, liquidity)
```

#### Price Data:
```
GET /markets/{market_id}
- Current prices (YES/NO odds)
- Liquidity
- Volume
- Market status

GET /order-book/{market_id}
- Bid/ask spreads
- Order depth
```

#### Historical Data:
```
GET /prices-history?market={market_id}
- Price movements over time
- For backtesting strategies
```

### 2.2 Trading API (Authenticated)

**Authentication:** API Key + Signature

**Note:** Trading requires:
- Polymarket account
- Wallet connection (Polygon blockchain)
- USDC balance
- API credentials

#### Place Orders:
```
POST /orders
- Market orders (instant execution)
- Limit orders (price targets)
- Size, side (BUY/SELL)
```

#### Manage Positions:
```
GET /positions
- Active positions
- Unrealized P&L

POST /orders/{id}/cancel
- Cancel pending orders
```

---

## 3. Module Architecture

### 3.1 File Structure

```
weather-forecast-tracker/
├── polymarket/
│   ├── __init__.py
│   ├── client.py           # API client (read-only)
│   ├── trader.py           # Trading logic (write)
│   ├── market_finder.py    # Search weather markets
│   ├── strategy.py         # Betting strategy
│   └── portfolio.py        # Position tracking, P&L
├── config.py               # Add POLYMARKET_* constants
├── polymarket_bot.py       # Main automation script
└── POLYMARKET.md           # This file
```

### 3.2 Core Components

#### **client.py** - API Wrapper
```python
class PolymarketClient:
    def __init__(self, api_key=None):
        self.base_url = "https://gamma-api.polymarket.com"
        self.api_key = api_key  # Optional for read-only
    
    def search_markets(self, keywords, active_only=True):
        """Search markets by keywords"""
    
    def get_market(self, market_id):
        """Get market details + current prices"""
    
    def get_orderbook(self, market_id):
        """Get bid/ask spread"""
    
    def get_price_history(self, market_id, days=7):
        """Historical prices for backtesting"""
```

#### **market_finder.py** - Market Discovery
```python
class WeatherMarketFinder:
    def __init__(self, client):
        self.client = client
    
    def find_temperature_markets(self, city, date):
        """
        Find markets like:
        - "Paris temperature > 25°C on April 10"
        - "London 15-20°C range on April 10"
        
        Returns: List[Market] with metadata
        """
    
    def filter_by_liquidity(self, markets, min_liquidity=1000):
        """Only bet on liquid markets"""
    
    def filter_by_date(self, markets, target_date):
        """Only relevant dates"""
```

#### **strategy.py** - Betting Logic
```python
class WeatherBettingStrategy:
    def __init__(self, forecast_db, polymarket_client):
        self.db = forecast_db
        self.client = polymarket_client
    
    def evaluate_market(self, market, city, date):
        """
        Compare market odds vs our forecast:
        
        Our forecast: 25.8°C (TOP 3 ensemble)
        Market: "Paris > 25°C" YES price: 60¢ (implied 60% prob)
        
        Our confidence: 85% (based on spread + historical accuracy)
        
        → Edge: 25% → BET YES!
        """
    
    def calculate_edge(self, market_price, our_prob):
        """
        Edge = our_prob - market_price
        
        Only bet if edge > 10% (conservative)
        """
    
    def calculate_bet_size(self, edge, bankroll):
        """
        Kelly Criterion:
        bet_fraction = (edge * our_prob - (1 - our_prob)) / edge
        
        BUT: Use fractional Kelly (10-25%) for safety
        """
    
    def should_bet(self, market, forecast):
        """
        Decision logic:
        1. Check edge > 10%
        2. Check liquidity > $1000
        3. Check our forecast confidence (spread < 2°C)
        4. Check time until resolution (18-24h ideal)
        
        Returns: (should_bet: bool, side: YES/NO, size: float)
        """
```

#### **trader.py** - Order Execution
```python
class PolymarketTrader:
    def __init__(self, client):
        self.client = client
    
    def place_order(self, market_id, side, size, price=None):
        """
        Place market or limit order
        
        Args:
            market_id: Market to trade
            side: "BUY" or "SELL"
            size: Amount in USDC
            price: Limit price (optional, None = market order)
        
        Returns: Order confirmation
        """
    
    def cancel_order(self, order_id):
        """Cancel pending order"""
    
    def get_positions(self):
        """Current open positions"""
    
    def close_position(self, market_id):
        """Exit position (sell YES or buy back NO)"""
```

#### **portfolio.py** - Performance Tracking
```python
class PolymarketPortfolio:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
    
    def log_trade(self, market_id, side, size, price, forecast_used):
        """Record every trade"""
    
    def log_resolution(self, market_id, outcome, pnl):
        """Record market resolution + profit/loss"""
    
    def get_performance_stats(self):
        """
        Returns:
        - Total trades
        - Win rate
        - Total P&L
        - ROI
        - Sharpe ratio
        - Per-city performance
        """
    
    def get_open_positions(self):
        """Current exposure"""
```

---

## 4. Implementation Phases

### Phase 1: Read-Only Integration (Week 1) ✅ SAFE

**Goal:** Market discovery + analysis (NO TRADING YET)

**Tasks:**
1. ✅ Create `polymarket/client.py` with read-only methods
2. ✅ Create `polymarket/market_finder.py`
3. ✅ Test: Find Paris/London/Munich/Warsaw temperature markets
4. ✅ Create `polymarket/strategy.py` - calculate edges (dry-run only)
5. ✅ Create dashboard section: "💰 Polymarket Opportunities"
   - Show markets found
   - Show our forecast vs market odds
   - Show calculated edge
   - Show recommended bet size (hypothetical)

**Deliverable:** Dashboard shows opportunities but doesn't trade

**Safety:** NO API keys, NO wallet, NO real money

---

### Phase 2: Paper Trading (Week 2) 📝 SIMULATION

**Goal:** Simulate trades, track hypothetical performance

**Tasks:**
1. Create `polymarket/portfolio.py` with simulated trading
2. Log every "would-be" trade to database
3. Track simulated P&L
4. Compare simulated performance vs actual market resolutions
5. Dashboard: "📊 Paper Trading Performance"

**Deliverable:** 7-14 days of simulated trades with metrics

**Safety:** Still NO real money, validate strategy works

---

### Phase 3: Live Trading - Small Scale (Week 3-4) 💰 REAL MONEY

**Goal:** Start with $50-100 test capital

**Tasks:**
1. Setup Polymarket account + wallet
2. Get API credentials
3. Implement `polymarket/trader.py` with real orders
4. Set hard limits:
   - Max bet: $10 per market
   - Max daily: $30
   - Max total exposure: $100
5. Manual approval for first 10 trades (safety check)
6. Alert system (email/telegram) for every trade

**Deliverable:** Live trading with tight risk controls

**Safety:** Small capital, hard limits, manual oversight

---

### Phase 4: Scale Up (Month 2+) 🚀

**Goal:** Increase capital after proven track record

**Requirements:**
- ✅ 30+ trades completed
- ✅ Win rate > 55%
- ✅ Positive ROI
- ✅ No major bugs/errors

**Scale:**
- Capital: $500-1000
- Max bet: $50-100 per market
- Full automation

---

## 5. Risk Management

### 5.1 Position Limits

```python
LIMITS = {
    'max_bet_size': 10,           # USD per bet (Phase 3)
    'max_daily_bets': 3,          # Bets per day
    'max_total_exposure': 100,    # Total capital at risk
    'min_liquidity': 1000,        # Only liquid markets
    'min_edge': 0.10,             # 10% minimum edge
    'max_edge': 0.40,             # Too good = suspicious
}
```

### 5.2 Safety Checks

```python
def pre_trade_checks(market, forecast):
    """
    Safety checks before placing order:
    
    1. Market liquidity > $1000
    2. Edge > 10% and < 40%
    3. Forecast confidence high (spread < 2°C)
    4. Time to resolution: 12-36h (ideal window)
    5. Total exposure < limit
    6. Daily trade count < limit
    7. Market not manipulated (check price history)
    
    Returns: (safe: bool, reason: str)
    """
```

### 5.3 Circuit Breakers

```python
CIRCUIT_BREAKERS = {
    'max_daily_loss': 50,         # Stop if lose $50 in a day
    'max_consecutive_losses': 3,  # Pause after 3 losses
    'max_weekly_loss': 100,       # Stop if lose $100 in a week
}
```

---

## 6. Database Schema

### 6.1 New Tables

```sql
-- Markets tracked
CREATE TABLE polymarket_markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT UNIQUE NOT NULL,
    question TEXT NOT NULL,
    city TEXT,
    date DATE,
    outcome_type TEXT,  -- 'range', 'over_under'
    threshold REAL,     -- e.g., 25.0 for "> 25°C"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trades (real or simulated)
CREATE TABLE polymarket_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    trade_type TEXT NOT NULL,  -- 'paper' or 'live'
    side TEXT NOT NULL,        -- 'BUY' or 'SELL'
    size REAL NOT NULL,        -- USD amount
    price REAL NOT NULL,       -- Entry price (0-1)
    forecast_used REAL,        -- Our forecast value
    ensemble_error REAL,       -- Our confidence estimate
    edge REAL,                 -- Calculated edge
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Resolution (filled later)
    resolved_at TIMESTAMP,
    outcome TEXT,              -- 'YES' or 'NO'
    exit_price REAL,
    pnl REAL,                  -- Profit/loss in USD
    
    FOREIGN KEY (market_id) REFERENCES polymarket_markets(market_id)
);

-- Daily performance
CREATE TABLE polymarket_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    trades_count INTEGER,
    wins INTEGER,
    losses INTEGER,
    win_rate REAL,
    total_pnl REAL,
    roi REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Example Workflow

### 7.1 Morning (08:00 UTC)

```python
# 1. Collect today's forecasts (already done by cron)
# 2. Search for relevant markets

finder = WeatherMarketFinder(client)
markets = finder.find_temperature_markets(
    cities=['paris', 'london', 'munich', 'warsaw'],
    dates=[today, tomorrow]
)

# 3. Evaluate each market
strategy = WeatherBettingStrategy(db, client)

for market in markets:
    city = market.city
    date = market.date
    
    forecast = get_ensemble_forecast(city, date)
    
    decision = strategy.should_bet(market, forecast)
    
    if decision.should_bet:
        print(f"🎯 OPPORTUNITY:")
        print(f"   Market: {market.question}")
        print(f"   Our forecast: {forecast.temp:.1f}°C")
        print(f"   Market price: {market.yes_price:.0%}")
        print(f"   Edge: {decision.edge:.1%}")
        print(f"   Recommended: {decision.side} ${decision.size:.2f}")
        
        if LIVE_TRADING:
            trader.place_order(market.id, decision.side, decision.size)
```

### 7.2 Evening (20:00 UTC)

```python
# 1. Observations collected (already done by cron)
# 2. Check market resolutions

portfolio = PolymarketPortfolio(db)
open_positions = portfolio.get_open_positions()

for position in open_positions:
    market = client.get_market(position.market_id)
    
    if market.resolved:
        outcome = market.outcome
        pnl = calculate_pnl(position, outcome)
        
        portfolio.log_resolution(market.id, outcome, pnl)
        
        print(f"✅ Market resolved: {market.question}")
        print(f"   Outcome: {outcome}")
        print(f"   P&L: ${pnl:+.2f}")
```

---

## 8. Success Metrics

### 8.1 Target Performance (Phase 3+)

```
Win Rate: > 55% (industry standard for sports betting)
ROI: > 10% per month (aggressive but achievable)
Sharpe Ratio: > 1.0 (risk-adjusted returns)
Max Drawdown: < 20% (capital preservation)
```

### 8.2 Benchmark

```
Compare to:
- Random betting (50% win rate)
- Always bet YES (market baseline)
- Buy & hold USDC (0% return)
```

---

## 9. Next Steps

### Immediate (Today):

1. ✅ Create this POLYMARKET.md plan
2. ✅ Research API endpoints (done above)
3. ⏳ Create `polymarket/` directory
4. ⏳ Implement `client.py` (read-only)
5. ⏳ Test: Search for Paris temperature markets

### This Week:

1. Complete Phase 1 (read-only integration)
2. Add Polymarket section to dashboard
3. Test market discovery for all 4 cities
4. Document findings

### Next Week:

1. Phase 2: Paper trading
2. Track simulated performance
3. Analyze edge calculation accuracy

---

## 10. Security & Compliance

### 10.1 API Key Management

```python
# NEVER commit keys to git!

# .env file (gitignored):
POLYMARKET_API_KEY=xxx
POLYMARKET_SECRET=xxx
WALLET_PRIVATE_KEY=xxx  # CRITICAL - never expose

# config.py:
import os
from dotenv import load_dotenv

load_dotenv()

POLYMARKET_API_KEY = os.getenv('POLYMARKET_API_KEY')
POLYMARKET_SECRET = os.getenv('POLYMARKET_SECRET')
```

### 10.2 Legal Considerations

**Important:**
- Polymarket may have geographic restrictions
- Check local gambling/prediction market laws
- This is for educational/research purposes
- Start with small amounts to test
- Not financial advice

---

## 11. Resources

### Documentation:
- Polymarket API Docs: https://docs.polymarket.com
- Polymarket Dev Portal: https://github.com/Polymarket

### Python Libraries:
```bash
pip install py-clob-client  # Official Polymarket Python client
pip install web3            # For blockchain interaction
pip install python-dotenv   # For .env management
```

---

**Status:** Planning complete, ready for Phase 1 implementation  
**Risk Level:** Phase 1 = ZERO (read-only), Phase 3 = LOW (small capital)  
**Timeline:** 4 weeks to live trading (if Phase 1-2 successful)
