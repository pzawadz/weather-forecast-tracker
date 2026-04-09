"""
Polymarket API Client (Read-Only)
Phase 1: Market discovery and price data only, NO trading
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class PolymarketClient:
    """
    Read-only client for Polymarket public API.
    
    Phase 1: No authentication, no trading, just data fetching.
    """
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize client.
        
        Args:
            api_key: Optional API key (not needed for read-only in Phase 1)
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WeatherForecastTracker/0.1.0',
            'Accept': 'application/json'
        })
    
    def search_markets(self, query: str, active_only: bool = True, limit: int = 100) -> List[Dict]:
        """
        Search markets by keyword.
        
        Args:
            query: Search query (e.g., "temperature", "weather", "Paris")
            active_only: Only return active (non-resolved) markets
            limit: Max results to return
        
        Returns:
            List of market dictionaries
        
        Example:
            >>> client = PolymarketClient()
            >>> markets = client.search_markets("Paris temperature")
            >>> for m in markets:
            ...     print(f"{m['question']} - ${m['volume']}")
        """
        url = f"{self.BASE_URL}/markets"
        params = {
            'limit': limit,
            'offset': 0
        }
        
        if active_only:
            params['closed'] = 'false'
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filter by query (API might not support search, so we filter locally)
            markets = data if isinstance(data, list) else data.get('data', [])
            
            if query:
                query_lower = query.lower()
                markets = [
                    m for m in markets
                    if query_lower in m.get('question', '').lower() or
                       query_lower in m.get('description', '').lower()
                ]
            
            return markets
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching markets: {e}")
            return []
    
    def get_market(self, market_id: str) -> Optional[Dict]:
        """
        Get detailed market information including current prices.
        
        Args:
            market_id: Market ID or condition ID
        
        Returns:
            Market dictionary with prices, volume, liquidity
        
        Example:
            >>> market = client.get_market("0x123...")
            >>> print(f"YES price: {market['outcomes'][0]['price']}")
        """
        url = f"{self.BASE_URL}/markets/{market_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching market {market_id}: {e}")
            return None
    
    def get_price_history(self, market_id: str, days: int = 7) -> Optional[List[Dict]]:
        """
        Get historical price data for a market.
        
        Args:
            market_id: Market ID
            days: Number of days of history
        
        Returns:
            List of price points with timestamps
        
        Example:
            >>> history = client.get_price_history("0x123...", days=7)
            >>> for point in history:
            ...     print(f"{point['t']}: {point['p']}")
        """
        url = f"{self.BASE_URL}/prices-history"
        params = {
            'market': market_id,
            'interval': '1h',  # Hourly data
            'fidelity': days
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching price history: {e}")
            return None
    
    def get_order_book(self, token_id: str) -> Optional[Dict]:
        """
        Get order book (bids/asks) for a market outcome.
        
        Args:
            token_id: Outcome token ID
        
        Returns:
            Order book with bids and asks
        """
        url = f"{self.BASE_URL}/book"
        params = {'token_id': token_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching order book: {e}")
            return None
    
    def get_markets_by_date(self, target_date: datetime) -> List[Dict]:
        """
        Find markets resolving around a specific date.
        
        Useful for finding weather markets for a specific day.
        
        Args:
            target_date: Date to search around
        
        Returns:
            List of markets
        """
        # Search for date in question text
        date_str = target_date.strftime("%B %d")  # e.g., "April 09"
        date_str2 = target_date.strftime("%b %d")  # e.g., "Apr 09"
        date_str3 = target_date.strftime("%Y-%m-%d")  # e.g., "2026-04-09"
        
        markets = []
        for date_format in [date_str, date_str2, date_str3]:
            results = self.search_markets(date_format, active_only=True)
            markets.extend(results)
        
        # Deduplicate by market ID
        seen = set()
        unique_markets = []
        for m in markets:
            market_id = m.get('condition_id') or m.get('id')
            if market_id and market_id not in seen:
                seen.add(market_id)
                unique_markets.append(m)
        
        return unique_markets


# Simple test if run directly
if __name__ == "__main__":
    print("Testing Polymarket Client (Read-Only)\n")
    
    client = PolymarketClient()
    
    # Test 1: Search for weather markets
    print("1. Searching for weather markets...")
    weather_markets = client.search_markets("weather", limit=10)
    print(f"   Found {len(weather_markets)} weather-related markets")
    
    if weather_markets:
        market = weather_markets[0]
        print(f"\n   Example: {market.get('question', 'N/A')}")
        print(f"   Volume: ${market.get('volume', 0):,.0f}")
    
    # Test 2: Search for temperature
    print("\n2. Searching for temperature markets...")
    temp_markets = client.search_markets("temperature", limit=10)
    print(f"   Found {len(temp_markets)} temperature markets")
    
    # Test 3: Search by city
    print("\n3. Searching for Paris markets...")
    paris_markets = client.search_markets("Paris", limit=10)
    print(f"   Found {len(paris_markets)} Paris-related markets")
    
    print("\n✅ Client test complete!")
    print("   Phase 1: Read-only access working")
    print("   Next: Implement market_finder.py for weather-specific filtering")
