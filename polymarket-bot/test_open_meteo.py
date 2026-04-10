#!/usr/bin/env python3
"""Quick test of Open-Meteo API integration."""

import sys
from datetime import date, timedelta
from bot.connectors.open_meteo import fetch_forecast, fetch_ensemble_forecast

# Test city: Warsaw
LAT = 52.2297
LON = 21.0122
CITY = "Warsaw"

# Test date: tomorrow
TARGET_DATE = date.today() + timedelta(days=1)

print(f"🧪 Testing Open-Meteo API for {CITY}")
print(f"📍 Coordinates: {LAT}°N, {LON}°E")
print(f"📅 Target date: {TARGET_DATE}")
print("="*60)

# Test 1: Single model (ECMWF)
print("\n1️⃣ Testing single model fetch (ECMWF IFS)...")
try:
    result = fetch_forecast(LAT, LON, TARGET_DATE, "ecmwf_ifs025")
    if result:
        print(f"✅ SUCCESS!")
        print(f"   Temp max: {result['temp_max_c']:.1f}°C / {result['temp_max_f']:.1f}°F")
        print(f"   Model: {result['model']}")
        print(f"   Confidence: {result['confidence']}")
    else:
        print("❌ FAIL: No data returned")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 2: Ensemble (all 5 models)
print("\n2️⃣ Testing ensemble fetch (5 models)...")
try:
    result = fetch_ensemble_forecast(LAT, LON, TARGET_DATE)
    if result:
        print(f"✅ SUCCESS!")
        print(f"   Ensemble temp: {result['temp_max_c']:.1f}°C / {result['temp_max_f']:.1f}°F")
        print(f"   Model count: {result['model_count']}")
        print(f"   Model spread: {result['model_spread_f']:.1f}°F")
        print(f"   Ensemble sigma: {result['ensemble_sigma_f']:.1f}°F")
        print(f"\n   Individual models:")
        for fc in result['individual_forecasts']:
            print(f"     - {fc['model']}: {fc['temp_max_f']:.1f}°F (weight: {fc['weight']})")
    else:
        print("❌ FAIL: No ensemble data returned")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 3: Dynamic sigma calculation
print("\n3️⃣ Testing dynamic sigma calculation...")
spread = result['model_spread_f']
base_sigma = 4.0
dynamic_sigma = base_sigma + (spread / 2.0)
print(f"   Base sigma: {base_sigma}°F")
print(f"   Model spread: {spread:.1f}°F")
print(f"   Dynamic sigma: {dynamic_sigma:.1f}°F")
if spread < 3.0:
    print("   ✅ Low spread → models agree → high confidence")
elif spread < 6.0:
    print("   ⚠️  Medium spread → moderate uncertainty")
else:
    print("   ❌ High spread → models disagree → low confidence")

print("\n" + "="*60)
print("🎉 All tests PASSED!")
print("\nNext: Test weather connector (with tracker fallback)")
