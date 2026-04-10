"""
Weather Forecast Tracker integration.

Optional: read pre-collected forecasts + bias data from weather-forecast-tracker SQLite DB.
Advantage: includes historical bias correction based on actual observations.

If tracker DB is available, bot will:
1. Read latest forecasts for target date
2. Read model bias data (7-day average error per model)
3. Apply bias correction to forecasts
4. Return bias-corrected ensemble

If tracker DB is not available, bot falls back to Open-Meteo API directly.
"""

import sqlite3
import os
from datetime import date
from typing import Optional, Dict, List
import structlog

logger = structlog.get_logger()


class TrackerConnector:
    """Read forecasts from weather-forecast-tracker database."""
    
    def __init__(self, db_path: str):
        """
        Initialize tracker connector.
        
        Args:
            db_path: Path to weather_forecasts.db (from weather-forecast-tracker project)
        """
        self.db_path = db_path
        self.available = os.path.exists(db_path) if db_path else False
        
        if not self.available:
            logger.info("tracker_db_not_found", path=db_path, note="Will use Open-Meteo directly")
        else:
            logger.info("tracker_db_found", path=db_path, note="Will use bias-corrected forecasts")
    
    def fetch_forecast(
        self, 
        location_key: str, 
        target_date: date
    ) -> Optional[Dict]:
        """
        Read latest forecasts for target date from tracker DB.
        
        Args:
            location_key: Location identifier (e.g., "warsaw", "london")
            target_date: Date to forecast
        
        Returns:
            Dict with:
            - forecasts: list of {model, temp_max_c, forecast_time, hours_ahead}
            - bias_corrections: dict of {model: mean_bias_c}
            - corrected_ensemble_c: bias-corrected ensemble (Celsius)
            - corrected_ensemble_f: bias-corrected ensemble (Fahrenheit)
            - model_count: number of models
            
            None if tracker DB not available or no data for location/date
        """
        if not self.available:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            
            # Get latest forecasts for target date
            # Only take most recent forecast_time (freshest data)
            forecasts = conn.execute('''
                SELECT model, temp_max, forecast_time, hours_ahead
                FROM forecasts
                WHERE target_date = ? AND location = ?
                  AND forecast_time = (
                      SELECT MAX(forecast_time) 
                      FROM forecasts 
                      WHERE target_date = ? AND location = ?
                  )
                ORDER BY model
            ''', (target_date, location_key, target_date, location_key)).fetchall()
            
            if not forecasts:
                logger.debug("tracker_no_forecasts", location=location_key, date=target_date)
                conn.close()
                return None
            
            # Get model bias data (7-day average error)
            # Only use recent observations (last 7 days)
            # Filter by hours_ahead <= 48 (short-term forecasts only)
            bias_data = conn.execute('''
                SELECT model, AVG(bias) as mean_bias
                FROM model_bias
                WHERE location = ? 
                  AND hours_ahead <= 48
                  AND date >= date('now', '-7 days')
                GROUP BY model
            ''', (location_key,)).fetchall()
            
            conn.close()
            
            # Convert to dicts
            forecast_list = [
                {
                    "model": model,
                    "temp_max_c": temp,
                    "forecast_time": ftime,
                    "hours_ahead": hours
                }
                for model, temp, ftime, hours in forecasts
            ]
            
            bias_corrections = {
                model: bias for model, bias in bias_data
            }
            
            # Apply bias correction to ensemble
            # Subtract known bias from each model's forecast
            corrected_temps = []
            for f in forecast_list:
                model = f["model"]
                temp_c = f["temp_max_c"]
                
                # Subtract known bias (positive bias = model too warm, so subtract)
                bias = bias_corrections.get(model, 0.0)
                corrected_temp = temp_c - bias
                corrected_temps.append(corrected_temp)
            
            # Simple average (tracker already does weighted ensemble)
            if corrected_temps:
                corrected_ensemble_c = sum(corrected_temps) / len(corrected_temps)
                corrected_ensemble_f = corrected_ensemble_c * 9/5 + 32
            else:
                corrected_ensemble_c = None
                corrected_ensemble_f = None
            
            logger.info(
                "tracker_forecast_fetched",
                location=location_key,
                date=target_date,
                model_count=len(forecast_list),
                bias_count=len(bias_corrections),
                corrected_temp_c=round(corrected_ensemble_c, 1) if corrected_ensemble_c else None,
                corrected_temp_f=round(corrected_ensemble_f, 1) if corrected_ensemble_f else None
            )
            
            return {
                "forecasts": forecast_list,
                "bias_corrections": bias_corrections,
                "corrected_ensemble_c": corrected_ensemble_c,
                "corrected_ensemble_f": corrected_ensemble_f,
                "model_count": len(forecast_list),
            }
        
        except Exception as e:
            logger.error("tracker_fetch_failed", location=location_key, error=str(e))
            return None
    
    def get_recent_accuracy(self, location_key: str, days: int = 7) -> Optional[Dict]:
        """
        Get recent forecast accuracy stats for a location.
        
        Args:
            location_key: Location identifier
            days: Number of recent days to analyze
        
        Returns:
            Dict with:
            - mae: Mean Absolute Error (°C)
            - bias: Mean Bias (°C)
            - sample_count: Number of observations
            
            None if tracker DB not available or insufficient data
        """
        if not self.available:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            
            result = conn.execute('''
                SELECT 
                    AVG(ABS(bias)) as mae,
                    AVG(bias) as mean_bias,
                    COUNT(*) as sample_count
                FROM model_bias
                WHERE location = ?
                  AND date >= date('now', '-' || ? || ' days')
                  AND hours_ahead <= 48
            ''', (location_key, days)).fetchone()
            
            conn.close()
            
            if result and result[2] > 0:
                mae, mean_bias, sample_count = result
                logger.info(
                    "tracker_accuracy_computed",
                    location=location_key,
                    mae_c=round(mae, 2),
                    bias_c=round(mean_bias, 2),
                    samples=sample_count
                )
                return {
                    "mae": mae,
                    "bias": mean_bias,
                    "sample_count": sample_count,
                }
            
            return None
        
        except Exception as e:
            logger.error("tracker_accuracy_failed", location=location_key, error=str(e))
            return None
