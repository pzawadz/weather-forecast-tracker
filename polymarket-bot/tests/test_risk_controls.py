"""Unit tests for risk control systems."""

import pytest
from datetime import date
from pathlib import Path
import shutil
from bot.risk_controls import CircuitBreaker, PositionLimits, TradeFrequencyLimiter


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for tests."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    yield str(data_dir)
    # Cleanup
    shutil.rmtree(data_dir)


def test_circuit_breaker_triggers(temp_data_dir):
    """Test circuit breaker triggers on loss."""
    cb = CircuitBreaker(daily_loss_limit=-50.0, data_dir=temp_data_dir)
    
    # Record small losses - should not trigger
    assert not cb.record_trade(-10.0)
    assert not cb.record_trade(-15.0)
    assert not cb.is_triggered()
    
    # Record large loss - should trigger
    assert cb.record_trade(-30.0)  # Total: -55
    assert cb.is_triggered()


def test_circuit_breaker_reset(temp_data_dir):
    """Test circuit breaker can be reset."""
    cb = CircuitBreaker(daily_loss_limit=-50.0, data_dir=temp_data_dir)
    
    cb.record_trade(-60.0)  # Trigger
    assert cb.is_triggered()
    
    cb.reset()
    assert not cb.is_triggered()


def test_position_limits_per_market(temp_data_dir):
    """Test position limit per market."""
    limits = PositionLimits(
        max_position_per_market=10.0,
        max_daily_exposure_pct=0.10,
        bankroll=1000.0,
        data_dir=temp_data_dir
    )
    
    market_id = "market_123"
    
    # First trade OK
    can_trade, reason = limits.check_can_trade(market_id, 5.0)
    assert can_trade
    limits.record_trade(market_id, 5.0)
    
    # Second trade OK (total 9.0)
    can_trade, reason = limits.check_can_trade(market_id, 4.0)
    assert can_trade
    limits.record_trade(market_id, 4.0)
    
    # Third trade exceeds limit (would be 12.0)
    can_trade, reason = limits.check_can_trade(market_id, 3.0)
    assert not can_trade
    assert "Position limit exceeded" in reason


def test_position_limits_daily_exposure(temp_data_dir):
    """Test daily exposure limit."""
    limits = PositionLimits(
        max_position_per_market=50.0,
        max_daily_exposure_pct=0.10,  # 10% of $1000 = $100
        bankroll=1000.0,
        data_dir=temp_data_dir
    )
    
    # Can trade up to $100 total exposure
    can_trade, _ = limits.check_can_trade("market_1", 50.0)
    assert can_trade
    limits.record_trade("market_1", 50.0)
    
    can_trade, _ = limits.check_can_trade("market_2", 40.0)
    assert can_trade
    limits.record_trade("market_2", 40.0)
    
    # Total now $90, next trade would be $110
    can_trade, reason = limits.check_can_trade("market_3", 20.0)
    assert not can_trade
    assert "Daily exposure limit exceeded" in reason


def test_trade_frequency_daily_limit(temp_data_dir):
    """Test daily trade frequency limit."""
    limiter = TradeFrequencyLimiter(
        max_trades_per_day=5,
        max_trades_per_scan=20,  # High enough to not interfere
        max_trades_per_city=10,
        data_dir=temp_data_dir
    )
    
    limiter.start_scan()
    
    # Can trade up to 5 times
    for i in range(5):
        can_trade, _ = limiter.check_can_trade(f"city_{i}")
        assert can_trade
        limiter.record_trade(f"city_{i}")
    
    # 6th trade blocked
    can_trade, reason = limiter.check_can_trade("city_6")
    assert not can_trade
    assert "Daily trade limit reached" in reason


def test_trade_frequency_scan_limit(temp_data_dir):
    """Test scan trade frequency limit."""
    limiter = TradeFrequencyLimiter(
        max_trades_per_day=10,
        max_trades_per_scan=3,
        max_trades_per_city=5,
        data_dir=temp_data_dir
    )
    
    limiter.start_scan()
    
    # Can trade up to 3 times per scan
    for i in range(3):
        can_trade, _ = limiter.check_can_trade("city_1")
        assert can_trade
        limiter.record_trade("city_1")
    
    # 4th trade in scan blocked
    can_trade, reason = limiter.check_can_trade("city_1")
    assert not can_trade
    assert "Scan trade limit reached" in reason
    
    # Start new scan - can trade again
    limiter.start_scan()
    can_trade, _ = limiter.check_can_trade("city_1")
    assert can_trade


def test_trade_frequency_city_limit(temp_data_dir):
    """Test city trade frequency limit."""
    limiter = TradeFrequencyLimiter(
        max_trades_per_day=10,
        max_trades_per_scan=10,
        max_trades_per_city=2,
        data_dir=temp_data_dir
    )
    
    limiter.start_scan()
    
    # Can trade 2 times in Warsaw
    can_trade, _ = limiter.check_can_trade("warsaw")
    assert can_trade
    limiter.record_trade("warsaw")
    
    can_trade, _ = limiter.check_can_trade("warsaw")
    assert can_trade
    limiter.record_trade("warsaw")
    
    # 3rd trade in Warsaw blocked
    can_trade, reason = limiter.check_can_trade("warsaw")
    assert not can_trade
    assert "City trade limit reached" in reason
    
    # Can still trade in Berlin
    can_trade, _ = limiter.check_can_trade("berlin")
    assert can_trade


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
