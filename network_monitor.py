#!/usr/bin/env python3
"""
Polish Weather Models Scraper - Network Monitor Version
Monitors API calls to find forecast data endpoints
"""

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import json
import time

class NetworkMonitor:
    def __init__(self):
        self.api_calls = []
        self.forecast_data = {}
        
    def log_request(self, request):
        """Log interesting requests"""
        url = request.url
        if any(keyword in url.lower() for keyword in ['api', 'forecast', 'prognoza', 'weather', 'meteo', 'data']):
            self.api_calls.append({
                'url': url,
                'method': request.method,
                'type': request.resource_type
            })
            print(f"   📡 API Call: {request.method} {url[:100]}...")
    
    def log_response(self, response):
        """Log interesting responses"""
        url = response.url
        if 'api' in url.lower() or 'data' in url.lower():
            try:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            self.forecast_data[url] = data
                            print(f"   ✓ JSON Response from: {url[:80]}...")
                            print(f"     Keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                        except:
                            pass
            except:
                pass

def scrape_with_network_monitor():
    """Scrape IMGW with network monitoring"""
    print("\n=== Polish Weather Scraper - Network Monitor ===\n")
    
    monitor = NetworkMonitor()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Setup network monitoring
        page.on("request", monitor.log_request)
        page.on("response", monitor.log_response)
        
        try:
            print("1. Loading meteo.imgw.pl with network monitoring...")
            page.goto("http://meteo.imgw.pl", wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            print("\n2. Analyzing page...")
            # Try to trigger forecast loading
            try:
                # Look for forecast/prognoza buttons/links
                selectors = [
                    "a:has-text('Prognoza')",
                    "button:has-text('Prognoza')",
                    "[href*='prognoz']",
                    "text=Forecast"
                ]
                
                for selector in selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            print(f"   Clicking: {selector}")
                            element.click()
                            page.wait_for_load_state("networkidle", timeout=10000)
                            time.sleep(2)
                            break
                    except:
                        continue
            except:
                pass
            
            print("\n3. Captured API calls:")
            print(f"   Total: {len(monitor.api_calls)}")
            
            if monitor.api_calls:
                print("\n   API Endpoints:")
                for call in monitor.api_calls[:20]:
                    print(f"     {call['method']:6s} {call['url']}")
            
            print(f"\n4. Captured JSON responses: {len(monitor.forecast_data)}")
            
            if monitor.forecast_data:
                print("\n   Forecast Data Sources:")
                for url, data in monitor.forecast_data.items():
                    print(f"     URL: {url}")
                    if isinstance(data, dict):
                        print(f"     Keys: {', '.join(list(data.keys())[:10])}")
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"     Array length: {len(data)}")
                        if isinstance(data[0], dict):
                            print(f"     Item keys: {', '.join(list(data[0].keys())[:5])}")
            
            # Save results
            results = {
                'api_calls': monitor.api_calls,
                'forecast_data': monitor.forecast_data,
                'timestamp': datetime.now().isoformat()
            }
            
            with open("network_monitor_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print("\n✅ Network monitoring complete!")
            print("Results saved to: network_monitor_results.json")
            
            return results
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_with_network_monitor()
