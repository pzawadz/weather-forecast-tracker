#!/usr/bin/env python3
"""
Weather Forecast Tracker for Warsaw
Collects forecasts every 4h, compares with actual observations
"""

import sqlite3
import requests
from datetime import datetime, timedelta
import json
import statistics

# Warsaw coordinates
LAT = 52.2297
LON = 21.0122

# Open-Meteo API endpoints
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Models available in Open-Meteo
MODELS = [
    "ecmwf_ifs025",          # ECMWF IFS 0.25° (best global)
    "icon_eu",               # ICON-EU 0.0625° (7km, excellent for Poland) 🇵🇱
    "gfs_global",            # GFS Global
    "icon_global",           # ICON Global
    "meteofrance_seamless",  # Meteo France
    "gem_global",            # GEM Global
]


def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    # Forecasts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            forecast_time TIMESTAMP NOT NULL,
            target_date DATE NOT NULL,
            hours_ahead INTEGER NOT NULL,
            temp_max REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Actual observations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            temp_max REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Model bias tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS model_bias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            date DATE NOT NULL,
            bias REAL NOT NULL,
            hours_ahead INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(model, date, hours_ahead)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")


def fetch_forecast(model, target_date):
    """Fetch tomorrow's max temp forecast from a specific model"""
    try:
        params = {
            'latitude': LAT,
            'longitude': LON,
            'daily': 'temperature_2m_max',
            'timezone': 'Europe/Warsaw',
            'start_date': target_date.strftime('%Y-%m-%d'),
            'end_date': target_date.strftime('%Y-%m-%d'),
            'models': model,
        }
        
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'daily' in data and 'temperature_2m_max' in data['daily']:
            temp_max = data['daily']['temperature_2m_max'][0]
            return temp_max
        else:
            print(f"⚠️  {model}: No data for {target_date}")
            return None
            
    except Exception as e:
        print(f"❌ {model}: {e}")
        return None


def fetch_actual_temp(date):
    """Fetch actual observed max temp for a given date"""
    try:
        params = {
            'latitude': LAT,
            'longitude': LON,
            'start_date': date.strftime('%Y-%m-%d'),
            'end_date': date.strftime('%Y-%m-%d'),
            'daily': 'temperature_2m_max',
            'timezone': 'Europe/Warsaw',
        }
        
        response = requests.get(HISTORICAL_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'daily' in data and 'temperature_2m_max' in data['daily']:
            temp_max = data['daily']['temperature_2m_max'][0]
            return temp_max
        else:
            print(f"⚠️  No observation data for {date}")
            return None
            
    except Exception as e:
        print(f"❌ Observation fetch error: {e}")
        return None


def save_forecast(model, forecast_time, target_date, hours_ahead, temp_max):
    """Save forecast to database"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max)
        VALUES (?, ?, ?, ?, ?)
    ''', (model, forecast_time, target_date, hours_ahead, temp_max))
    
    conn.commit()
    conn.close()


def save_observation(date, temp_max):
    """Save actual observation to database"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO observations (date, temp_max)
        VALUES (?, ?)
    ''', (date, temp_max))
    
    conn.commit()
    conn.close()
    print(f"✓ Saved observation: {date} → {temp_max}°C")


def get_model_bias(model, days_back=7):
    """Get average bias for a model over last N days"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT AVG(bias) 
        FROM model_bias
        WHERE model = ? 
          AND date >= date('now', '-' || ? || ' days')
          AND hours_ahead BETWEEN 20 AND 28
    ''', (model, days_back))
    
    row = c.fetchone()
    conn.close()
    
    return row[0] if row and row[0] is not None else 0.0


