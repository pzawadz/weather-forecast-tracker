#!/usr/bin/env python3
"""
Weather Forecast Tracker - Multi-Location Support
Collects forecasts every 4h for multiple cities
"""

import sqlite3
import requests
from datetime import datetime, timedelta
import json
import statistics
import time
import concurrent.futures
import argparse

# Location configurations
LOCATIONS = {
    'warsaw': {
        'name': 'Warsaw',
        'country': 'Poland',
        'lat': 52.2297,
        'lon': 21.0122,
        'timezone': 'Europe/Warsaw',
        'models_priority': ['icon_eu', 'ecmwf_ifs025']  # Best for Poland
    },
    'paris': {
        'name': 'Paris',
        'country': 'France',
        'lat': 48.8566,
        'lon': 2.3522,
        'timezone': 'Europe/Paris',
        'models_priority': ['meteofrance_seamless', 'ecmwf_ifs025']  # Native French
    },
    'munich': {
        'name': 'Munich',
        'country': 'Germany',
        'lat': 48.1351,
        'lon': 11.5820,
        'timezone': 'Europe/Berlin',
        'models_priority': ['icon_eu', 'ecmwf_ifs025']  # Native German (ICON-EU)
    },
    'london': {
        'name': 'London',
        'country': 'UK',
        'lat': 51.5074,
        'lon': -0.1278,
        'timezone': 'Europe/London',
        'models_priority': ['ecmwf_ifs025', 'icon_eu']  # ECMWF good for UK
    }
}

# Open-Meteo API endpoints
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Models available in Open-Meteo
MODELS = [
    "ecmwf_ifs025",          # ECMWF IFS 0.25° (best global)
    "icon_eu",               # ICON-EU 0.0625° (7km, excellent for Central Europe)
    "gfs_global",            # GFS Global
    "icon_global",           # ICON Global
    "meteofrance_seamless",  # Meteo France (best for France)
    "gem_global",            # GEM Global
]

# IMGW API configuration (Polish native model)
IMGW_API_URL = "https://meteo.imgw.pl/api/v1/forecast/fcapi"
IMGW_TOKEN = "p4DXKjsYadfBV21TYrDk"

