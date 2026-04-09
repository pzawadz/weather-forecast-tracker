"""
Weather Forecast Tracker - Shared Configuration
Single source of truth for all configuration constants.
"""

import os

# Database path - always relative to this file's location
DB_PATH = os.path.join(os.path.dirname(__file__), "weather_forecasts.db")

# Location configurations
LOCATIONS = {
    'warsaw': {
        'name': 'Warsaw',
        'country': 'Poland',
        'flag': '🇵🇱',
        'lat': 52.2297,
        'lon': 21.0122,
        'timezone': 'Europe/Warsaw',
        'models_priority': ['icon_eu', 'ecmwf_ifs025'],  # Best for Poland
        'native_model': 'imgw_hybrid'  # Polish IMGW model
    },
    'paris': {
        'name': 'Paris',
        'country': 'France',
        'flag': '🇫🇷',
        'lat': 48.8566,
        'lon': 2.3522,
        'timezone': 'Europe/Paris',
        'models_priority': ['meteofrance_seamless', 'ecmwf_ifs025'],  # Native French
        'native_model': 'meteofrance_seamless'
    },
    'munich': {
        'name': 'Munich',
        'country': 'Germany',
        'flag': '🇩🇪',
        'lat': 48.1351,
        'lon': 11.5820,
        'timezone': 'Europe/Berlin',
        'models_priority': ['icon_eu', 'ecmwf_ifs025'],  # Native German (ICON-EU)
        'native_model': 'icon_eu'
    },
    'london': {
        'name': 'London',
        'country': 'UK',
        'flag': '🇬🇧',
        'lat': 51.5074,
        'lon': -0.1278,
        'timezone': 'Europe/London',
        'models_priority': ['ecmwf_ifs025', 'icon_eu'],  # ECMWF good for UK
        'native_model': 'ecmwf_ifs025'
    }
}

# Weather models (Open-Meteo)
MODELS_OPENMETEO = [
    'ecmwf_ifs025',        # ECMWF IFS (9km) - European model
    'icon_global',         # DWD ICON Global (13km) - German global
    'icon_eu',             # DWD ICON-EU (7km) - European regional
    'gfs_global',          # NOAA GFS (13km) - US model
    'meteofrance_seamless',# Meteo France (variable) - French model
    'gem_global'           # CMC GEM (variable) - Canadian model
]

# Special models (location-specific)
MODELS_SPECIAL = {
    'warsaw': ['imgw_hybrid']  # IMGW HYBRID 1.0 (UM 4km + AROME 2.5km)
}

# All models combined (for queries)
ALL_MODELS = MODELS_OPENMETEO + ['imgw_hybrid']

# API Configuration
OPENMETEO_API_BASE = 'https://api.open-meteo.com/v1/forecast'
IMGW_API_BASE = 'https://meteo.imgw.pl/api/v1/forecast/fcapi'
IMGW_API_TOKEN = 'p4DXKjsYadfBV21TYrDk'  # Public token

# Retry configuration
RETRY_DELAYS = [5, 15, 30]  # seconds
RETRY_MAX_ATTEMPTS = 3

# Dashboard configuration
DASHBOARD_CACHE_TTL = 300  # seconds (5 minutes)
DASHBOARD_DB_TIMEOUT = 5000  # milliseconds

# Polymarket betting windows (hours ahead)
BETTING_WINDOWS = {
    'primary': 18,    # Best balance: ~85% accuracy
    'secondary': 24,  # Standard benchmark: ~80% accuracy
    'early': 48       # Contrarian plays: ~70% accuracy
}