def collect_forecasts():
    """Collect forecasts from all models for tomorrow with bias correction"""
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    hours_until_tomorrow = (datetime.combine(tomorrow, datetime.min.time()) - now).total_seconds() / 3600
    
    print(f"\n📊 Collecting forecasts for {tomorrow} ({hours_until_tomorrow:.1f}h ahead)")
    print(f"   Forecast time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    forecasts_raw = []
    forecasts_corrected = []
    
    for model in MODELS:
        temp_max = fetch_forecast(model, tomorrow)
        if temp_max is not None:
            # Save raw forecast
            save_forecast(model, now, tomorrow, int(hours_until_tomorrow), temp_max)
            forecasts_raw.append(temp_max)
            
            # Apply bias correction
            bias = get_model_bias(model, days_back=7)
            temp_corrected = temp_max - bias
            forecasts_corrected.append(temp_corrected)
            
            print(f"   ✓ {model:25s} → {temp_max:5.1f}°C (bias: {bias:+.2f}°C, corrected: {temp_corrected:5.1f}°C)")
    
    if forecasts_raw:
        # Raw ensemble
        median_raw = statistics.median(forecasts_raw)
        mean_raw = statistics.mean(forecasts_raw)
        
        # Bias-corrected ensemble
        median_corrected = statistics.median(forecasts_corrected)
        mean_corrected = statistics.mean(forecasts_corrected)
        std_dev = statistics.stdev(forecasts_corrected) if len(forecasts_corrected) > 1 else 0.0
        
        print(f"\n   📈 Raw ensemble: median={median_raw:.1f}°C, mean={mean_raw:.1f}°C")
        print(f"   🎯 Bias-corrected: median={median_corrected:.1f}°C, mean={mean_corrected:.1f}°C, σ={std_dev:.1f}°C")
        
        # Save both versions
        save_forecast("ENSEMBLE_MEDIAN", now, tomorrow, int(hours_until_tomorrow), median_raw)
        save_forecast("ENSEMBLE_MEAN", now, tomorrow, int(hours_until_tomorrow), mean_raw)
        save_forecast("ENSEMBLE_CORRECTED", now, tomorrow, int(hours_until_tomorrow), median_corrected)
        
        # Betting recommendation
        confidence = "HIGH" if std_dev < 1.0 else "MEDIUM" if std_dev < 2.0 else "LOW"
        print(f"\n   💰 BETTING: {median_corrected:.1f}°C (confidence: {confidence}, spread: ±{std_dev:.1f}°C)")
    
    return len(forecasts_raw)


def collect_observation():
    """Collect actual observation for yesterday"""
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    print(f"\n🌡️  Fetching observation for {yesterday}")
    temp_max = fetch_actual_temp(yesterday)
    
    if temp_max is not None:
        save_observation(yesterday, temp_max)
        calculate_errors(yesterday)


def calculate_errors(date):
    """Calculate forecast errors for a given date"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    # Get actual observation
    c.execute('SELECT temp_max FROM observations WHERE date = ?', (date,))
    row = c.fetchone()
    if not row:
        print(f"⚠️  No observation for {date}")
        conn.close()
        return
    
    actual = row[0]
    
    # Get all forecasts for this date
    c.execute('''
        SELECT model, hours_ahead, temp_max
        FROM forecasts
        WHERE target_date = ?
        ORDER BY hours_ahead DESC, model
    ''', (date,))
    
    print(f"\n📉 Errors for {date} (actual: {actual:.1f}°C)")
    
    for model, hours_ahead, forecast in c.fetchall():
        error = forecast - actual
        c.execute('''
            INSERT OR REPLACE INTO model_bias (model, date, bias, hours_ahead)
            VALUES (?, ?, ?, ?)
        ''', (model, date, error, hours_ahead))
        
        print(f"   {hours_ahead:3d}h {model:25s} {forecast:5.1f}°C → error: {error:+5.1f}°C")
    
    conn.commit()
    conn.close()


def show_statistics(days=7):
    """Show model performance statistics"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    print(f"\n📊 Model Performance (last {days} days, 24h forecasts)")
    print("="*70)
    
    c.execute('''
        SELECT 
            model,
            COUNT(*) as count,
            AVG(bias) as mean_error,
            AVG(ABS(bias)) as mae,
            SQRT(AVG(bias * bias)) as rmse
        FROM model_bias
        WHERE date >= date('now', '-' || ? || ' days')
          AND hours_ahead BETWEEN 20 AND 28
        GROUP BY model
        ORDER BY mae ASC
    ''', (days,))
    
    print(f"{'Model':<25} {'Count':>6} {'Mean Error':>12} {'MAE':>8} {'RMSE':>8}")
    print("-"*70)
    
    for model, count, mean_error, mae, rmse in c.fetchall():
        print(f"{model:<25} {count:>6} {mean_error:>+11.2f}°C {mae:>7.2f}° {rmse:>7.2f}°")
    
    conn.close()


def main():
    """Main entry point"""
    import sys
    
    init_db()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "forecast":
            count = collect_forecasts()
            print(f"\n✅ Collected {count} forecasts")
        
        elif command == "observe":
            collect_observation()
        
        elif command == "stats":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            show_statistics(days)
        
        elif command == "both":
            # Typical daily run: collect observation for yesterday, forecast for tomorrow
            collect_observation()
            collect_forecasts()
        
        else:
            print("Usage: weather_tracker.py [forecast|observe|both|stats]")
            sys.exit(1)
    else:
        # Default: both
        collect_observation()
        collect_forecasts()


if __name__ == "__main__":
    main()
