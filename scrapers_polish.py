#!/usr/bin/env python3
"""
Polish weather model scrapers (Meteo.pl, IMGW)
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# Warsaw coordinates for Meteo.pl grid
WARSAW_ROW = 406
WARSAW_COL = 250

def scrape_meteo_pl_um():
    """
    Scrape UM (Unified Model) forecast from Meteo.pl
    Returns tomorrow's max temp
    """
    try:
        url = f"https://www.meteo.pl/um/php/meteorogram_list.php?ntype=0u&row={WARSAW_ROW}&col={WARSAW_COL}&lang=pl&cname=Warszawa"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Meteo.pl meteogram format:
        # Look for meteorogram image URL or data table
        
        # Method 1: Try to find direct data table
        tables = soup.find_all('table')
        
        # Method 2: Parse meteorogram image URL and extract data from filename
        img = soup.find('img', {'alt': re.compile('Meteorogram')})
        if img and img.get('src'):
            meteogram_url = img['src']
            # Some meteograms encode data in URL parameters
            print(f"   Found meteogram: {meteogram_url}")
        
        # Method 3: Check if there's a JSON/CSV data endpoint
        # Meteo.pl sometimes has mgram.php endpoint with CSV data
        csv_url = f"https://www.meteo.pl/um/php/mgram_csv.php?ntype=0u&row={WARSAW_ROW}&col={WARSAW_COL}&lang=pl"
        csv_response = requests.get(csv_url, timeout=10)
        
        if csv_response.status_code == 200 and len(csv_response.text) > 100:
            lines = csv_response.text.strip().split('\n')
            
            # Parse CSV format
            # Format varies, typically: date, hour, temp, pressure, wind, etc.
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            max_temp_tomorrow = None
            
            for line in lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        date_str = parts[0].strip()
                        time_str = parts[1].strip()
                        temp_str = parts[2].strip()
                        
                        # Parse date (format may vary)
                        if str(tomorrow) in date_str or tomorrow.strftime('%Y%m%d') in date_str:
                            temp = float(temp_str)
                            if max_temp_tomorrow is None or temp > max_temp_tomorrow:
                                max_temp_tomorrow = temp
                    except (ValueError, IndexError):
                        continue
            
            if max_temp_tomorrow is not None:
                return max_temp_tomorrow
        
        # If CSV parsing failed, return None
        print("   ⚠️  UM: Could not parse data from Meteo.pl")
        return None
        
    except Exception as e:
        print(f"   ❌ UM scraping error: {e}")
        return None


def scrape_imgw_arome():
    """
    Scrape AROME forecast from IMGW cmm.imgw.pl
    Returns tomorrow's max temp
    
    NOTE: IMGW uses interactive maps, may require selenium/playwright
    This is a simplified version
    """
    try:
        # IMGW CMM uses JavaScript-heavy interface
        # Direct API endpoint (if exists):
        base_url = "https://cmm.imgw.pl"
        
        # Check if there's a direct data API
        # This is a placeholder - actual implementation would need:
        # 1. Selenium/Playwright for JS rendering
        # 2. Or reverse-engineering their API calls
        
        print("   ⚠️  AROME: IMGW scraping requires JS rendering (TODO)")
        return None
        
    except Exception as e:
        print(f"   ❌ AROME scraping error: {e}")
        return None


def test_scrapers():
    """Test all scrapers"""
    print("Testing Polish model scrapers\n")
    
    print("1. Meteo.pl (UM)")
    print("-"*60)
    um_temp = scrape_meteo_pl_um()
    if um_temp:
        print(f"   ✓ UM forecast: {um_temp:.1f}°C")
    else:
        print("   ✗ UM scraping failed")
    
    print("\n2. IMGW (AROME)")
    print("-"*60)
    arome_temp = scrape_imgw_arome()
    if arome_temp:
        print(f"   ✓ AROME forecast: {arome_temp:.1f}°C")
    else:
        print("   ✗ AROME scraping not implemented yet")


if __name__ == "__main__":
    test_scrapers()
