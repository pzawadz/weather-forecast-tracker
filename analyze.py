#!/usr/bin/env python3
"""
Weather Forecast Analysis & Reporting
"""

import sqlite3
from datetime import datetime, timedelta
import json

def get_recent_forecasts(days=7):
    """Get all forecasts and actuals for recent days"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            f.target_date,
            f.model,
            f.hours_ahead,
            f.temp_max as forecast,
            o.temp_max as actual,
            (f.temp_max - o.temp_max) as error
        FROM forecasts f
        LEFT JOIN observations o ON f.target_date = o.date
        WHERE f.target_date >= date('now', '-' || ? || ' days')
        ORDER BY f.target_date DESC, f.hours_ahead DESC, f.model
    ''', (days,))
    
    results = []
    for row in c.fetchall():
        results.append({
            'date': row[0],
            'model': row[1],
            'hours_ahead': row[2],
            'forecast': row[3],
            'actual': row[4],
            'error': row[5]
        })
    
    conn.close()
    return results


def get_model_performance(days=30):
    """Get model performance statistics by forecast horizon"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    # Group by forecast horizon buckets (24h, 20h, 16h, 12h, 8h, 4h)
    horizons = [
        (20, 28, "24h"),
        (16, 24, "20h"),
        (12, 20, "16h"),
        (8, 16, "12h"),
        (4, 12, "8h"),
        (0, 8, "4h"),
    ]
    
    results = {}
    
    for min_h, max_h, label in horizons:
        c.execute('''
            SELECT 
                model,
                COUNT(*) as count,
                AVG(bias) as mean_error,
                AVG(ABS(bias)) as mae,
                SQRT(AVG(bias * bias)) as rmse
            FROM model_bias
            WHERE date >= date('now', '-' || ? || ' days')
              AND hours_ahead >= ? AND hours_ahead < ?
            GROUP BY model
            ORDER BY mae ASC
        ''', (days, min_h, max_h))
        
        results[label] = []
        for row in c.fetchall():
            results[label].append({
                'model': row[0],
                'count': row[1],
                'mean_error': row[2],
                'mae': row[3],
                'rmse': row[4]
            })
    
    conn.close()
    return results


def print_performance_table(horizon_data, horizon_label):
    """Pretty print performance table for a specific horizon"""
    if not horizon_data:
        return
    
    print(f"\n{'='*80}")
    print(f"📊 {horizon_label} Forecast Performance")
    print(f"{'='*80}")
    print(f"{'Model':<30} {'Days':>6} {'Mean Error':>12} {'MAE':>8} {'RMSE':>8}")
    print('-'*80)
    
    for item in horizon_data:
        print(f"{item['model']:<30} {item['count']:>6} "
              f"{item['mean_error']:>+11.2f}°C {item['mae']:>7.2f}° "
              f"{item['rmse']:>7.2f}°")


def print_forecast_evolution(date_str):
    """Show how forecasts evolved for a specific date"""
    conn = sqlite3.connect('weather_forecasts.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            forecast_time,
            hours_ahead,
            model,
            temp_max
        FROM forecasts
        WHERE target_date = ?
        ORDER BY hours_ahead DESC, forecast_time, model
    ''', (date_str,))
    
    # Get actual
    c.execute('SELECT temp_max FROM observations WHERE date = ?', (date_str,))
    actual_row = c.fetchone()
    actual = actual_row[0] if actual_row else None
    
    print(f"\n{'='*90}")
    print(f"📈 Forecast Evolution for {date_str}" + 
          (f" (Actual: {actual:.1f}°C)" if actual else ""))
    print(f"{'='*90}")
    print(f"{'Forecast Time':<20} {'Hours Ahead':>12} {'Model':<30} {'Temp':>8} {'Error':>8}")
    print('-'*90)
    
    for row in c.fetchall():
        forecast_time, hours_ahead, model, temp = row
        error = (temp - actual) if actual else None
        error_str = f"{error:+.1f}°C" if error is not None else "-"
        print(f"{forecast_time:<20} {hours_ahead:>12}h {model:<30} {temp:>7.1f}° {error_str:>8}")
    
    conn.close()


def generate_summary_report(days=7):
    """Generate comprehensive summary report"""
    print("\n" + "="*80)
    print(f"🌤️  WEATHER FORECAST TRACKER - SUMMARY REPORT")
    print(f"    Period: Last {days} days")
    print(f"    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Get performance by horizon
    perf = get_model_performance(days)
    
    for horizon in ['24h', '20h', '16h', '12h', '8h', '4h']:
        if horizon in perf and perf[horizon]:
            print_performance_table(perf[horizon], horizon)
    
    # Get recent forecasts
    forecasts = get_recent_forecasts(days)
    
    if forecasts:
        print(f"\n{'='*80}")
        print(f"📅 Recent Forecasts & Actuals")
        print(f"{'='*80}")
        
        current_date = None
        for f in forecasts:
            if f['date'] != current_date:
                current_date = f['date']
                actual_str = f"{f['actual']:.1f}°C" if f['actual'] else "pending"
                print(f"\n📆 {current_date} (Actual: {actual_str})")
            
            if f['actual'] is not None:
                print(f"   {f['hours_ahead']:3d}h {f['model']:<30} {f['forecast']:>5.1f}°C → "
                      f"error: {f['error']:>+5.1f}°C")
            else:
                print(f"   {f['hours_ahead']:3d}h {f['model']:<30} {f['forecast']:>5.1f}°C")


def main():
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            generate_summary_report(days)
        
        elif command == "evolution":
            if len(sys.argv) < 3:
                print("Usage: analyze.py evolution YYYY-MM-DD")
                sys.exit(1)
            date_str = sys.argv[2]
            print_forecast_evolution(date_str)
        
        else:
            print("Usage: analyze.py [summary|evolution]")
            print("  summary [days]       - Show performance summary (default: 7 days)")
            print("  evolution YYYY-MM-DD - Show forecast evolution for specific date")
            sys.exit(1)
    else:
        # Default: summary
        generate_summary_report(7)


if __name__ == "__main__":
    main()
