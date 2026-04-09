# Polymarket Bot - Microservices Architecture Plan

**Created:** 2026-04-09  
**Status:** Planning Phase (No Code Yet)  
**Based on:** Official Polymarket API Documentation Research

---

## 🚨 CRITICAL: Geographic Restrictions

### Poland (PL) Status: "Close-Only"

⚠️ **Blocking Issue Identified:**

```
Poland has "close-only" status on Polymarket:
❌ Cannot open NEW positions from Poland
✅ Can close existing positions
❌ VPN usage prohibited in ToS (§2.1.4)
```

### Solution: Deploy Outside Poland

```
Primary Region: AWS us-east-1 (US East)
Backup Region: AWS eu-west-1 (Ireland, non-PL)

Bot must run from non-restricted geography.
All trading operations execute from cloud infrastructure.
```

---

## 📐 High-Level Architecture

### 9 Independent Microservices

```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY / ORCHESTRATOR               │
│          (HTTP API + gRPC + Message Queue)                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────────┐
        │                   │                       │
        ▼                   ▼                       ▼
┌──────────────┐   ┌──────────────┐       ┌──────────────┐
│   DISCOVERY  │   │   STRATEGY   │       │   TRADING    │
│   SERVICE    │──▶│   SERVICE    │──────▶│   SERVICE    │
└──────────────┘   └──────────────┘       └──────────────┘
        │                   │                       │
        │                   ▼                       ▼
        │           ┌──────────────┐       ┌──────────────┐
        │           │  RISK MGMT   │◀──────│  MONITORING  │
        │           │  SERVICE     │       │  SERVICE     │
        │           └──────────────┘       └──────────────┘
        │                                           │
        ▼                                           ▼
┌──────────────┐                           ┌──────────────┐
│  WEBSOCKET   │                           │   RELAYER    │
│  SERVICE     │                           │   SERVICE    │
└──────────────┘                           └──────────────┘
        │                                           │
        └───────────────────┬───────────────────────┘
                            ▼
                    ┌──────────────┐
                    │     DATA     │
                    │  PERSISTENCE │
                    │   SERVICE    │
                    └──────────────┘
                            │
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │   + Redis    │
                    └──────────────┘
```

---

## 🔧 Service Breakdown

### 1. Discovery Service 🔍

**Responsibility:**
- Search temperature markets across cities
- Cache market metadata (conditionId, clobTokenIds)
- Monitor tick size changes
- Filter by enableOrderBook, negRisk flags

**Tech Stack:**
```
Language: Python (asyncio)
Framework: FastAPI
Cache: Redis (5 min TTL)
Database: PostgreSQL
```

**API Sources:**
- Gamma API: `GET /events`, `GET /markets`
- CLOB API: `GET /tick-size`

**Config:**
```yaml
discovery:
  gamma_api_url: "https://gamma-api.polymarket.com"
  clob_api_url: "https://clob.polymarket.com"
  cache_ttl_seconds: 300
  poll_interval_seconds: 60
  target_cities:
    - warsaw
    - paris
    - london
    - munich
```

---

### 2. Strategy Service 🧠

**Responsibility:**
- Forecast vs market odds analysis
- Edge calculation
- Kelly Criterion bet sizing
- Multi-outcome optimization (negative risk)

**Tech Stack:**
```
Language: Python
Framework: FastAPI
ML: NumPy, SciPy
Database: PostgreSQL
```

**Core Algorithm:**
```python
def evaluate_market(market, forecast):
    # 1. Market implied probability
    market_prob = get_book_midpoint(market.token_id_yes)
    
    # 2. Our confidence
    our_prob = calculate_confidence(
        forecast.ensemble_median,
        forecast.spread,
        forecast.historical_mae
    )
    
    # 3. Edge
    edge = our_prob - market_prob
    
    # 4. Threshold check
    if edge < 0.10:  # Min 10%
        return NO_BET
    
    # 5. Kelly sizing (25% fractional)
    bet_size = 0.25 * edge * bankroll
    
    return BettingDecision(
        should_bet=True,
        side="BUY",
        size=bet_size,
        edge=edge
    )
```

**Config:**
```yaml
strategy:
  min_edge: 0.10
  max_edge: 0.40
  kelly_fraction: 0.25
  min_confidence: 0.70
  max_spread_celsius: 2.0
  optimal_lead_time_hours: 18
```

---

### 3. Trading Service 💰

