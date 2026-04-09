# Architecture Guidelines

This document defines architectural rules for the Weather Forecast Tracker codebase.
**Every agent or contributor MUST read this file before making changes.**

---

## 1. Single Source of Truth for Configuration

All shared configuration MUST live in one place. Do NOT duplicate constants across files.

### Locations
`LOCATIONS` dict is currently defined in both `weather_tracker.py` and `dashboard.py`.
**Rule**: Extract to a shared `config.py` module. All files import from there.

```python
# config.py
LOCATIONS = {
    "warsaw": {"lat": 52.23, "lon": 21.01, "name": "Warsaw", ...},
    ...
}
MODELS = ["ecmwf", "icon", "gfs", "meteofrance", "gem"]
DB_PATH = os.path.join(os.path.dirname(__file__), "weather_forecasts.db")
```

### Database Path
Never use `sqlite3.connect('weather_forecasts.db')` with a bare relative path.
**Rule**: Always use `config.DB_PATH` (based on `__file__`) so the app works regardless of cwd.

### Models List
Model names appear in multiple files. Keep the canonical list in `config.py`.

---

## 2. Database Rules

### Indexes
The database MUST have indexes on frequently queried columns. Add these in `init_db()`:

```python
c.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_target ON forecasts(target_date, location)')
c.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_model ON forecasts(model, forecast_time)')
c.execute('CREATE INDEX IF NOT EXISTS idx_observations_date ON observations(date, location)')
c.execute('CREATE INDEX IF NOT EXISTS idx_bias_date ON model_bias(date, hours_ahead)')
```

Without indexes, dashboard queries degrade exponentially as data grows.

### Transactions
Wrap related writes in a transaction. Do not commit after every single INSERT.

### Connection Management
Avoid opening a new `sqlite3.connect()` in every function. Prefer passing a connection object or using a module-level helper.

---

## 3. Code Reuse — Do Not Duplicate Logic

### API Fetch + Retry
There is a `retry_with_backoff()` helper. Use it for ALL external API calls.
Do NOT write inline retry loops elsewhere.

### Saving Forecasts
The INSERT INTO forecasts logic appears 5+ times in `weather_tracker.py`.
**Rule**: Extract to a `save_forecast(conn, model, target_date, temp_max, ...)` function.

### Saving Observations
The INSERT INTO observations logic is inline in `collect_observation()`.
**Rule**: Extract to a `save_observation(conn, date, temp_max, location)` function and export it — `backfill.py` needs to import it.

> **Known bug**: `backfill.py` imports `save_observation` from `weather_tracker`, but this function does not exist yet. It MUST be created.

---

## 4. Dashboard Performance

### Caching
Streamlit queries MUST use `@st.cache_data(ttl=300)` to avoid re-running SQL on every interaction.

### Query Timeouts
Set `PRAGMA busy_timeout=5000` on SQLite connections in the dashboard.

---

## 5. Error Handling

### API Responses
Always validate before accessing list elements:

```python
temps = data.get('daily', {}).get('temperature_2m_max', [])
if not temps or temps[0] is None:
    raise ValueError(f"No valid data for {target_date}")
```

### Retry Strategy
Retry on transient errors (429, 502, 503, 504, timeouts). Do NOT retry on 400/401.

---

## 6. Infrastructure — Reduce Duplication

- Consolidate the 5 deploy scripts into ONE parametrized script: `./deploy.sh --region eu-west-1 --mode local|remote`
- Consolidate the 3 CloudFormation templates into ONE with parameters for region differences.

---

## 7. File Organization

- `scrapers_polish.py` and `scrapers_playwright.py` are not imported anywhere. Either integrate them or move to `experimental/`.
- `MULTI_LOCATION_GUIDE.md` and `MULTILOCATION_DEPLOYMENT.md` overlap — merge into one.
- Before creating new .md files, check if content fits in an existing doc.

---

## 8. Security

- NEVER commit real AWS resource IDs (VPC, subnet, instance IDs) to the repo.
- Use environment variables or `.env` (gitignored) for infrastructure identifiers.

---

## Implementation Checklist

### Critical Fixes (MUST do immediately):
- [x] Create this ARCHITECTURE.md file
- [ ] Create `config.py` with shared LOCATIONS, MODELS, and DB_PATH
- [ ] Create `save_observation()` function in weather_tracker.py and export it
- [ ] Create `save_forecast()` function in weather_tracker.py
- [ ] Add database indexes in `init_db()`
- [ ] Add `@st.cache_data(ttl=300)` to dashboard queries
- [ ] Add `PRAGMA busy_timeout=5000` to dashboard DB connection

### Medium Priority (within 1 week):
- [ ] Refactor all files to use `config.py`
- [ ] Extract retry logic to reusable functions
- [ ] Add transaction support for batch inserts

### Low Priority (nice to have):
- [ ] Consolidate deploy scripts
- [ ] Merge overlapping documentation
- [ ] Move experimental scrapers to `experimental/` directory

---

**Created:** 2026-04-09  
**Last Updated:** 2026-04-09  
**Maintainer:** Claw Dev Agent
