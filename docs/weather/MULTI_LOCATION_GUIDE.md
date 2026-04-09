# Multi-Location Support - Quick Implementation Guide

If you find active Polymarket markets for Berlin/Paris, here's how to add them (2-3 hours):

## Step 1: Update Configuration (5 min)

```python
# In weather_tracker.py, replace single location with:

LOCATIONS = {
    'warsaw': {
        'name': 'Warsaw',
        'country': 'Poland',
        'lat': 52.2297,
        'lon': 21.0122,
        'models_priority': ['icon_eu', 'ecmwf_ifs025']  # Best for Poland
    },
    'berlin': {
        'name': 'Berlin',
        'country': 'Germany',
        'lat': 52.52,
        'lon': 13.405,
        'models_priority': ['icon_eu', 'ecmwf_ifs025']  # Native German models
    },
    'paris': {
        'name': 'Paris',
        'country': 'France',
        'lat': 48.8566,
        'lon': 2.3522,
        'models_priority': ['meteofrance_seamless', 'ecmwf_ifs025']  # Native French
    }
}
```

## Step 2: Update Database Schema (30 min)

```sql
ALTER TABLE forecasts ADD COLUMN location TEXT NOT NULL DEFAULT 'warsaw';
ALTER TABLE observations ADD COLUMN location TEXT NOT NULL DEFAULT 'warsaw';
ALTER TABLE model_bias ADD COLUMN location TEXT NOT NULL DEFAULT 'warsaw';

-- Update indexes
CREATE INDEX idx_forecasts_location_date ON forecasts(location, target_date);
CREATE INDEX idx_observations_location_date ON observations(location, date);
```

## Step 3: Update Collection Loop (15 min)

```python
def collect_all_forecasts():
    for location_key, location_data in LOCATIONS.items():
        print(f"\n🌍 Collecting for {location_data['name']}...")
        collect_forecasts(
            location=location_key,
            lat=location_data['lat'],
            lon=location_data['lon']
        )
```

## Step 4: Update Dashboard (1 hour)

```python
# Add location selector in sidebar
location = st.sidebar.selectbox(
    "Location",
    options=list(LOCATIONS.keys()),
    format_func=lambda x: LOCATIONS[x]['name']
)

# Use selected location in queries
query = f"""
SELECT * FROM forecasts 
WHERE location = '{location}' 
AND target_date = ?
"""
```

## Step 5: Test (30 min)

```bash
# Run for each location
./weather_tracker.py forecast --location=warsaw
./weather_tracker.py forecast --location=berlin
./weather_tracker.py forecast --location=paris

# Check dashboard shows all locations
```

---

## Total Time: ~2-3 hours

**Benefits:**
- Leverage EXISTING models (ICON-EU for Germany, Meteo France for France)
- No new API calls needed
- Dashboard automatically supports all locations
- Easy to add more cities later

**No downsides:**
- Same models, different coordinates
- Minimal code changes
- Same infrastructure

---

## When to Implement

**ONLY AFTER:**
1. ✅ Verified active Polymarket markets exist
2. ✅ Confirmed market liquidity (>$10k volume)
3. ✅ Confirmed betting frequency (daily markets)

**Don't implement if:**
- Markets don't exist
- Markets are illiquid
- Markets are infrequent (monthly)

---

**Conclusion:** Multi-location is EASY to add. But check market availability first!
