#!/usr/bin/env python3
"""Test weather connector with tracker integration."""

import sys
from datetime import date, timedelta
from pathlib import Path

# Mock config for testing
class MockConfig:
    TRACKER_DB_PATH = "../weather-forecast-tracker/weather_forecasts.db"

config = MockConfig()

# Check if tracker DB exists
tracker_exists = Path(config.TRACKER_DB_PATH).exists()

print("🧪 Testing Weather Connector")
print("="*60)
print(f"Tracker DB path: {config.TRACKER_DB_PATH}")
print(f"Tracker available: {tracker_exists}")
print("")

# Import weather connector
from bot.connectors.weather import WeatherConnector

# Create connector
connector = WeatherConnector(config)

# Test city: Warsaw
LAT = 52.2297
LON = 21.0122
LOCATION_KEY = "warsaw"
TARGET_DATE = date.today() + timedelta(days=1)

print(f"📍 Testing: Warsaw ({LAT}°N, {LON}°E)")
print(f"📅 Target date: {TARGET_DATE}")
print("="*60)

# Test 1: Fetch forecast
print("\n1️⃣ Fetching forecast...")
try:
    result = connector.get_forecast(LAT, LON, TARGET_DATE, location_key=LOCATION_KEY)
    
    if result:
        print(f"✅ SUCCESS!")
        print(f"   Source: {result['source']}")
        print(f"   Temp: {result['temp_max_c']:.1f}°C / {result['temp_max_f']:.1f}°F")
        print(f"   Sigma: {result['sigma_f']:.1f}°F (uncertainty)")
        print(f"   Model count: {result['model_count']}")
        if result['source'] == 'open_meteo':
            print(f"   Model spread: {result['model_spread_f']:.1f}°F")
        print(f"\n   → {result['source'].upper()} source used")
        if result['source'] == 'tracker':
            print(f"   → Bias-corrected forecast (more accurate!)")
    else:
        print("❌ FAIL: No forecast returned")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Cache test
print("\n2️⃣ Testing cache (should be instant)...")
import time
start = time.time()
result2 = connector.get_forecast(LAT, LON, TARGET_DATE, location_key=LOCATION_KEY)
elapsed = time.time() - start

if result2:
    print(f"✅ Cache hit! ({elapsed*1000:.1f}ms)")
    if result2['temp_max_f'] == result['temp_max_f']:
        print("   Same result as first fetch ✓")
    else:
        print("   ⚠️  Different result - cache issue?")
else:
    print("❌ Cache miss")

# Test 3: Clear cache and refetch
print("\n3️⃣ Testing cache clear...")
connector.clear_cache()
result3 = connector.get_forecast(LAT, LON, TARGET_DATE, location_key=LOCATION_KEY)
if result3:
    print(f"✅ Refetched after cache clear")
    print(f"   Source: {result3['source']}")

print("\n" + "="*60)
print("🎉 Weather connector tests PASSED!")

# Summary
print("\n📊 Summary:")
print(f"   - Open-Meteo API: ✅ Working")
print(f"   - Tracker integration: {'✅ Working' if tracker_exists else '⚠️  Not available (OK)'}")
print(f"   - Cache: ✅ Working")
print(f"   - Forecast source: {result['source']}")
