"""Unit tests for probability calculation."""

import pytest
from bot.connectors.weather import WeatherConnector


class MockConfig:
    """Mock config for testing."""
    TRACKER_DB_PATH = None


@pytest.fixture
def weather_connector():
    """Create weather connector instance."""
    return WeatherConnector(MockConfig())


def test_probability_above_threshold(weather_connector):
    """Test probability calculation for above threshold."""
    # Forecast: 50°F, sigma: 5°F
    # Threshold: 45°F (1 sigma below forecast)
    # Expected: ~84% probability above (normal CDF)
    
    forecast = {
        "temp_max_f": 50.0,
        "temp_max_c": 10.0,
        "sigma_f": 5.0,
        "sigma_c": 2.8,
    }
    
    prob = weather_connector.calculate_probability(
        forecast=forecast,
        threshold=45.0,
        threshold_type="high_temp_f",
        direction="above"
    )
    
    # Should be around 84% (1 sigma above)
    assert 0.80 <= prob <= 0.88


def test_probability_below_threshold(weather_connector):
    """Test probability calculation for below threshold."""
    # Forecast: 50°F, sigma: 5°F
    # Threshold: 55°F (1 sigma above forecast)
    # Expected: ~84% probability below
    
    forecast = {
        "temp_max_f": 50.0,
        "sigma_f": 5.0,
    }
    
    prob = weather_connector.calculate_probability(
        forecast=forecast,
        threshold=55.0,
        threshold_type="high_temp_f",
        direction="below"
    )
    
    assert 0.80 <= prob <= 0.88


def test_probability_at_forecast(weather_connector):
    """Test probability when threshold equals forecast."""
    # Forecast: 50°F
    # Threshold: 50°F (at forecast)
    # Expected: ~50% probability above
    
    forecast = {
        "temp_max_f": 50.0,
        "sigma_f": 5.0,
    }
    
    prob = weather_connector.calculate_probability(
        forecast=forecast,
        threshold=50.0,
        threshold_type="high_temp_f",
        direction="above"
    )
    
    # Should be close to 50%
    assert 0.48 <= prob <= 0.52


def test_probability_celsius(weather_connector):
    """Test probability calculation in Celsius."""
    forecast = {
        "temp_max_c": 10.0,
        "sigma_c": 2.0,
    }
    
    prob = weather_connector.calculate_probability(
        forecast=forecast,
        threshold=12.0,
        threshold_type="high_temp_c",
        direction="above"
    )
    
    # 12°C is 1 sigma above 10°C
    # P(temp > 12) ~ 16%
    assert 0.14 <= prob <= 0.18


def test_probability_range(weather_connector):
    """Test range probability calculation."""
    # Forecast: 50°F, sigma: 5°F
    # Range: 48-52°F (±0.4 sigma from forecast)
    # Expected: ~31% (within range)
    
    forecast = {
        "temp_max_f": 50.0,
        "sigma_f": 5.0,
    }
    
    prob = weather_connector.calculate_range_probability(
        forecast=forecast,
        range_low=48.0,
        range_high=52.0,
        threshold_type="high_temp_f"
    )
    
    assert 0.28 <= prob <= 0.35


def test_probability_clamping(weather_connector):
    """Test probability is clamped to [0.01, 0.99]."""
    # Very far from threshold → should clamp to 0.01 or 0.99
    
    forecast = {
        "temp_max_f": 50.0,
        "sigma_f": 5.0,
    }
    
    # Far above threshold
    prob_high = weather_connector.calculate_probability(
        forecast=forecast,
        threshold=20.0,  # 6 sigma below
        threshold_type="high_temp_f",
        direction="above"
    )
    assert prob_high == 0.99
    
    # Far below threshold
    prob_low = weather_connector.calculate_probability(
        forecast=forecast,
        threshold=80.0,  # 6 sigma above
        threshold_type="high_temp_f",
        direction="above"
    )
    assert prob_low == 0.01


def test_dynamic_sigma_effect(weather_connector):
    """Test that dynamic sigma affects probability."""
    forecast_low_sigma = {
        "temp_max_f": 50.0,
        "sigma_f": 3.0,  # Low uncertainty (models agree)
    }
    
    forecast_high_sigma = {
        "temp_max_f": 50.0,
        "sigma_f": 7.0,  # High uncertainty (models disagree)
    }
    
    threshold = 55.0
    
    prob_low = weather_connector.calculate_probability(
        forecast=forecast_low_sigma,
        threshold=threshold,
        threshold_type="high_temp_f",
        direction="above"
    )
    
    prob_high = weather_connector.calculate_probability(
        forecast=forecast_high_sigma,
        threshold=threshold,
        threshold_type="high_temp_f",
        direction="above"
    )
    
    # Lower sigma → more confident → lower probability of exceeding
    # (threshold is above forecast)
    assert prob_high > prob_low


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
