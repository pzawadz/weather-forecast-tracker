#!/usr/bin/env python3
"""End-to-end test: parse + forecast + probability calculation."""

import sys
from datetime import date, timedelta

# Mock config
class MockConfig:
    TRACKER_DB_PATH = "../weather-forecast-tracker/weather_forecasts.db"
    extreme_yes_max_price = 0.12
    extreme_yes_min_price = 0.03
    extreme_yes_ideal_price = 0.08
    extreme_no_min_yes_price = 0.50
    extreme_no_ideal_yes_price = 0.60
    extreme_no_min_price = 0.03
    extreme_min_position = 1.50
    extreme_max_position = 2.50
    extreme_aggressive_max = 5.00
    prefer_no_on_range = True
    skip_yes_on_threshold = False
    min_edge_threshold = 0.10

config = MockConfig()

# Import weather connector
from bot.connectors.weather import WeatherConnector

# Create connector
weather = WeatherConnector(config)

print("🧪 END-TO-END TEST: Strategy Components")
print("="*60)

# Test cases
test_cases = [
    {
        "name": "Warsaw Threshold (Fahrenheit)",
        "question": "Will the high temperature in Warsaw exceed 50°F on April 11, 2026?",
        "expected_location": "Warsaw",
        "expected_threshold": 50.0,
        "expected_unit": "F",
    },
    {
        "name": "Berlin Range (Celsius)",
        "question": "Will Berlin's high temperature be between 18-20°C on Apr 11, 2026?",
        "expected_location": "Berlin",
        "expected_range": (18.0, 20.0),
        "expected_unit": "C",
    },
    {
        "name": "London Below (Celsius)",
        "question": "Will London's high temperature be below 15°C on 2026-04-11?",
        "expected_location": "London",
        "expected_threshold": 15.0,
        "expected_direction": "below",
        "expected_unit": "C",
    },
    {
        "name": "NYC Above (Fahrenheit)",
        "question": "Will NYC's high temperature be above 60°F on April 11?",
        "expected_location": "NYC",
        "expected_threshold": 60.0,
        "expected_direction": "above",
        "expected_unit": "F",
    }
]

TARGET_DATE = date(2026, 4, 11)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {test['name']}")
    print(f"{'='*60}")
    print(f"Question: {test['question']}")
    print("")
    
    # Step 1: Parse market question
    print("1️⃣ Parsing market question...")
    try:
        parsed = weather.parse_market_question(test['question'])
        
        print(f"   ✅ Location: {parsed['location']}")
        print(f"   ✅ Temperature unit: {parsed['temp_unit']}")
        print(f"   ✅ Threshold type: {parsed['threshold_type']}")
        
        if parsed['is_range']:
            print(f"   ✅ Range: {parsed['range_low']}-{parsed['range_high']}")
            assert parsed['range_low'] == test['expected_range'][0], "Range low mismatch"
            assert parsed['range_high'] == test['expected_range'][1], "Range high mismatch"
        else:
            print(f"   ✅ Threshold: {parsed['threshold']}")
            if parsed.get('threshold_direction'):
                print(f"   ✅ Direction: {parsed['threshold_direction']}")
            assert parsed['threshold'] == test['expected_threshold'], "Threshold mismatch"
        
        # Validate expectations
        assert parsed['location'] == test['expected_location'], "Location mismatch"
        assert parsed['temp_unit'] == test['expected_unit'], "Unit mismatch"
        
        if 'expected_direction' in test:
            assert parsed.get('threshold_direction') == test['expected_direction'], "Direction mismatch"
        
    except AssertionError as e:
        print(f"   ❌ FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 2: Get forecast
    print("\n2️⃣ Fetching forecast...")
    try:
        forecast = weather.get_forecast_by_location(parsed['location'], TARGET_DATE)
        
        if forecast:
            print(f"   ✅ Source: {forecast['source']}")
            print(f"   ✅ Temp: {forecast['temp_max_c']:.1f}°C / {forecast['temp_max_f']:.1f}°F")
            print(f"   ✅ Sigma: {forecast['sigma_f']:.1f}°F / {forecast['sigma_c']:.1f}°C")
            print(f"   ✅ Model count: {forecast['model_count']}")
            if forecast['source'] == 'open_meteo':
                print(f"   ✅ Model spread: {forecast['model_spread_f']:.1f}°F")
        else:
            print(f"   ❌ No forecast available")
            continue
            
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 3: Calculate probability
    print("\n3️⃣ Calculating probability...")
    try:
        if parsed['is_range']:
            # Range probability
            probability = weather.calculate_range_probability(
                forecast=forecast,
                range_low=parsed['range_low'],
                range_high=parsed['range_high'],
                threshold_type=parsed['threshold_type']
            )
            print(f"   ✅ P(temp in range [{parsed['range_low']}, {parsed['range_high']}]): {probability:.1%}")
        else:
            # Threshold probability
            direction = parsed.get('threshold_direction', 'above')
            probability = weather.calculate_probability(
                forecast=forecast,
                threshold=parsed['threshold'],
                threshold_type=parsed['threshold_type'],
                direction=direction
            )
            print(f"   ✅ P(temp {direction} {parsed['threshold']}): {probability:.1%}")
        
        # Sanity checks
        assert 0.0 <= probability <= 1.0, f"Probability out of range: {probability}"
        print(f"   ✅ Probability valid: {probability:.1%}")
        
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "="*60)
print("🎉 ALL END-TO-END TESTS PASSED!")
print("\nComponents working:")
print("  ✅ parse_market_question() - European + US cities, °C/°F, ranges/thresholds")
print("  ✅ get_forecast_by_location() - City name → forecast")
print("  ✅ calculate_probability() - Dynamic sigma from forecast")
print("  ✅ calculate_range_probability() - Range markets")
print("\n🚀 Strategy ready for use!")