**Responsibility:**
- Order placement (POST /order)
- Order cancellation (DELETE /order)
- Heartbeat maintenance (POST /heartbeats)
- Retry logic (425, 429)
- L2 authentication (HMAC-SHA256)

**Tech Stack:**
```
Language: Python
Framework: FastAPI
Auth: EIP-712 + HMAC
Queue: RabbitMQ
Database: PostgreSQL
```

**Critical Features:**

#### A) Two-Level Authentication

```python
# L1: EIP-712 for API key derivation
def derive_api_credentials(private_key, funder_address):
    signature = sign_eip712(private_key, domain)
    response = requests.post(
        "https://clob.polymarket.com/auth/api-key",
        json={"signature": signature, "funder": funder_address}
    )
    return response.json()  # {apiKey, secret, passphrase}

# L2: HMAC-SHA256 for request signing
def sign_request(method, path, body, timestamp, api_key, secret):
    message = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        base64.b64decode(secret),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()
```

#### B) Heartbeat (CRITICAL!)

```python
async def heartbeat_loop():
    """
    Send heartbeat every 60s.
    Missing heartbeat = auto-cancel all open orders!
    """
    while True:
        try:
            response = await client.post(
                "/heartbeats",
                headers=hmac_headers(api_key, secret)
            )
            logger.info(f"Heartbeat OK")
        except Exception as e:
            logger.critical(f"Heartbeat FAILED: {e}")
            # ALERT IMMEDIATELY!
        
        await asyncio.sleep(60)
```

#### C) Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((HTTPError425, HTTPError429))
)
async def place_order_with_retry(order):
    response = await client.post("/order", json=order)
    
    if response.status_code == 425:
        # Matching engine restart (Tuesdays 7 AM ET)
        raise HTTPError425("Engine restarting")
    
    if response.status_code == 429:
        # Rate limit
        raise HTTPError429("Rate limited")
    
    return response.json()
```

**Config:**
```yaml
trading:
  clob_api_url: "https://clob.polymarket.com"
  heartbeat_interval_seconds: 60
  order_expiry_hours: 24
  retry_max_attempts: 3
  retry_backoff_multiplier: 1
```

---

### 4. Risk Management Service 🛡️

**Responsibility:**
- Position limits enforcement
- Circuit breakers
- Pre-trade checks
- Portfolio exposure monitoring

**Tech Stack:**
```
Language: Go (performance)
Framework: gRPC
Database: PostgreSQL + Redis
```

**Hard Limits:**
```go
type RiskLimits struct {
    MaxBetSize           float64  // $10 (Phase 3)
    MaxDailyBets         int      // 3
    MaxTotalExposure     float64  // $100
    MinLiquidity         float64  // $1000
    MinEdge              float64  // 0.10
    MaxEdge              float64  // 0.40
    
    // Circuit breakers
    MaxDailyLoss         float64  // $50
    MaxConsecutiveLosses int      // 3
    MaxWeeklyLoss        float64  // $100
}
```

**Pre-Trade Checks:**
```go
func (s *RiskService) PreTradeCheck(order OrderRequest) RiskCheckResult {
    // 1. Exposure check
    if currentExposure + order.Size > s.limits.MaxTotalExposure {
        return REJECT("Exposure limit exceeded")
    }
    
    // 2. Bet size check
    if order.Size > s.limits.MaxBetSize {
        return REJECT("Bet size too large")
    }
    
    // 3. Daily count check
    if dailyOrderCount >= s.limits.MaxDailyBets {
        return REJECT("Daily bet limit reached")
    }
    
    // 4. Edge validation
    if order.Edge < s.limits.MinEdge || order.Edge > s.limits.MaxEdge {
        return REJECT("Edge outside range")
    }
    
    // 5. Circuit breaker check
    if s.isCircuitBreakerTripped() {
        return REJECT("Circuit breaker active")
    }
    
    return APPROVE
}
```

---

### 5. Monitoring Service 📊

**Responsibility:**
- Metrics collection (Prometheus)
- Alerting (Telegram/Email)
- Health checks
- P&L calculation
- Performance tracking

**Tech Stack:**
```
Language: Python
Framework: FastAPI
Metrics: Prometheus + Grafana
Alerts: Alertmanager → Telegram
Database: PostgreSQL + TimescaleDB
```

**Key Metrics:**
```python
# Trading
orders_placed_total = Counter("orders_placed_total")
orders_filled_total = Counter("orders_filled_total")
order_fill_latency = Histogram("order_fill_latency_seconds")

