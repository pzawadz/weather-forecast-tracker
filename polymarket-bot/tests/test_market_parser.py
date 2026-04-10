"""Unit tests for market question parsing."""

import pytest
from datetime import datetime
from bot.connectors.weather import WeatherConnector


class MockConfig:
    """Mock config for testing."""
    TRACKER_DB_PATH = None


@pytest.fixture
def weather_connector():
    """Create weather connector instance."""
    return WeatherConnector(MockConfig())


def test_parse_warsaw_threshold_fahrenheit(weather_connector):
    """Test parsing Warsaw threshold in Fahrenheit."""
    question = "Will the high temperature in Warsaw exceed 50°F on April 11, 2026?"
    
    parsed = weather_connector.parse_market_question(question)
    
    assert parsed["location"] == "Warsaw"
    assert parsed["threshold"] == 50.0
    assert parsed["temp_unit"] == "F"
    assert parsed["threshold_type"] == "high_temp_f"
    assert parsed["threshold_direction"] == "above"
    assert not parsed["is_range"]


def test_parse_berlin_range_celsius(weather_connector):
    """Test parsing Berlin range in Celsius."""
    question = "Will Berlin's high temperature be between 18-20°C on Apr 11, 2026?"
    
    parsed = weather_connector.parse_market_question(question)
    
    assert parsed["location"] == "Berlin"
    assert parsed["range_low"] == 18.0
    assert parsed["range_high"] == 20.0
    assert parsed["temp_unit"] == "C"
    assert parsed["threshold_type"] == "high_temp_c"
    assert parsed["is_range"]


def test_parse_london_below_celsius(weather_connector):
    """Test parsing London below threshold in Celsius."""
    question = "Will London's high temperature be below 15°C on 2026-04-11?"
    
    parsed = weather_connector.parse_market_question(question)
    
    assert parsed["location"] == "London"
    assert parsed["threshold"] == 15.0
    assert parsed["temp_unit"] == "C"
    assert parsed["threshold_direction"] == "below"
    assert parsed["date"].date() == datetime(2026, 4, 11).date()


def test_parse_nyc_above_fahrenheit(weather_connector):
    """Test parsing NYC above threshold in Fahrenheit."""
    question = "Will NYC's high temperature be above 60°F on April 11?"
    
    parsed = weather_connector.parse_market_question(question)
    
    assert parsed["location"] == "NYC"
    assert parsed["threshold"] == 60.0
    assert parsed["temp_unit"] == "F"
    assert parsed["threshold_direction"] == "above"


def test_parse_temperature_unit_autodetect(weather_connector):
    """Test temperature unit auto-detection based on location."""
    # European city without explicit unit
    q1 = "Will Warsaw temperature exceed 10 on April 11?"
    parsed1 = weather_connector.parse_market_question(q1)
    assert parsed1["temp_unit"] == "C"  # Europe defaults to Celsius
    
    # US city without explicit unit
    q2 = "Will Chicago temperature exceed 50 on April 11?"
    parsed2 = weather_connector.parse_market_question(q2)
    assert parsed2["temp_unit"] == "F"  # US defaults to Fahrenheit


def test_parse_date_formats(weather_connector):
    """Test various date format parsing."""
    # Month name format
    q1 = "Will Warsaw exceed 50°F on April 11, 2026?"
    parsed1 = weather_connector.parse_market_question(q1)
    assert parsed1["date"].date() == datetime(2026, 4, 11).date()
    
    # ISO format
    q2 = "Will Berlin exceed 20°C on 2026-04-11?"
    parsed2 = weather_connector.parse_market_question(q2)
    assert parsed2["date"].date() == datetime(2026, 4, 11).date()


def test_parse_negative_temperatures(weather_connector):
    """Test parsing negative temperatures."""
    question = "Will the temperature in Chicago be below -5°F on Jan 15, 2026?"
    
    parsed = weather_connector.parse_market_question(question)
    
    assert parsed["location"] == "Chicago"
    assert parsed["threshold"] == -5.0
    assert parsed["threshold_direction"] == "below"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
