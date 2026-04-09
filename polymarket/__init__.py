"""
Polymarket Integration Module
Read-only market discovery and analysis (Phase 1)
"""

__version__ = "0.1.0"
__phase__ = "1 - Read-Only"

from .client import PolymarketClient
from .market_finder import WeatherMarketFinder

__all__ = [
    'PolymarketClient',
    'WeatherMarketFinder',
]
