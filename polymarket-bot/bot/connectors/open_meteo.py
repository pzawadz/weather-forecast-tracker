"""
Open-Meteo weather connector.

Fetches forecasts from multiple NWP models via Open-Meteo API.
Supports global locations (not just US like NWS).
Free, no API key required.

API docs: https://open-meteo.com/en/docs
"""

import requests
from datetime import date
from typing import Optional, Dict, List
import structlog

logger = structlog.get_logger()

# Models available via Open-Meteo
# Weights based on general accuracy, confidence from literature
MODELS = {
    "ecmwf_ifs025": {"name": "ECMWF IFS", "weight": 2.0, "confidence": 0.92},
    "icon_global": {"name": "DWD ICON", "weight": 1.5, "confidence": 0.88},
    "gfs_global": {"name": "NOAA GFS", "weight": 1.0, "confidence": 0.85},
    "meteofrance_arpege_world": {"name": "Meteo France", "weight": 1.0, "confidence": 0.85},
    "gem_global": {"name": "GEM Global", "weight": 1.0, "confidence": 0.83},
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast(
    lat: float, 
    lon: float, 
    target_date: date, 
    model: str
) -> Optional[Dict]:
    """
    Fetch forecast for a specific model from Open-Meteo.
    
    Args:
        lat: Latitude
        lon: Longitude
        target_date: Date to forecast
        model: Model identifier (e.g., "ecmwf_ifs025")
    
    Returns:
        Dict with temp_max_c, temp_max_f, temp_min_c, temp_min_f, model, confidence
        None if forecast not available
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min",
        "models": model,
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "timezone": "auto",
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        temps_max = data.get("daily", {}).get("temperature_2m_max", [])
        temps_min = data.get("daily", {}).get("temperature_2m_min", [])
        
        if not temps_max or temps_max[0] is None:
            logger.warning("no_forecast_data", model=model, date=target_date)
            return None
        
        temp_max_c = temps_max[0]
        temp_min_c = temps_min[0] if temps_min and temps_min[0] is not None else None
        
        return {
            "temp_max_c": temp_max_c,
            "temp_max_f": temp_max_c * 9/5 + 32,
            "temp_min_c": temp_min_c,
            "temp_min_f": temp_min_c * 9/5 + 32 if temp_min_c is not None else None,
            "model": model,
            "confidence": MODELS[model]["confidence"],
        }
    
    except Exception as e:
        logger.error("fetch_forecast_failed", model=model, error=str(e))
        return None


def fetch_ensemble_forecast(
    lat: float, 
    lon: float, 
    target_date: date
) -> Optional[Dict]:
    """
    Fetch forecasts from all models and compute weighted ensemble.
    
    Args:
        lat: Latitude
        lon: Longitude
        target_date: Date to forecast
    
    Returns:
        Dict with:
        - temp_max_f: weighted average forecast (Fahrenheit)
        - temp_max_c: weighted average forecast (Celsius)
        - model_spread_f: max - min across models (uncertainty measure)
        - model_count: number of models that returned data
        - individual_forecasts: list of per-model results
        - ensemble_sigma_f: estimated forecast uncertainty (Fahrenheit)
        - ensemble_sigma_c: estimated forecast uncertainty (Celsius)
        
        None if no models returned data
    """
    forecasts = []
    
    for model_key, model_info in MODELS.items():
        result = fetch_forecast(lat, lon, target_date, model_key)
        if result:
            result["weight"] = model_info["weight"]
            forecasts.append(result)
    
    if not forecasts:
        logger.warning("no_ensemble_data", date=target_date)
        return None
    
    # Weighted average
    total_weight = sum(f["weight"] for f in forecasts)
    temp_max_f = sum(f["temp_max_f"] * f["weight"] for f in forecasts) / total_weight
    temp_max_c = sum(f["temp_max_c"] * f["weight"] for f in forecasts) / total_weight
    
    # Model spread = measure of uncertainty
    all_temps_f = [f["temp_max_f"] for f in forecasts]
    model_spread_f = max(all_temps_f) - min(all_temps_f)
    
    # Dynamic sigma: base sigma + model disagreement
    # Base: 4°F for 1-day forecast (European models)
    # Added: half of model spread as additional uncertainty
    base_sigma_f = 4.0
    base_sigma_c = 2.2
    ensemble_sigma_f = base_sigma_f + (model_spread_f / 2.0)
    ensemble_sigma_c = ensemble_sigma_f / 1.8  # F to C conversion
    
    logger.info(
        "ensemble_computed",
        date=target_date,
        temp_f=round(temp_max_f, 1),
        temp_c=round(temp_max_c, 1),
        spread_f=round(model_spread_f, 1),
        sigma_f=round(ensemble_sigma_f, 1),
        model_count=len(forecasts)
    )
    
    return {
        "temp_max_f": temp_max_f,
        "temp_max_c": temp_max_c,
        "model_spread_f": model_spread_f,
        "model_count": len(forecasts),
        "individual_forecasts": forecasts,
        "ensemble_sigma_f": ensemble_sigma_f,
        "ensemble_sigma_c": ensemble_sigma_c,
    }