# Performance
pnl_daily = Gauge("pnl_daily_usd")
win_rate = Gauge("win_rate_percent")
sharpe_ratio = Gauge("sharpe_ratio")
max_drawdown = Gauge("max_drawdown_percent")

# System
heartbeat_failures = Counter("heartbeat_failures_total")
api_errors_total = Counter("api_errors_total", ["endpoint"])
websocket_disconnects = Counter("websocket_disconnects_total")
```

**Alert Conditions:**
```python
CRITICAL:
  - Heartbeat failed 3x in row
  - Circuit breaker tripped
  - Daily loss > $50

WARNING:
  - Low liquidity < $1000
  - High slippage > 2%
  - API error rate > 5%

INFO:
  - Order filled
  - Position closed with P&L
```

---

### 6. WebSocket Service 🔌

**Responsibility:**
- Market channel (orderbook, prices, tick changes)
- User channel (fills, order status)
- Event streaming to other services
- Reconnection logic

**Tech Stack:**
```
Language: Node.js
Framework: ws library
Message Broker: Redis Streams
Database: PostgreSQL
```

**Subscriptions:**

#### Market Channel (unauthenticated):
```javascript
const marketSubscription = {
    "assets_ids": [
        "12345678901234567890",  // YES token
        "98765432109876543210"   // NO token
    ],
    "type": "market"
};

// Events:
// - "book" (orderbook update)
// - "last_trade_price"
// - "price_change"
// - "tick_size_change" (CRITICAL!)
```

#### User Channel (authenticated):
```javascript
const userSubscription = {
    "auth": {
        "apiKey": "...",
        "secret": "...",
        "passphrase": "..."
    },
    "type": "user"
};

// Events:
// - "MATCHED" (order matched)
// - "MINED" (tx submitted)
// - "CONFIRMED" (tx confirmed)
// - "FILLED" (order filled)
```

---

### 7. Relayer Service 🔗

**Responsibility:**
- On-chain operations (approve, split, merge, redeem)
- Gasless transactions via Relayer API
- Negative risk token conversions
- Deposit/withdraw flows

**Tech Stack:**
```
Language: Python
Framework: FastAPI
Blockchain: web3.py (Polygon)
Database: PostgreSQL
```

**Operations:**
- `approve()`: Allow CTF contract to spend USDC.e
- `split()`: Convert USDC.e → YES + NO tokens
- `merge()`: Convert YES + NO → USDC.e
- `redeem()`: Redeem winning tokens → USDC.e
- `convertNoToYes()`: Negative risk conversion

---

### 8. Data Persistence Service 💾

**Responsibility:**
- Centralized database access
- Schema migrations
- Query optimization
- Backup/restore

**Tech Stack:**
```
Language: Python
Framework: SQLAlchemy ORM
Database: PostgreSQL 15
Cache: Redis
Backup: S3
```

**Schema Highlights:**
```sql
-- Markets
CREATE TABLE markets (
    id UUID PRIMARY KEY,
    condition_id TEXT UNIQUE,
    question TEXT,
    city TEXT,
    target_date DATE,
    clob_token_ids JSONB,
    tick_size DECIMAL(10,8),
    neg_risk BOOLEAN
);

-- Orders
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    order_id TEXT UNIQUE,
    market_id UUID REFERENCES markets(id),
    token_id TEXT,
    side TEXT,
    size DECIMAL(18,6),
    price DECIMAL(10,8),
    status TEXT,
    edge REAL,
    pnl DECIMAL(18,6)
);

