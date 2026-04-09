#!/usr/bin/env python3
"""
Research Polish weather sources with Playwright
Explore structure of IMGW meteo site
"""

from playwright.sync_api import sync_playwright
import json
import time

print("=== Exploring IMGW Meteo Site ===\n")

def explore_imgw():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless for server
        page = browser.new_page()
        
        # Go to IMGW meteo
        print("1. Loading meteo.imgw.pl...")
        page.goto("http://meteo.imgw.pl", wait_until="networkidle", timeout=30000)
        time.sleep(3)  # Wait for JavaScript
        
        print(f"   Title: {page.title()}")
        print(f"   URL: {page.url}")
        
        # Take screenshot
        page.screenshot(path="imgw_homepage.png")
        print("   Screenshot saved: imgw_homepage.png")
        
        # Find Warsaw link/button
        print("\n2. Looking for Warsaw forecast...")
        
        # Try common selectors
        selectors_to_try = [
            "text=Warszawa",
            "text=Warsaw",
            "[data-city='Warszawa']",
            "a:has-text('Warszawa')",
            "button:has-text('Warszawa')",
            ".city-link:has-text('Warszawa')"
        ]
        
        for selector in selectors_to_try:
            try:
                element = page.query_selector(selector)
                if element:
                    print(f"   ✓ Found with selector: {selector}")
                    print(f"     Text: {element.text_content()}")
                    break
            except:
                continue
        
        # Get all links
        print("\n3. Analyzing page structure...")
        links = page.query_selector_all("a")
        print(f"   Total links: {len(links)}")
        
        # Look for forecast-related links
        forecast_links = []
        for link in links[:50]:  # First 50 links
            text = link.text_content().strip()
            href = link.get_attribute("href")
            if text and ("warszawa" in text.lower() or "prognoza" in text.lower()):
                forecast_links.append({"text": text, "href": href})
        
        if forecast_links:
            print("\n   Forecast-related links found:")
            for link in forecast_links[:10]:
                print(f"     - {link['text']}: {link['href']}")
        
        # Check for forecast data in page content
        print("\n4. Checking for forecast data...")
        content = page.content()
        
        has_temp_data = "°C" in content or "temperatura" in content.lower()
        has_forecast = "prognoza" in content.lower()
        
        print(f"   Has temperature data: {has_temp_data}")
        print(f"   Has forecast mention: {has_forecast}")
        
        # Check localStorage/sessionStorage
        print("\n5. Checking browser storage...")
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")
        session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
        
        print(f"   LocalStorage: {len(local_storage)} chars")
        print(f"   SessionStorage: {len(session_storage)} chars")
        
        # Save final HTML
        with open("imgw_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("\n6. HTML saved to: imgw_page.html")
        
        browser.close()
        print("\n✅ Exploration complete!")

if __name__ == "__main__":
    try:
        explore_imgw()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
