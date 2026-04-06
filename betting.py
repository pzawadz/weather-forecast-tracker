#!/usr/bin/env python3
"""
Betting Recommendation Engine for Polymarket temperature bets
"""

import sqlite3
from datetime import datetime, timedelta
import statistics

def get_ensemble_forecast(hours_ahead=None):
    """
    Get ensemble forecast with uncertainty estimation
    If hours_ahead is None, use the most recent forecasts
    Returns: (median_temp, std_dev, confidence_level, models_count)
    """
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    
    if hours_ahead is None:
        # Get most recent forecasts for tomorrow (any hours_ahead)
        c.execute('''
            SELECT DISTINCT model, temp_max
            FROM forecasts
            WHERE target_date = ?
              AND model NOT LIKE 'ENSEMBLE%'
              AND forecast_time = (
                  SELECT MAX(forecast_time) 
                  FROM forecasts 
                  WHERE target_date = ? AND model NOT LIKE 'ENSEMBLE%'
              )
        ''', (tomorrow, tomorrow))
    else:
        # Get forecasts within specified timeframe
        c.execute('''
            SELECT model, temp_max
            FROM forecasts
            WHERE target_date = ?
              AND hours_ahead BETWEEN ? AND ?
              AND model NOT LIKE 'ENSEMBLE%'
            ORDER BY forecast_time DESC
            LIMIT 20
        ''', (tomorrow, hours_ahead - 4, hours_ahead + 4))
    
    forecasts = [row[1] for row in c.fetchall()]
    conn.close()
    
    if not forecasts:
        return None, None, None, 0
    
    median = statistics.median(forecasts)
    std_dev = statistics.stdev(forecasts) if len(forecasts) > 1 else 0.0
    
    # Confidence based on std dev and model count
    if std_dev < 0.5 and len(forecasts) >= 5:
        confidence = "VERY_HIGH"
    elif std_dev < 1.0 and len(forecasts) >= 4:
        confidence = "HIGH"
    elif std_dev < 1.5 and len(forecasts) >= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return median, std_dev, confidence, len(forecasts)


def calculate_bet_probability(threshold_temp, forecast_temp, std_dev):
    """
    Calculate probability that actual temp will be above threshold
    Using normal distribution assumption
    
    P(actual > threshold) = ?
    """
    from math import erf, sqrt
    
    if std_dev == 0:
        # No uncertainty - binary probability
        return 1.0 if forecast_temp > threshold_temp else 0.0
    
    # Z-score: how many std devs is threshold from forecast
    z = (threshold_temp - forecast_temp) / std_dev
    
    # CDF of standard normal distribution
    # P(X > threshold) = 1 - CDF(z) = 1 - 0.5 * (1 + erf(z / sqrt(2)))
    prob_below = 0.5 * (1 + erf(z / sqrt(2)))
    prob_above = 1.0 - prob_below
    
    return prob_above


def recommend_bet(threshold_temp, bet_type="above"):
    """
    Recommend bet sizing based on ensemble forecast
    
    bet_type: "above" or "below" or "between" (for range bets)
    threshold_temp: temperature threshold for bet
    
    Returns recommendation dict
    """
    median, std_dev, confidence, models = get_ensemble_forecast(hours_ahead=None)
    
    if median is None:
        return {
            "status": "NO_DATA",
            "message": "Not enough forecast data yet",
        }
    
    # Calculate probability based on bet type
    if bet_type == "above":
        prob = calculate_bet_probability(threshold_temp, median, std_dev)
    elif bet_type == "below":
        prob = 1.0 - calculate_bet_probability(threshold_temp, median, std_dev)
    else:
        prob = 0.5  # Default for range bets
    
    # Edge calculation (if we have market odds)
    # edge = our_prob - market_prob
    
    # Bet sizing (Kelly criterion)
    # If prob > 0.55 → consider betting
    # If prob > 0.65 → medium bet
    # If prob > 0.75 → large bet
    
    if prob < 0.45:
        action = "BET_NO"
        size = "SMALL" if prob < 0.35 else "MEDIUM" if prob < 0.40 else "LARGE"
    elif prob > 0.55:
        action = "BET_YES"
        size = "SMALL" if prob < 0.65 else "MEDIUM" if prob < 0.75 else "LARGE"
    else:
        action = "SKIP"
        size = "NONE"
    
    return {
        "status": "READY",
        "forecast_median": round(median, 1),
        "uncertainty": round(std_dev, 2),
        "confidence": confidence,
        "models_count": models,
        "threshold": threshold_temp,
        "bet_type": bet_type,
        "probability": round(prob, 3),
        "action": action,
        "bet_size": size,
        "reasoning": f"{prob*100:.1f}% chance temp {bet_type} {threshold_temp}°C (forecast: {median:.1f}±{std_dev:.1f}°C)",
    }


def print_betting_card():
    """Print formatted betting recommendation card"""
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    
    print("\n" + "="*80)
    print(f"💰 POLYMARKET BETTING CARD - Warsaw Temperature")
    print(f"   Target Date: {tomorrow}")
    print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    median, std_dev, confidence, models = get_ensemble_forecast(hours_ahead=None)
    
    if median is None:
        print("\n⚠️  Not enough data yet. Run forecasts first:")
        print("   ./weather_tracker.py forecast")
        return
    
    print(f"\n📊 ENSEMBLE FORECAST")
    print(f"   Median: {median:.1f}°C")
    print(f"   Uncertainty: ±{std_dev:.1f}°C")
    print(f"   Confidence: {confidence}")
    print(f"   Models: {models}")
    
    # Common Polymarket temperature bet thresholds
    thresholds = [8, 10, 12, 15, 18, 20]
    
    print(f"\n💵 BETTING RECOMMENDATIONS")
    print("-"*80)
    print(f"{'Threshold':<12} {'Type':<8} {'Probability':<12} {'Action':<12} {'Size':<10}")
    print("-"*80)
    
    for threshold in thresholds:
        rec_above = recommend_bet(threshold, bet_type="above")
        if rec_above['status'] == "READY":
            prob = rec_above['probability']
            action = rec_above['action']
            size = rec_above['bet_size']
            print(f">{threshold}°C      {'ABOVE':<8} {prob*100:>5.1f}%       {action:<12} {size:<10}")
    
    print("\n" + "="*80)
    print("Legend:")
    print("  BET_YES  = Bet that temperature WILL exceed threshold")
    print("  BET_NO   = Bet that temperature WON'T exceed threshold")
    print("  SKIP     = No edge, don't bet")
    print("  Size: SMALL (2-5% bankroll), MEDIUM (5-10%), LARGE (10-15%)")
    print("="*80)


def main():
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "card":
            print_betting_card()
        
        elif command == "recommend":
            if len(sys.argv) < 4:
                print("Usage: betting.py recommend THRESHOLD TYPE")
                print("Example: betting.py recommend 15 above")
                sys.exit(1)
            
            threshold = float(sys.argv[2])
            bet_type = sys.argv[3]
            
            rec = recommend_bet(threshold, bet_type)
            print(f"\n{rec}\n")
        
        else:
            print("Usage: betting.py [card|recommend]")
            sys.exit(1)
    else:
        # Default: show betting card
        print_betting_card()


if __name__ == "__main__":
    main()