-- Positions
CREATE TABLE positions (
    id UUID PRIMARY KEY,
    market_id UUID REFERENCES markets(id),
    token_id TEXT,
    size DECIMAL(18,6),
    avg_price DECIMAL(10,8),
    unrealized_pnl DECIMAL(18,6)
);
```

---

### 9. Orchestrator / API Gateway 🎛️

**Responsibility:**
- Service discovery
- Request routing
- Workflow orchestration
- External REST API
- Load balancing

**Tech Stack:**
```
Language: Go
Framework: gRPC Gateway
Message Queue: RabbitMQ
Registry: Consul / etcd
```

**Workflow Example:**
```go
func (o *Orchestrator) PlaceBet(ctx context.Context, req *BetRequest) (*BetResult, error) {
    // 1. Discovery
    market := o.discoveryClient.FindMarket(req.City, req.Date)
    
    // 2. Strategy
    decision := o.strategyClient.EvaluateMarket(market, req.Forecast)
    if !decision.ShouldBet {
        return &BetResult{Skipped: true}
    }
    
    // 3. Risk
    riskCheck := o.riskClient.PreTradeCheck(decision)
    if !riskCheck.Approved {
        return &BetResult{Rejected: true}
    }
    
    // 4. Trading
    orderResult := o.tradingClient.PlaceOrder(decision)
    
    // 5. Monitoring
    o.monitoringClient.SendAlert("Order placed", orderResult)
    
    return &BetResult{Success: true, OrderID: orderResult.ID}
}
```

---

## 🔄 Communication Patterns

### Synchronous (gRPC)
```
Orchestrator → Discovery: GetMarketMetadata()
Orchestrator → Strategy: EvaluateMarket()
Orchestrator → Risk: PreTradeCheck()
Orchestrator → Trading: PlaceOrder()
```

### Asynchronous (Redis Streams)
```
WebSocket Service: OrderFilled event
        ↓
    Redis Streams
        ↓
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
Monitoring  Risk   Trading  Data
```

---

## 🚀 Deployment

### Infrastructure
```yaml
Cloud: AWS
Region: us-east-1 (no Poland restrictions)

Services:
  - ECS Fargate: Container orchestration
  - RDS PostgreSQL: Database (Multi-AZ)
  - ElastiCache Redis: Cache + pub/sub
  - RabbitMQ (AmazonMQ): Message broker
  - S3: Backups
  - CloudWatch: Logs + metrics

Cost: ~$120/month
```

### Docker Compose (Local)
```yaml
services:
  postgres:
    image: postgres:15
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]

  orchestrator:
    build: ./services/orchestrator
    ports: ["8080:8080"]

  discovery:
    build: ./services/discovery

  strategy:
    build: ./services/strategy

  trading:
    build: ./services/trading

  risk:
    build: ./services/risk

  monitoring:
    build: ./services/monitoring
    ports: ["9090:9090", "3000:3000"]

  websocket:
    build: ./services/websocket

  relayer:
    build: ./services/relayer

  data:
    build: ./services/data
```

---

## 📊 Monitoring & Observability

### Grafana Dashboards

**1. Trading Overview:**
- Orders placed/filled/cancelled (24h)
- Win rate (%)
- Daily P&L
- Open positions value

**2. System Health:**
- Service uptime
- API error rate
- WebSocket status
- Heartbeat status

**3. Risk Metrics:**
- Current exposure
- Circuit breaker status
- Max drawdown
- Sharpe ratio

**4. Performance:**
- Order fill latency (p50, p95, p99)
- API response times
- Database query performance

---

## 🔐 Security

### Secrets Management
```
AWS Secrets Manager:
  - PRIVATE_KEY (wallet)
  - API_KEY/SECRET/PASSPHRASE (CLOB L2)
  - TELEGRAM_BOT_TOKEN
  - DATABASE_PASSWORD

Rotation:
  - API keys: 90 days
  - DB password: 180 days
  - Wallet: NEVER (blockchain identity)
```

### Network Security
```yaml
VPC:
  - Private subnets (all services)
  - NAT Gateway (outbound only)
  - Security Groups (whitelist ports)
  - No SSH (use Systems Manager)

Encryption:
  - At rest: RDS + S3 encryption
  - In transit: TLS 1.3
  - Internal: mTLS (optional)
