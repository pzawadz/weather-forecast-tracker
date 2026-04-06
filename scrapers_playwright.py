#!/usr/bin/env python3
"""
Playwright-based scraper for Meteo.pl UM model
Requires: pip install playwright && playwright install chromium
"""

import asyncio
import re
from datetime import datetime, timedelta

async def scrape_meteo_pl_um_playwright():
    """
    Use Playwright to render JavaScript and extract UM forecast
    Returns tomorrow's max temp or None
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Install with:")
        print("   pip3 install playwright")
        print("   playwright install chromium")
        return None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load meteogram page
            url = "https://www.meteo.pl/um/php/meteorogram_list.php?ntype=0u&row=406&col=250&lang=pl&cname=Warszawa"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for meteogram to load
            await page.wait_for_timeout(2000)
            
            # Try to find data in page
            # Option 1: Check if there's a data table
            table_data = await page.evaluate("""() => {
                // Look for temperature data in DOM
                const temps = [];
                const tempElements = document.querySelectorAll('.temp, .temperature, [class*="temp"]');
                tempElements.forEach(el => {
                    const text = el.textContent.trim();
                    const match = text.match(/(-?\\d+(\\.\\d+)?)/);
                    if (match) temps.push(parseFloat(match[1]));
                });
                return temps;
            }""")
            
            if table_data and len(table_data) > 0:
                # Find max temp for tomorrow (heuristic: look at data points)
                tomorrow_max = max(table_data[:24]) if len(table_data) >= 24 else max(table_data)
                await browser.close()
                return tomorrow_max
            
            # Option 2: Parse from meteogram image alt text or canvas
            # This is more complex and might require OCR
            
            await browser.close()
            print("⚠️  UM Playwright: Could not extract data from page")
            return None
            
    except Exception as e:
        print(f"❌ UM Playwright error: {e}")
        return None


def scrape_meteo_pl_um():
    """
    Synchronous wrapper for async Playwright scraper
    """
    try:
        return asyncio.run(scrape_meteo_pl_um_playwright())
    except RuntimeError as e:
        if "already running" in str(e):
            # Create new event loop if one is already running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(scrape_meteo_pl_um_playwright())
        raise


async def scrape_imgw_cmm_playwright():
    """
    Scrape IMGW CMM (AROME/ICON-LAM) using Playwright
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # IMGW CMM page
            url = "https://cmm.imgw.pl"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Try to navigate to Warsaw forecast
            # This requires understanding their UI structure
            # Placeholder for now
            
            await browser.close()
            print("⚠️  IMGW AROME: Complex UI, needs manual inspection")
            return None
            
    except Exception as e:
        print(f"❌ IMGW Playwright error: {e}")
        return None


def test_playwright():
    """Test Playwright scrapers"""
    print("Testing Playwright scrapers\n")
    
    print("1. Meteo.pl UM")
    print("-"*60)
    um_temp = scrape_meteo_pl_um()
    if um_temp:
        print(f"✓ UM forecast: {um_temp:.1f}°C")
    else:
        print("✗ UM scraping failed or Playwright not installed")
    
    print("\n2. IMGW CMM (AROME)")
    print("-"*60)
    print("⚠️  Not implemented (complex interactive map)")


if __name__ == "__main__":
    test_playwright()