# Location-specific models (IMGW only works for Poland)
LOCATION_SPECIFIC_MODELS = {
    'warsaw': ['imgw_hybrid'],  # Polish HYBRID model (UM + AROME 2.5-4km)
    'paris': [],
    'munich': [],
    'london': []
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # seconds (exponential backoff)


def retry_with_backoff(func, *args, max_retries=MAX_RETRIES, delays=RETRY_DELAYS, **kwargs):
    """
    Retry a function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of attempts
        delays: List of delays between retries (seconds)
    
    Returns:
        Result of func or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise
            else:
                delay = delays[attempt] if attempt < len(delays) else delays[-1]
                print(f"      Retry {attempt + 1}/{max_retries} after {delay}s...")
                time.sleep(delay)
    
    return None


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
            location TEXT NOT NULL DEFAULT 'warsaw',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Actual observations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            temp_max REAL NOT NULL,
            location TEXT NOT NULL DEFAULT 'warsaw',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, location)
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
            location TEXT NOT NULL DEFAULT 'warsaw',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(model, date, hours_ahead, location)
        )
    ''')
    
    # Performance indexes (critical for dashboard queries)
    print("✓ Creating indexes...")
    c.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_target ON forecasts(target_date, location)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_model ON forecasts(model, forecast_time)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_forecasts_location ON forecasts(location, target_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_observations_date ON observations(date, location)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_bias_date ON model_bias(date, hours_ahead)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_bias_model ON model_bias(model, location, date)')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized with indexes")


def _fetch_forecast_single(model, target_date, location_key):
    """Single attempt to fetch forecast (used by retry wrapper)"""
    location = LOCATIONS[location_key]
    params = {
        'latitude': location['lat'],
        'longitude': location['lon'],
        'daily': 'temperature_2m_max',
        'timezone': location['timezone'],
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
        raise ValueError(f"No data returned for {target_date}")


def fetch_forecast(model, target_date, location_key='warsaw'):
    """Fetch tomorrow's max temp forecast from a specific model (with retry)"""
    try:
        temp_max = retry_with_backoff(_fetch_forecast_single, model, target_date, location_key)
        return temp_max
    except Exception as e:
        error_msg = str(e)
        # Shorten long error messages
        if len(error_msg) > 100:
            error_msg = error_msg[:97] + "..."
        print(f"❌ {model}: {error_msg}")
        return None


def _fetch_actual_temp_single(date, location_key):
    """Single attempt to fetch actual temperature (used by retry wrapper)"""
    location = LOCATIONS[location_key]
    params = {
        'latitude': location['lat'],
        'longitude': location['lon'],
        'daily': 'temperature_2m_max',
        'timezone': location['timezone'],
        'start_date': date.strftime('%Y-%m-%d'),
        'end_date': date.strftime('%Y-%m-%d'),
    }
    
    response = requests.get(HISTORICAL_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'daily' in data and 'temperature_2m_max' in data['daily']:
        temp_max = data['daily']['temperature_2m_max'][0]
        return temp_max
    else:
        raise ValueError(f"No data returned for {date}")


def fetch_actual_temp(date, location_key='warsaw'):
    """Fetch actual max temp for a given date (with retry)"""
    try:
        temp_max = retry_with_backoff(_fetch_actual_temp_single, date, location_key)
        return temp_max
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:97] + "..."
        print(f"❌ Error fetching actual temp: {error_msg}")
        return None


def _fetch_imgw_forecast_single(target_date, location_key):
    """Single attempt to fetch IMGW HYBRID forecast (used by retry wrapper)"""
    location = LOCATIONS[location_key]
    
    params = {
        'token': IMGW_TOKEN,
        'lat': location['lat'],
        'lon': location['lon'],
        'm': 'hybrid'  # HYBRID = UM + AROME combined
    }
    
    response = requests.get(IMGW_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # Extract tomorrow's forecast from Day_Night_Data (more granular than Daily_Data)
    if 'data' in data and 'Day_Night_Data' in data['data']:
        day_night_data = data['data']['Day_Night_Data']
        
        # Find tomorrow's DAY entry (isDay=True)
        tomorrow_str = target_date.strftime('%Y-%m-%d')
        for entry in day_night_data:
            date_str = entry.get('Date', '')
            is_day = entry.get('isDay', False)
            
            if date_str.startswith(tomorrow_str) and is_day:
                # Temperature is in Kelvin, convert to Celsius
                temp_k = float(entry['Temp_Max'])
                temp_c = temp_k - 273.15
                return temp_c
        
        raise ValueError(f"No day data for {target_date} in IMGW response")
    else:
        raise ValueError("Invalid IMGW API response structure")


def fetch_imgw_forecast(target_date, location_key='warsaw'):
    """Fetch tomorrow's max temp from IMGW HYBRID model (with retry)"""
    try:
        temp_max = retry_with_backoff(_fetch_imgw_forecast_single, target_date, location_key)
        return temp_max
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:97] + "..."
        print(f"❌ imgw_hybrid: {error_msg}")
        return None


def collect_forecasts_parallel(location_key='warsaw', use_parallel=True):
    """Collect forecasts from all models using parallel requests"""
    location = LOCATIONS[location_key]
    print(f"\n🌍 Collecting forecasts for {location['name']}, {location['country']}")
    
    now = datetime.now()
    tomorrow = now.date() + timedelta(days=1)
    hours_ahead = (datetime.combine(tomorrow, datetime.min.time()) - now).total_seconds() / 3600
    
    print(f"📅 Target date: {tomorrow} ({hours_ahead:.1f}h ahead)")
    print(f"🕐 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    # Get models for this location (Open-Meteo + location-specific like IMGW)
    location_models = MODELS + LOCATION_SPECIFIC_MODELS.get(location_key, [])
    
    results = {}
    start_time = time.time()
    
    if use_parallel:
        # Parallel requests using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            # Submit all tasks
            future_to_model = {}
            for model in location_models:
                if model == 'imgw_hybrid':
                    future_to_model[executor.submit(fetch_imgw_forecast, tomorrow, location_key)] = model
                else:
                    future_to_model[executor.submit(fetch_forecast, model, tomorrow, location_key)] = model
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    temp_max = future.result()
                    if temp_max is not None:
                        results[model] = temp_max
                        c.execute('''
                            INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max, location)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (model, now, tomorrow, hours_ahead, temp_max, location_key))
                        print(f"✓ {model:25s} {temp_max:5.1f}°C")
                    else:
                        print(f"✗ {model:25s} failed")
                except Exception as e:
                    print(f"✗ {model:25s} error: {str(e)[:50]}")
    else:
        # Sequential requests (fallback)
        for model in location_models:
            if model == 'imgw_hybrid':
                temp_max = fetch_imgw_forecast(tomorrow, location_key)
            else:
                temp_max = fetch_forecast(model, tomorrow, location_key)
            
            if temp_max is not None:
                results[model] = temp_max
                c.execute('''
                    INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (model, now, tomorrow, hours_ahead, temp_max, location_key))
                print(f"✓ {model:25s} {temp_max:5.1f}°C")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Collection time: {elapsed:.2f}s")
    
    # Calculate ensemble if we have multiple forecasts
    if len(results) >= 2:
        temps = list(results.values())
        ensemble_median = statistics.median(temps)
        ensemble_mean = statistics.mean(temps)
        
        # Save ensemble forecasts
        c.execute('''
            INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('ENSEMBLE_MEDIAN', now, tomorrow, hours_ahead, ensemble_median, location_key))
        
        c.execute('''
            INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('ENSEMBLE_MEAN', now, tomorrow, hours_ahead, ensemble_mean, location_key))
        
        print(f"\n📊 Ensemble:")
        print(f"   Median: {ensemble_median:.1f}°C")
        print(f"   Mean:   {ensemble_mean:.1f}°C")
        print(f"   Range:  {min(temps):.1f}°C - {max(temps):.1f}°C")
    
    conn.commit()
    conn.close()
    
    print(f"✅ {location['name']} forecasts saved!")


def collect_all_locations(use_parallel=True):
    """Collect forecasts for all configured locations"""
    print("=" * 60)
    print("🌐 MULTI-LOCATION FORECAST COLLECTION")
    print("=" * 60)
    
    for location_key in LOCATIONS.keys():
        try:
            collect_forecasts_parallel(location_key, use_parallel)
        except Exception as e:
            print(f"\n❌ Error collecting {location_key}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ All locations processed!")
    print("=" * 60)


def collect_observation(location_key='warsaw'):
    """Collect actual observation - smart timing"""
    location = LOCATIONS[location_key]
    print(f"\n🌡️  Collecting observation for {location['name']}, {location['country']}")
    
    now = datetime.now()
    dates_to_collect = []
    
    # Always collect yesterday (might be missing)
    yesterday = now.date() - timedelta(days=1)
    dates_to_collect.append(('yesterday', yesterday))
    
    # If after 18:00 UTC (evening), also collect today
    # Temperature peak is usually 14-16:00 local, so 18:00 UTC is safe
    if now.hour >= 18:
        today = now.date()
        dates_to_collect.append(('today', today))
        print(f"⏰ After 18:00 UTC - collecting TODAY + yesterday")
    
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    for label, date in dates_to_collect:
        print(f"📅 {label.capitalize()}: {date}", end=' ')
        
        actual_temp = fetch_actual_temp(date, location_key)
        
        if actual_temp is not None:
            try:
                c.execute('''
                    INSERT INTO observations (date, temp_max, location)
                    VALUES (?, ?, ?)
                ''', (date, actual_temp, location_key))
                conn.commit()
                print(f"✅ {actual_temp:.1f}°C recorded")
            except sqlite3.IntegrityError:
                print(f"⚠️  Already exists ({actual_temp:.1f}°C)")
        else:
            print(f"❌ Failed to fetch")
    
    conn.close()


def collect_all_observations():
    """Collect observations for all locations"""
    print("=" * 60)
    print("🌡️  MULTI-LOCATION OBSERVATION COLLECTION")
    print("=" * 60)
    
    for location_key in LOCATIONS.keys():
        try:
            collect_observation(location_key)
        except Exception as e:
            print(f"\n❌ Error collecting observation for {location_key}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ All observations processed!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Weather Forecast Tracker')
    parser.add_argument('action', choices=['forecast', 'observe', 'forecast-all', 'observe-all'], 
                       help='Action to perform')
    parser.add_argument('--location', choices=list(LOCATIONS.keys()), default='warsaw',
                       help='Location to collect data for (default: warsaw)')
    parser.add_argument('--no-parallel', action='store_true',
                       help='Disable parallel API requests')
    
    args = parser.parse_args()
    
    init_db()
    
    if args.action == 'forecast':
        collect_forecasts_parallel(args.location, use_parallel=not args.no_parallel)
    elif args.action == 'observe':
        collect_observation(args.location)
    elif args.action == 'forecast-all':
        collect_all_locations(use_parallel=not args.no_parallel)
    elif args.action == 'observe-all':
        collect_all_observations()