```

---

## 📝 Development Roadmap

### Phase 1: Foundation (Week 1-2)
```
✅ Define schemas
✅ Setup Docker Compose
✅ Data Persistence Service
✅ Discovery Service (read-only)
```

### Phase 2: Core Logic (Week 3-4)
```
✅ Strategy Service
✅ Risk Management Service
✅ Connect to Weather Tracker
```

### Phase 3: Trading (Week 5-6)
```
✅ Trading Service (auth + orders)
✅ Heartbeat mechanism
✅ Retry logic
✅ Paper trading mode
```

### Phase 4: Real-Time (Week 7)
```
✅ WebSocket Service
✅ Market + User channels
✅ Redis Streams integration
```

### Phase 5: On-Chain (Week 8)
```
✅ Relayer Service
✅ Split/merge/redeem
✅ Negative risk handling
```

### Phase 6: Observability (Week 9)
```
✅ Monitoring Service
✅ Prometheus + Grafana
✅ Telegram alerts
```

### Phase 7: Orchestration (Week 10)
```
✅ Orchestrator
✅ Service discovery
✅ Workflow engine
```

### Phase 8: Testing (Week 11-12)
```
✅ E2E tests
✅ Load testing
✅ Paper trading (30 days)
```

### Phase 9: Deployment (Week 13)
```
✅ Terraform IaC
✅ CI/CD pipelines
✅ Production deployment
```

### Phase 10: Live Trading (Week 14+)
```
✅ Live with $50-100 capital
✅ Manual oversight (first 10 trades)
✅ Scale if profitable
```

**Total Timeline: ~14 weeks to live trading**

---

## ⚠️ Risks & Mitigation

### 1. Geographic Restriction
```
Risk: Poland "close-only" status
Mitigation: Deploy to AWS us-east-1
Status: ✅ Addressed
```

### 2. Heartbeat Failure
```
Risk: Auto-cancel all orders
Mitigation: Redundant heartbeat + alerts
Status: ✅ Designed
```

### 3. Matching Engine Restart
```
Risk: HTTP 425 on Tuesdays 7 AM ET
Mitigation: Detect + retry with backoff
Status: ✅ Designed
```

### 4. Tick Size Change
```
Risk: Order rejected if tick changes
Mitigation: WebSocket subscription + auto-update
Status: ✅ Designed
```

### 5. Rate Limits
```
Risk: HTTP 429 rate limit
Mitigation: Use 80% of limit + backoff
Status: ✅ Designed
```

---

## 💰 Cost Estimate

### AWS Infrastructure
```
ECS Fargate (9 services):    $25/mo
RDS PostgreSQL:              $30/mo
ElastiCache Redis:           $15/mo
NAT Gateway:                 $35/mo
Data Transfer:               $10/mo
CloudWatch:                  $5/mo

Total: ~$120/month
```

### Development
```
Timeline: 14 weeks
Effort: 20 hours/week
Total: 280 hours
```

---

## 📚 Documentation Structure

```
docs/
├── architecture/
│   ├── overview.md (this file)
│   ├── service-discovery.md
│   ├── orchestration.md
│   └── security.md
│
├── services/
│   ├── discovery-service.md
│   ├── strategy-service.md
│   ├── trading-service.md
│   ├── risk-management-service.md
│   ├── monitoring-service.md
│   ├── websocket-service.md
│   ├── relayer-service.md
│   ├── data-persistence-service.md
│   └── orchestrator.md
│
├── api/
│   ├── polymarket-gamma-api.md
│   ├── polymarket-clob-api.md
│   ├── polymarket-data-api.md
│   └── internal-grpc-api.md
│
└── operations/
    ├── deployment-guide.md
    ├── monitoring-guide.md
    ├── troubleshooting.md
    └── runbooks/
        ├── heartbeat-failure.md
        ├── circuit-breaker-tripped.md
        └── websocket-disconnect.md
```

---

## ✅ Key Decisions Summary

### Architecture
```
✅ 9 microservices (independent development)
✅ gRPC for sync, Redis Streams for async
✅ PostgreSQL as single source of truth
✅ Docker + ECS Fargate deployment
```

### Security
```
✅ Host outside Poland (AWS us-east-1)
✅ Secrets Manager for credentials
✅ VPC private subnets + NAT
✅ mTLS between services (optional)
```

### Trading
```
✅ Heartbeat every 60s (critical!)
✅ Retry logic (425, 429)
✅ Tick size monitoring (WebSocket)
✅ Pre-trade risk checks
✅ Circuit breakers
```

### Monitoring
```
✅ Prometheus + Grafana
✅ Telegram alerts
✅ Health checks all services
✅ Real-time P&L tracking
```

### Phasing
```
Phase 1-2: Foundation (4 weeks)
Phase 3-6: Core trading (6 weeks)
Phase 7-8: Orchestration + testing (3 weeks)
Phase 9-10: Deployment + live (1 week)

Total: 14 weeks to live trading
```

---

## 🎯 Next Steps

1. **Review & Approve** this architecture plan
2. **Setup GitHub repo** structure for all 9 services
3. **Create Docker Compose** local environment
4. **Start Phase 1** (Data Persistence + Discovery)

---

**Status:** ✅ Architecture planning complete  
**Ready for:** Implementation kickoff  
**Estimated completion:** ~14 weeks to live trading

**Questions? Ready to start coding?** 🚀
