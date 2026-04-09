"""
Weather Forecast Tracker - Database Helper Functions
Reusable functions for saving data to the database.
"""

import sqlite3
from datetime import datetime
from config import DB_PATH


def get_db_connection():
    """
    Get a database connection with proper configuration.
    Always uses DB_PATH from config to avoid cwd issues.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    # Enable busy timeout for concurrent access
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def save_forecast(conn, model, forecast_time, target_date, hours_ahead, temp_max, location):
    """
    Save a single forecast to the database.
    
    Args:
        conn: SQLite connection object
        model: Model name (e.g., 'ecmwf_ifs025')
        forecast_time: When the forecast was made (datetime or ISO string)
        target_date: Date being forecast (date or ISO string)
        hours_ahead: Hours between forecast_time and target_date
        temp_max: Maximum temperature (float)
        location: Location key (e.g., 'warsaw')
    
    Returns:
        None
    
    Raises:
        sqlite3.Error on database errors
    """
    c = conn.cursor()
    c.execute('''
        INSERT INTO forecasts (model, forecast_time, target_date, hours_ahead, temp_max, location)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (model, forecast_time, target_date, hours_ahead, temp_max, location))


def save_observation(conn, date, temp_max, location):
    """
    Save an actual observation to the database.
    
    Args:
        conn: SQLite connection object
        date: Date of the observation (date or ISO string)
        temp_max: Actual maximum temperature (float)
        location: Location key (e.g., 'warsaw')
    
    Returns:
        bool: True if saved, False if already exists
    
    Raises:
        sqlite3.Error on database errors (except IntegrityError for duplicates)
    """
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO observations (date, temp_max, location)
            VALUES (?, ?, ?)
        ''', (date, temp_max, location))
        return True
    except sqlite3.IntegrityError:
        # Already exists
        return False


def save_model_bias(conn, model, date, hours_ahead, bias, location):
    """
    Save model bias (error) for a specific date.
    
    Args:
        conn: SQLite connection object
        model: Model name
        date: Date of the forecast target
        hours_ahead: Forecast lead time
        bias: Forecast error (forecast - actual)
        location: Location key
    """
    c = conn.cursor()
    c.execute('''
        INSERT INTO model_bias (model, date, hours_ahead, bias, location)
        VALUES (?, ?, ?, ?, ?)
    ''', (model, date, hours_ahead, bias, location))
