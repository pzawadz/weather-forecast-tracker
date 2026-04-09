#!/usr/bin/env python3
"""
IMGW API Update Frequency Monitor
Tracks when Daily_Data (forecast) changes
"""

import requests
from datetime import datetime
import time
import json

BASE_URL = 'https://meteo.imgw.pl/api/v1/forecast/fcapi'
TOKEN = 'p4DXKjsYadfBV21TYrDk'

def fetch_forecast():
    """Fetch current forecast"""
    params = {
        'token': TOKEN,
        'lat': 52.240528,
        'lon': 21.034166,
        'm': 'hybrid'
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        
        # Extract tomorrow's forecast
        if 'Daily_Data' in data and len(data['Daily_Data']) > 0:
            tomorrow = data['Daily_Data'][0]
            temp_max_c = round(float(tomorrow['Temp_Max']) - 273.15, 1)
            return {
                'timestamp': datetime.now().isoformat(),
                'temp_max': temp_max_c,
                'date': tomorrow['Date']
            }
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    return None

def monitor(duration_hours=6, check_interval_minutes=15):
    """Monitor forecast changes"""
    print(f'=== IMGW Forecast Monitor ===')
    print(f'Duration: {duration_hours}h, Check every: {check_interval_minutes}min\n')
    
    results = []
    last_temp = None
    
    checks = int((duration_hours * 60) / check_interval_minutes)
    
    for i in range(checks):
        check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f'[{i+1}/{checks}] {check_time}', end=' ')
        
        forecast = fetch_forecast()
        
        if forecast and 'temp_max' in forecast:
            temp = forecast['temp_max']
            
            if last_temp is None:
                print(f'→ {temp}°C (baseline)')
            elif temp != last_temp:
                print(f'→ {temp}°C (CHANGED from {last_temp}°C!) ⚠️')
            else:
                print(f'→ {temp}°C (unchanged)')
            
            last_temp = temp
            results.append(forecast)
        else:
            print(f'→ Error: {forecast.get("error", "Unknown")}')
            results.append(forecast)
        
        # Sleep until next check (except last iteration)
        if i < checks - 1:
            time.sleep(check_interval_minutes * 60)
    
    # Save results
    with open('imgw_monitor_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'\n✅ Monitoring complete! Results saved to imgw_monitor_results.json')
    
    # Analyze changes
    changes = []
    for i in range(1, len(results)):
        if 'temp_max' in results[i] and 'temp_max' in results[i-1]:
            if results[i]['temp_max'] != results[i-1]['temp_max']:
                changes.append({
                    'time': results[i]['timestamp'],
                    'old': results[i-1]['temp_max'],
                    'new': results[i]['temp_max']
                })
    
    if changes:
        print(f'\n📊 Detected {len(changes)} change(s):')
        for change in changes:
            print(f'  {change["time"]}: {change["old"]}°C → {change["new"]}°C')
    else:
        print('\n📊 No changes detected during monitoring period')

if __name__ == '__main__':
    import sys
    
    # Quick test: 1 hour, every 10 minutes
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        monitor(duration_hours=1, check_interval_minutes=10)
    # Default: 6 hours, every 15 minutes
    else:
        monitor(duration_hours=6, check_interval_minutes=15)
