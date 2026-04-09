# Weather Classification - Simple Temperature-Based

## Classification Logic

Since we only track temperature (not weather codes), we classify days by temperature range:

```python
def classify_weather(temp_c):
    if temp_c < 0:
        return "Freezing", "🥶"
    elif temp_c < 10:
        return "Cold", "🧊"
    elif temp_c < 20:
        return "Cool", "🌤️"
    elif temp_c < 25:
        return "Warm", "☀️"
    else:
        return "Hot", "🔥"
```

## Usage

This simple classification helps identify if forecast accuracy varies by temperature range.

For example:
- "Models struggle with freezing temps (MAE: 1.2°C)"
- "Warm days: very accurate (MAE: 0.3°C)"

## Future Enhancement

To get true weather classification (sunny/rainy/cloudy), we'd need to:
1. Add `weather_code` parameter to forecast API calls
2. Store weather_code in database
3. Map codes to weather types (WMO weather codes 0-99)

**Cost:** No additional API calls (Open-Meteo includes weather_code for free)  
**Effort:** ~2 hours (modify weather_tracker.py + database schema)

---

**Current implementation:** Temperature-based classification (zero changes to data collection)
