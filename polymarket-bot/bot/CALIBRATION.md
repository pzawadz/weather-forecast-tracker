# Calibration Guide

## Overview

Calibration updates forecast uncertainty (sigma) values based on **actual forecast accuracy**.

The bot initially uses default sigma values from `config/calibration.json`:
- Europe: 2.0°C / 3.5°F (base sigma)
- US: 2.8°C / 5.0°F (base sigma)

After 7+ days of observations, calibration refines these values using **real performance data**.

---

## Requirements

### 1. Weather-forecast-tracker must be running
```bash
# Cron jobs should be active (see parent project)
0 */4 * * * cd /path/to/weather-forecast-tracker && python3 weather_tracker.py forecast-all
0 8,20 * * * cd /path/to/weather-forecast-tracker && python3 weather_tracker.py observe-all
```

### 2. Minimum 7 days of data
```
Day 1: Collect forecast for Day 2
Day 2: Collect observation for Day 2
Day 2: Calculate error (forecast - actual)
...
Day 7: 7 samples available
Day 7: Run calibration ✅
```

### 3. Database location
```
Default: ../weather_forecasts.db (parent project)
Can override: --tracker-db /path/to/weather_forecasts.db
```

---

## Usage

### Basic (recommended)
```bash
cd polymarket-bot
python -m bot.calibrate
```

### Dry run (preview changes)
```bash
python -m bot.calibrate --dry-run
```

### Custom parameters
```bash
python -m bot.calibrate --days 30 --min-samples 10
```

---

## What It Does

### 1. Analyzes Forecast Accuracy
For each location (Warsaw, Paris, Munich, London):
- Reads forecast errors from `model_bias` table
- Filters to 18-30h ahead forecasts (betting window)
- Calculates:
  - MAE (Mean Absolute Error)
  - Bias (systematic over/under-prediction)
  - Std Dev (forecast spread)

### 2. Calculates Optimal Sigma
```python
recommended_sigma = std_dev * 1.2  # 20% safety margin
```

Why?
- Sigma controls probability confidence
- Higher sigma = wider probability distribution = fewer trades
- Lower sigma = tighter distribution = more trades (but risk of overconfidence)
- Safety margin accounts for model spread not captured in individual model errors

### 3. Updates Config
Updates `config/calibration.json`:
```json
{
  "regions": {
    "europe": {
      "base_sigma_c": 2.5,  // Updated from 2.0
      "base_sigma_f": 4.5   // Updated from 3.5
    }
  }
}
```

Keeps history:
```json
{
  "calibration_history": [
    {
      "date": "2026-04-17T10:00:00",
      "locations_calibrated": ["warsaw", "paris", "munich", "london"],
      "europe_sigma_c": 2.5
    }
  ]
}
```

---

## Example Output

```
🔧 Polymarket Bot Calibration
============================================================
Tracker DB: ../weather_forecasts.db
Config: config/calibration.json
Days: 30
Min samples: 7
Dry run: False

📊 Analyzing forecast accuracy...

✅ Analyzed 4 locations:

  WARSAW:
    Samples: 10
    MAE: 1.8°C / 3.2°F
    Bias: -0.3°C / -0.5°F (slightly cold)
    Std Dev: 2.1°C / 3.8°F
    → Recommended sigma: 2.5°C / 4.5°F

  PARIS:
    Samples: 10
    MAE: 2.1°C / 3.8°F
    Bias: 0.2°C / 0.4°F (slightly warm)
    Std Dev: 2.3°C / 4.1°F
    → Recommended sigma: 2.8°C / 5.0°F

  ...

🎯 Regional sigma values:
  Europe: 2.6°C / 4.7°F (avg of Warsaw, Paris, Munich, London)
  US: 3.1°C / 5.6°F (avg of US cities if available)

✅ Config updated: config/calibration.json
   Version: 1.0.0.20260417

🎉 Calibration complete!
```

---

## Frequency

**Recommended:** Weekly

```bash
# Add to cron (Sundays at 9 AM)
0 9 * * 0 cd /path/to/polymarket-bot && source venv/bin/activate && python -m bot.calibrate
```

Why weekly?
- Forecast models don't change daily
- 7 new observations/week provides gradual refinement
- Avoids over-fitting to short-term weather patterns

---

## Troubleshooting

### "No locations with sufficient data for calibration"
```
Solution: Wait for more data
- Need 7+ observations per location
- Check parent project: python3 weather_tracker.py observe-all
- Check DB: SELECT COUNT(*) FROM observations WHERE location='warsaw';
```

### "Tracker DB not found"
```
Solution: Check path
- Default: ../weather_forecasts.db
- Override: python -m bot.calibrate --tracker-db /path/to/db
```

### Sigma values seem wrong
```
Solution: Check your data
1. Run calibration with --dry-run first
2. Review MAE and Std Dev values
3. If too high: check if forecast collection is working
4. If too low: might be lucky week, wait for more samples
```

---

## Impact on Strategy

### Before Calibration (defaults)
```python
# Warsaw forecast
predicted_temp = 10°C
sigma = 2.0°C  # Default for Europe

# Probability calculation
P(temp > 12°C) = 16%  # Based on default sigma
```

### After Calibration (actual = 2.5°C)
```python
# Warsaw forecast
predicted_temp = 10°C
sigma = 2.5°C  # Calibrated from real data

# Probability calculation
P(temp > 12°C) = 21%  # More accurate!
```

Higher sigma = more realistic uncertainty = better probability estimates = better trades.

---

## Advanced: Manual Override

If you want to override sigma without calibration:

```bash
# Edit config/calibration.json manually
nano config/calibration.json

# Change base_sigma_c values
{
  "regions": {
    "europe": {
      "base_sigma_c": 3.0,  // Your custom value
      "base_sigma_f": 5.4
    }
  }
}
```

Bot will use these values until next calibration.

---

**Status:** ⏳ Calibration requires 7+ days of data (currently day 1-2)
**Next:** Run after 2026-04-17 (7 days after tracker launch)
