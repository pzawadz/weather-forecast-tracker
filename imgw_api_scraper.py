#!/usr/bin/env python3
"""
Polish Weather Models Scraper - PRODUCTION VERSION
Fetches UM/AROME forecast data from IMGW API
"""

import requests
from datetime import datetime, timedelta
import json

class PolishForecastAPI:
    """Direct API client for IMGW forecast data"""
    
    # API endpoint and token (extracted from meteo.imgw.pl)
    BASE_URL = "https://meteo.imgw.pl/api/v1/forecast/fcapi"
    TOKEN = "p4DXKjsYadfBV21TYrDk"
    
    # Warsaw coordinates
    WARSAW_LAT = 52.240528
    WARSAW_LON = 21.034166
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WeatherTracker/1.0)'
        })
    
    def get_forecast(self, lat=None, lon=None, model='hybrid'):
        """
        Fetch forecast from IMGW API
        
        Args:
            lat: Latitude (default: Warsaw)
            lon: Longitude (default: Warsaw)
            model: Model type - 'hybrid', 'um', or 'arome'
        
        Returns:
            dict: Forecast data
        """
        lat = lat or self.WARSAW_LAT
        lon = lon or self.WARSAW_LON
        
        params = {
            'token': self.TOKEN,
            'lat': lat,
            'lon': lon,
            'm': model
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return None
    
    def extract_tomorrow_temp_max(self, forecast_data):
        """Extract tomorrow's max temperature from forecast"""
        if not forecast_data or 'data' not in forecast_data:
            return None
        
        data = forecast_data['data']
        
        # Tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        # Try Daily_Data first (cleaner)
        if 'Daily_Data' in data and len(data['Daily_Data']) > 0:
            for day in data['Daily_Data']:
                date_str = day.get('Date', '')
                if date_str:
                    day_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                    if day_date == tomorrow:
                        temp_k = float(day['Temp_Max'])
                        temp_c = temp_k - 273.15
                        return {
                            'date': tomorrow.isoformat(),
                            'temp_max_k': temp_k,
                            'temp_max_c': round(temp_c, 1),
                            'model': data.get('Model', 'UNKNOWN'),
                            'source': 'Daily_Data'
                        }
        
        # Fallback: Day_Night_Data (find day entries for tomorrow)
        if 'Day_Night_Data' in data:
            day_entries = [e for e in data['Day_Night_Data'] 
                          if e.get('isDay') == True]
            
            for entry in day_entries:
                date_str = entry.get('Date', '')
                if date_str:
                    entry_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                    if entry_date == tomorrow:
                        temp_k = float(entry['Temp_Max'])
                        temp_c = temp_k - 273.15
                        return {
                            'date': tomorrow.isoformat(),
                            'temp_max_k': temp_k,
                            'temp_max_c': round(temp_c, 1),
                            'model': data.get('Model', 'UNKNOWN'),
                            'source': 'Day_Night_Data'
                        }
        
        return None

def test_api():
    """Test the IMGW API"""
    print("=== Testing IMGW Forecast API ===\n")
    
    api = PolishForecastAPI()
    
    # Test different models
    models = ['hybrid', 'um', 'arome']
    
    for model in models:
        print(f"\n--- Model: {model.upper()} ---")
        
        forecast = api.get_forecast(model=model)
        
        if forecast:
            temp_data = api.extract_tomorrow_temp_max(forecast)
            
            if temp_data:
                print(f"✓ Success!")
                print(f"  Date: {temp_data['date']}")
                print(f"  Temp Max: {temp_data['temp_max_c']}°C")
                print(f"  Model: {temp_data['model']}")
                print(f"  Source: {temp_data['source']}")
            else:
                print(f"✗ No tomorrow data found")
        else:
            print(f"✗ API request failed")
    
    print("\n✅ API test complete!")

def scrape_polish_models():
    """Main function to scrape Polish models"""
    print("=== Scraping Polish Weather Models ===\n")
    
    api = PolishForecastAPI()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'location': {
            'name': 'Warsaw',
            'lat': api.WARSAW_LAT,
            'lon': api.WARSAW_LON
        },
        'forecasts': {}
    }
    
    # Scrape HYBRID (UM + AROME combined)
    print("1. Fetching HYBRID model (UM + AROME)...")
    hybrid_forecast = api.get_forecast(model='hybrid')
    if hybrid_forecast:
        temp = api.extract_tomorrow_temp_max(hybrid_forecast)
        if temp:
            results['forecasts']['hybrid'] = temp
            print(f"   ✓ {temp['temp_max_c']}°C")
    
    # Try individual models (may or may not work)
    for model in ['um', 'arome']:
        print(f"\n2. Fetching {model.upper()} model...")
        forecast = api.get_forecast(model=model)
        if forecast:
            temp = api.extract_tomorrow_temp_max(forecast)
            if temp:
                results['forecasts'][model] = temp
                print(f"   ✓ {temp['temp_max_c']}°C")
            else:
                print(f"   ✗ No data")
        else:
            print(f"   ✗ Failed")
    
    # Save results
    with open('polish_models_data.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Scraping complete!")
    print(f"Results saved to: polish_models_data.json")
    
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_api()
    else:
        scrape_polish_models()
