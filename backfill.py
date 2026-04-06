#!/usr/bin/env python3
"""
Backfill historical forecasts from Open-Meteo Historical Forecast API
Fills database with past 14 days of forecast data
"""

import sqlite3
import requests
from datetime import datetime, timedelta
import time

LAT = 52.2297
LON = 21.0122

HISTORICAL_FORECAST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

# Models available in Historical Forecast API
MODELS = [
    "ecmwf_ifs04",       # ECMWF IFS 0.4° (available back to 2022)
    "gfs_seamless",      # GFS Seamless
    "icon_seamless",     # ICON Seamless
]


def fetch_historical_forecast(model, forecast_date, target_date):
    """
    Fetch what the model predicted on forecast_date for target_date
    """
    try:
        # Historical Forecast API uses forecast_date as reference
        params = {
            'latitude': LAT,
            'longitude': LON,
            'start_date': forecast_date.strftime('%Y-%m-%d'),
            'end_date': forecast_date.strftime('%Y-%m-%d'),
            'daily': 'temperature_2m_max',
            'timezone': 'Europe/Warsaw',
            'models': model,
        }
        
        response = requests.get(HISTORICAL_FORECAST_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Find target_date in forecast
        if 'daily' in data and 'time' in data['daily'] and 'temperature_2m_max' in data['daily']:
            times = data['daily']['time']
            temps = data['daily']['temperature_2m_max']
            
            target_str = target_date.strftime('%Y-%m-%d')
            if target_str in times:
                idx = times.index(target_str)
                return temps[idx]
            else:
                print(f"⚠️  {model}: {target_str} not in forecast from {forecast_date}")
                return None
        else:
            print(f"⚠️  {model}: No data structure")
            return None
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"⚠️  {model}: Historical forecast not available for {forecast_date}")
        else:
            print(f"❌ {model}: HTTP {e.response.status_code}")
        return None
    except Exception as e:
        print(f"❌ {model}: {e}")
        return None


def save_forecast(model, forecast_time, target_date, hours_ahead, temp_max):
    """Save forecast to database (same as main tracker)"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    # Check if already exists
    c.execute('''
        SELECT id FROM forecasts 
        WHERE model = ? AND forecast_time = ? AND target_date = ?
    ''', (model, forecast_time, target_date))
    
    if c.fetchone():
        print(f"   ⏭️  {model} {forecast_time} → {target_date} already exists")
        conn.close()
        return
    
    c.execute('''
        INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max)
        VALUES (?, ?, ?, ?, ?)
    ''', (model, forecast_time, target_date, hours_ahead, temp_max))
    
    conn.commit()
    conn.close()


def backfill_day(target_date, forecast_hours=[24, 48, 72]):
    """
    Backfill forecasts for a specific target_date
    forecast_hours: list of hours before target_date to simulate forecast times
    """
    print(f"\n📅 Backfilling for target date: {target_date}")
    
    for hours_before in forecast_hours:
        forecast_date = target_date - timedelta(hours=hours_before)
        forecast_time = datetime.combine(forecast_date, datetime.min.time().replace(hour=12))
        
        print(f"\n   ⏰ Forecast from {forecast_date} ({hours_before}h ahead)")
        
        for model in MODELS:
            temp_max = fetch_historical_forecast(model, forecast_date, target_date)
            
            if temp_max is not None:
                save_forecast(model, forecast_time, target_date, hours_before, temp_max)
                print(f"      ✓ {model:25s} → {temp_max:5.1f}°C")
            
            # Rate limiting
            time.sleep(0.5)


def backfill_range(days_back=14):
    """Backfill forecasts for last N days"""
    print(f"\n🔄 Starting backfill for last {days_back} days")
    print(f"   Models: {', '.join(MODELS)}")
    print("="*80)
    
    today = datetime.now().date()
    
    # Backfill from (today - days_back) to yesterday
    for i in range(days_back, 0, -1):
        target_date = today - timedelta(days=i)
        
        # Fetch forecasts from 24h, 48h, 72h before
        backfill_day(target_date, forecast_hours=[24, 48, 72])
        
        # Small delay between days
        time.sleep(1)
    
    print("\n✅ Backfill complete!")


def fetch_observation(date):
    """Fetch actual observation (reuse from main tracker)"""
    from weather_tracker import fetch_actual_temp, save_observation
    temp_max = fetch_actual_temp(date)
    if temp_max:
        save_observation(date, temp_max)
        return temp_max
    return None


def backfill_observations(days_back=14):
    """Backfill actual observations for last N days"""
    print(f"\n🌡️  Backfilling observations for last {days_back} days")
    
    today = datetime.now().date()
    
    for i in range(days_back, 0, -1):
        date = today - timedelta(days=i)
        
        from weather_tracker import fetch_actual_temp, save_observation
        temp_max = fetch_actual_temp(date)
        
        if temp_max:
            save_observation(date, temp_max)
            print(f"   ✓ {date} → {temp_max:.1f}°C")
        
        time.sleep(0.3)
    
    print("\n✅ Observations backfill complete!")


def main():
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "forecasts":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 14
            backfill_range(days)
        
        elif command == "observations":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 14
            backfill_observations(days)
        
        elif command == "all":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 14
            print("\n" + "="*80)
            print("🔄 FULL BACKFILL")
            print("="*80)
            backfill_observations(days)
            backfill_range(days)
        
        else:
            print("Usage: backfill.py [forecasts|observations|all] [days]")
            print("")
            print("Examples:")
            print("  ./backfill.py all            # Backfill last 14 days (forecasts + obs)")
            print("  ./backfill.py forecasts 7    # Backfill forecasts for last 7 days")
            print("  ./backfill.py observations   # Backfill observations only")
            sys.exit(1)
    else:
        # Default: full backfill
        backfill_observations(14)
        backfill_range(14)


if __name__ == "__main__":
    main()
