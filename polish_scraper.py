#!/usr/bin/env python3
"""
Polish Weather Models Scraper (DEVELOPMENT VERSION)
Scrapes UM (4km) and AROME (2.5km) forecasts from IMGW
"""

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import json
import time
import re

class PolishWeatherScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.results = {}
        
    def scrape_imgw_warsaw(self):
        """Scrape IMGW meteo for Warsaw forecast"""
        print("\n=== Scraping IMGW Meteo (UM model - 4km) ===\n")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                # Step 1: Load homepage
                print("1. Loading meteo.imgw.pl...")
                page.goto("http://meteo.imgw.pl", wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                # Step 2: Look for forecast data
                print("2. Looking for Warsaw forecast data...")
                
                # Check if we're already on Warsaw page
                title = page.title()
                content = page.content()
                
                if "Warszawa" in content:
                    print("   ✓ Found Warsaw data on homepage")
                    
                    # Look for temperature in different formats
                    # Try to find tomorrow's forecast
                    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m")
                    print(f"   Looking for date: {tomorrow}")
                    
                    # Extract all temperature mentions
                    temp_pattern = r'(\d+\.?\d*)\s*°C'
                    temps = re.findall(temp_pattern, content)
                    
                    if temps:
                        print(f"   Found {len(temps)} temperature values")
                        print(f"   Sample temps: {temps[:10]}")
                    
                    # Try to click on forecast/prognoza link
                    forecast_links = [
                        "text=Prognoza",
                        "text=Forecast",
                        "a:has-text('prognoza')",
                        "[href*='prognoza']"
                    ]
                    
                    for selector in forecast_links:
                        try:
                            element = page.query_selector(selector)
                            if element:
                                print(f"   ✓ Found forecast link: {selector}")
                                element.click()
                                page.wait_for_load_state("networkidle", timeout=10000)
                                time.sleep(2)
                                break
                        except:
                            continue
                    
                    # Try navigation menu
                    print("\n3. Checking navigation...")
                    nav_selectors = [
                        "button:has-text('Prognozy')",
                        "a:has-text('Prognozy')",
                        "[href*='prognoz']"
                    ]
                    
                    for selector in nav_selectors:
                        try:
                            element = page.query_selector(selector)
                            if element:
                                print(f"   ✓ Found navigation: {selector}")
                                element.click()
                                page.wait_for_load_state("networkidle", timeout=10000)
                                time.sleep(2)
                                break
                        except:
                            continue
                    
                    # Take screenshot of current state
                    page.screenshot(path="warsaw_forecast.png")
                    print("   Screenshot saved: warsaw_forecast.png")
                    
                    # Extract structured forecast data
                    print("\n4. Extracting forecast data...")
                    
                    # Look for forecast tables/widgets
                    forecast_sections = page.query_selector_all(".forecast, .prognoza, [class*='forecast'], [class*='prognoza']")
                    print(f"   Found {len(forecast_sections)} potential forecast sections")
                    
                    # Try to extract JSON data from page
                    print("\n5. Checking for JSON data...")
                    scripts = page.query_selector_all("script")
                    for script in scripts:
                        script_content = script.inner_text()
                        if "forecast" in script_content.lower() or "prognoza" in script_content.lower():
                            if "{" in script_content:
                                print("   ✓ Found script with forecast data")
                                # Save first 500 chars
                                print(f"   Preview: {script_content[:500]}")
                                break
                    
                    # Save full HTML for analysis
                    final_html = page.content()
                    with open("warsaw_forecast_full.html", "w", encoding="utf-8") as f:
                        f.write(final_html)
                    print("\n6. Full HTML saved to: warsaw_forecast_full.html")
                
                else:
                    print("   ✗ Warsaw not found on homepage")
                
                # Try to access API directly (if visible in network)
                print("\n7. Checking for API calls...")
                # This would require monitoring network requests
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                browser.close()
        
        return self.results
    
    def scrape_all_sources(self):
        """Scrape all Polish weather sources"""
        # For now, just IMGW
        imgw_data = self.scrape_imgw_warsaw()
        
        return {
            'imgw_um': imgw_data,
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    scraper = PolishWeatherScraper(headless=True)
    results = scraper.scrape_all_sources()
    
    # Save results
    with open("polish_forecast_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Scraping complete!")
    print("Results saved to: polish_forecast_results.json")
