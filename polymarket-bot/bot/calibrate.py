#!/usr/bin/env python3
"""
Calibration script - weekly sigma recalibration based on actual performance.

Reads forecast accuracy from weather-forecast-tracker DB and updates
config/calibration.json with optimized sigma values.

Usage:
    python -m bot.calibrate
    python -m bot.calibrate --days 30 --min-samples 10
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import structlog

logger = structlog.get_logger()


class Calibrator:
    """Calibrate forecast uncertainty (sigma) based on historical accuracy."""
    
    def __init__(self, tracker_db_path: str, calibration_config_path: str):
        """
        Initialize calibrator.
        
        Args:
            tracker_db_path: Path to weather_forecasts.db
            calibration_config_path: Path to config/calibration.json
        """
        self.tracker_db_path = tracker_db_path
        self.calibration_config_path = calibration_config_path
        
        # Check if tracker DB exists
        if not Path(tracker_db_path).exists():
            raise FileNotFoundError(
                f"Tracker DB not found: {tracker_db_path}\n"
                f"Calibration requires weather-forecast-tracker database."
            )
        
        logger.info(
            "calibrator_initialized",
            tracker_db=tracker_db_path,
            calibration_config=calibration_config_path
        )
    
    def analyze_accuracy(
        self,
        location: str,
        days: int = 30,
        min_samples: int = 7
    ) -> Optional[Dict]:
        """
        Analyze forecast accuracy for a location.
        
        Args:
            location: Location key (e.g., "warsaw")
            days: Number of recent days to analyze
            min_samples: Minimum number of observations required
        
        Returns:
            Dict with:
            - mae_f: Mean Absolute Error (Fahrenheit)
            - mae_c: Mean Absolute Error (Celsius)
            - bias_f: Mean Bias (Fahrenheit)
            - bias_c: Mean Bias (Celsius)
            - std_dev_f: Standard deviation (Fahrenheit)
            - std_dev_c: Standard deviation (Celsius)
            - sample_count: Number of observations
            - recommended_sigma_f: Suggested sigma (Fahrenheit)
            - recommended_sigma_c: Suggested sigma (Celsius)
            
            None if insufficient data
        """
        conn = sqlite3.connect(self.tracker_db_path, timeout=5.0)
        
        # Get forecast errors for recent period
        # Only use 24h ahead forecasts (standard betting window)
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        query = """
            SELECT 
                ABS(bias) as abs_error,
                bias,
                date
            FROM model_bias
            WHERE location = ?
              AND date >= ?
              AND hours_ahead BETWEEN 18 AND 30
            ORDER BY date DESC
        """
        
        results = conn.execute(query, (location, cutoff_date)).fetchall()
        conn.close()
        
        if len(results) < min_samples:
            logger.warning(
                "insufficient_samples",
                location=location,
                samples=len(results),
                required=min_samples
            )
            return None
        
        # Calculate statistics
        abs_errors = [r[0] for r in results]
        biases = [r[1] for r in results]
        
        mae_c = sum(abs_errors) / len(abs_errors)
        bias_c = sum(biases) / len(biases)
        
        # Standard deviation (measure of forecast spread)
        mean_error = sum(biases) / len(biases)
        variance = sum((e - mean_error) ** 2 for e in biases) / len(biases)
        std_dev_c = variance ** 0.5
        
        # Convert to Fahrenheit
        mae_f = mae_c * 1.8
        bias_f = bias_c * 1.8
        std_dev_f = std_dev_c * 1.8
        
        # Recommended sigma = std_dev + safety margin
        # We want to capture ~68% of errors within 1 sigma
        # Add 20% safety margin for model spread
        recommended_sigma_c = std_dev_c * 1.2
        recommended_sigma_f = std_dev_f * 1.2
        
        # Floor at reasonable minimums
        recommended_sigma_c = max(1.5, recommended_sigma_c)
        recommended_sigma_f = max(2.7, recommended_sigma_f)
        
        logger.info(
            "accuracy_analyzed",
            location=location,
            sample_count=len(results),
            mae_c=round(mae_c, 2),
            std_dev_c=round(std_dev_c, 2),
            recommended_sigma_c=round(recommended_sigma_c, 2)
        )
        
        return {
            "mae_f": mae_f,
            "mae_c": mae_c,
            "bias_f": bias_f,
            "bias_c": bias_c,
            "std_dev_f": std_dev_f,
            "std_dev_c": std_dev_c,
            "sample_count": len(results),
            "recommended_sigma_f": recommended_sigma_f,
            "recommended_sigma_c": recommended_sigma_c,
        }
    
    def calibrate_all_locations(
        self,
        days: int = 30,
        min_samples: int = 7
    ) -> Dict[str, Dict]:
        """
        Calibrate sigma for all locations.
        
        Args:
            days: Number of recent days to analyze
            min_samples: Minimum observations required
        
        Returns:
            Dict mapping location to accuracy stats
        """
        # Get all locations from tracker DB
        conn = sqlite3.connect(self.tracker_db_path, timeout=5.0)
        locations = conn.execute(
            "SELECT DISTINCT location FROM observations ORDER BY location"
        ).fetchall()
        conn.close()
        
        locations = [loc[0] for loc in locations]
        
        logger.info("calibrating_locations", count=len(locations), locations=locations)
        
        results = {}
        for location in locations:
            try:
                stats = self.analyze_accuracy(location, days, min_samples)
                if stats:
                    results[location] = stats
            except Exception as e:
                logger.error("calibration_failed", location=location, error=str(e))
        
        return results
    
    def update_calibration_config(
        self,
        location_stats: Dict[str, Dict],
        dry_run: bool = False
    ) -> Dict:
        """
        Update config/calibration.json with new sigma values.
        
        Args:
            location_stats: Dict from calibrate_all_locations()
            dry_run: If True, don't actually write file
        
        Returns:
            Updated config dict
        """
        # Load current config
        with open(self.calibration_config_path) as f:
            config = json.load(f)
        
        # Calculate regional averages
        europe_sigmas = []
        us_sigmas = []
        
        for location, stats in location_stats.items():
            sigma_c = stats["recommended_sigma_c"]
            
            # Determine region (simple heuristic)
            if location in ["warsaw", "berlin", "london", "paris"]:
                europe_sigmas.append(sigma_c)
            else:
                us_sigmas.append(sigma_c)
        
        # Update regional base sigmas
        if europe_sigmas:
            avg_sigma_c = sum(europe_sigmas) / len(europe_sigmas)
            avg_sigma_f = avg_sigma_c * 1.8
            
            old_sigma = config["regions"]["europe"]["base_sigma_c"]
            config["regions"]["europe"]["base_sigma_c"] = round(avg_sigma_c, 1)
            config["regions"]["europe"]["base_sigma_f"] = round(avg_sigma_f, 1)
            
            logger.info(
                "europe_sigma_updated",
                old=old_sigma,
                new=round(avg_sigma_c, 1),
                sample_count=len(europe_sigmas)
            )
        
        if us_sigmas:
            avg_sigma_c = sum(us_sigmas) / len(us_sigmas)
            avg_sigma_f = avg_sigma_c * 1.8
            
            old_sigma = config["regions"]["us"]["base_sigma_c"]
            config["regions"]["us"]["base_sigma_c"] = round(avg_sigma_c, 1)
            config["regions"]["us"]["base_sigma_f"] = round(avg_sigma_f, 1)
            
            logger.info(
                "us_sigma_updated",
                old=old_sigma,
                new=round(avg_sigma_c, 1),
                sample_count=len(us_sigmas)
            )
        
        # Update metadata
        config["version"] = f"{config['version']}.{datetime.now().strftime('%Y%m%d')}"
        config["last_updated"] = datetime.now().isoformat()
        
        # Add calibration stats
        if "calibration_history" not in config:
            config["calibration_history"] = []
        
        config["calibration_history"].append({
            "date": datetime.now().isoformat(),
            "locations_calibrated": list(location_stats.keys()),
            "europe_sigma_c": config["regions"]["europe"]["base_sigma_c"] if europe_sigmas else None,
            "us_sigma_c": config["regions"]["us"]["base_sigma_c"] if us_sigmas else None,
        })
        
        # Keep only last 10 calibrations
        config["calibration_history"] = config["calibration_history"][-10:]
        
        # Write updated config
        if not dry_run:
            with open(self.calibration_config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("calibration_config_updated", path=self.calibration_config_path)
        else:
            logger.info("dry_run_complete", message="Config not written (dry_run=True)")
        
        return config


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calibrate forecast sigma values")
    parser.add_argument(
        "--tracker-db",
        default="../weather_forecasts.db",
        help="Path to weather-forecast-tracker DB"
    )
    parser.add_argument(
        "--config",
        default="config/calibration.json",
        help="Path to calibration config"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of recent days to analyze (default: 30)"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=7,
        help="Minimum observations required (default: 7)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write config file, just show what would change"
    )
    
    args = parser.parse_args()
    
    print("🔧 Polymarket Bot Calibration")
    print("="*60)
    print(f"Tracker DB: {args.tracker_db}")
    print(f"Config: {args.config}")
    print(f"Days: {args.days}")
    print(f"Min samples: {args.min_samples}")
    print(f"Dry run: {args.dry_run}")
    print("")
    
    try:
        # Initialize calibrator
        calibrator = Calibrator(args.tracker_db, args.config)
        
        # Calibrate all locations
        print("📊 Analyzing forecast accuracy...")
        location_stats = calibrator.calibrate_all_locations(args.days, args.min_samples)
        
        if not location_stats:
            print("❌ No locations with sufficient data for calibration")
            print(f"   Need at least {args.min_samples} observations per location")
            sys.exit(1)
        
        # Display results
        print(f"\n✅ Analyzed {len(location_stats)} locations:")
        print("")
        
        for location, stats in location_stats.items():
            print(f"  {location.upper()}:")
            print(f"    Samples: {stats['sample_count']}")
            print(f"    MAE: {stats['mae_c']:.1f}°C / {stats['mae_f']:.1f}°F")
            print(f"    Bias: {stats['bias_c']:.1f}°C / {stats['bias_f']:.1f}°F")
            print(f"    Std Dev: {stats['std_dev_c']:.1f}°C / {stats['std_dev_f']:.1f}°F")
            print(f"    → Recommended sigma: {stats['recommended_sigma_c']:.1f}°C / {stats['recommended_sigma_f']:.1f}°F")
            print("")
        
        # Update config
        print("📝 Updating calibration config...")
        updated_config = calibrator.update_calibration_config(
            location_stats,
            dry_run=args.dry_run
        )
        
        # Display changes
        print("\n🎯 Regional sigma values:")
        print(f"  Europe: {updated_config['regions']['europe']['base_sigma_c']}°C / {updated_config['regions']['europe']['base_sigma_f']}°F")
        print(f"  US: {updated_config['regions']['us']['base_sigma_c']}°C / {updated_config['regions']['us']['base_sigma_f']}°F")
        
        if args.dry_run:
            print("\n⚠️  DRY RUN - config not written")
        else:
            print(f"\n✅ Config updated: {args.config}")
            print(f"   Version: {updated_config['version']}")
        
        print("\n🎉 Calibration complete!")
        
    except Exception as e:
        print(f"\n❌ Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# Note: This file was created 2026-04-10
# Calibration requires at least 7 days of forecast + observation data
# Run weather-forecast-tracker for 7+ days first, then run calibration
# 
# Expected workflow:
# 1. weather_tracker.py forecast-all (daily, cron)
# 2. weather_tracker.py observe-all (daily, cron)
# 3. Wait 7+ days for accuracy data
# 4. python -m bot.calibrate (weekly, manual or cron)
