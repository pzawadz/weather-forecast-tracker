"""
Risk control system for trading bot.

Implements:
- Circuit breakers (daily loss limits)
- Position limits (per market, total exposure)
- Trade frequency limits
- Simulation mode tracking
"""

from datetime import datetime, date
from typing import Optional, List, Dict
from pathlib import Path
import json
import structlog

logger = structlog.get_logger()


class CircuitBreaker:
    """Circuit breaker - pause trading if daily loss exceeds threshold."""
    
    def __init__(self, daily_loss_limit: float, data_dir: str = "data"):
        """
        Initialize circuit breaker.
        
        Args:
            daily_loss_limit: Max daily loss (negative value, e.g., -50.00)
            data_dir: Directory for trade history
        """
        self.daily_loss_limit = daily_loss_limit
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.data_dir / "circuit_breaker_state.json"
        self.state = self._load_state()
        
        logger.info(
            "circuit_breaker_initialized",
            daily_loss_limit=daily_loss_limit,
            triggered=self.state.get("triggered", False)
        )
    
    def _load_state(self) -> Dict:
        """Load circuit breaker state from file."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "triggered": False,
            "trigger_date": None,
            "trigger_loss": None,
            "daily_pnl": {}
        }
    
    def _save_state(self):
        """Save circuit breaker state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def record_trade(self, pnl: float, trade_date: Optional[date] = None):
        """
        Record trade P&L and check circuit breaker.
        
        Args:
            pnl: Trade profit/loss (positive = profit, negative = loss)
            trade_date: Date of trade (defaults to today)
        
        Returns:
            True if trading should stop, False if OK to continue
        """
        if trade_date is None:
            trade_date = date.today()
        
        date_str = trade_date.isoformat()
        
        # Update daily P&L
        if date_str not in self.state["daily_pnl"]:
            self.state["daily_pnl"][date_str] = 0.0
        
        self.state["daily_pnl"][date_str] += pnl
        
        # Check if breaker should trigger
        daily_total = self.state["daily_pnl"][date_str]
        
        if daily_total <= self.daily_loss_limit and not self.state["triggered"]:
            self.trigger(daily_total)
            self._save_state()
            return True
        
        self._save_state()
        return self.state.get("triggered", False)
    
    def trigger(self, loss: float):
        """Trigger circuit breaker."""
        self.state["triggered"] = True
        self.state["trigger_date"] = date.today().isoformat()
        self.state["trigger_loss"] = loss
        
        logger.error(
            "circuit_breaker_triggered",
            loss=loss,
            limit=self.daily_loss_limit,
            date=self.state["trigger_date"]
        )
    
    def reset(self):
        """Reset circuit breaker (manual intervention required)."""
        old_state = self.state.copy()
        self.state["triggered"] = False
        self.state["trigger_date"] = None
        self.state["trigger_loss"] = None
        self._save_state()
        
        logger.warning(
            "circuit_breaker_reset",
            previous_loss=old_state.get("trigger_loss"),
            previous_date=old_state.get("trigger_date")
        )
    
    def is_triggered(self) -> bool:
        """Check if circuit breaker is triggered."""
        return self.state.get("triggered", False)
    
    def get_daily_pnl(self, trade_date: Optional[date] = None) -> float:
        """Get P&L for a date."""
        if trade_date is None:
            trade_date = date.today()
        
        date_str = trade_date.isoformat()
        return self.state["daily_pnl"].get(date_str, 0.0)


class PositionLimits:
    """Position limits - prevent overexposure."""
    
    def __init__(
        self,
        max_position_per_market: float,
        max_daily_exposure_pct: float,
        bankroll: float,
        data_dir: str = "data"
    ):
        """
        Initialize position limits.
        
        Args:
            max_position_per_market: Max $ in single market
            max_daily_exposure_pct: Max % of bankroll at risk daily (0.0-1.0)
            bankroll: Total bankroll ($)
            data_dir: Directory for position tracking
        """
        self.max_position_per_market = max_position_per_market
        self.max_daily_exposure_pct = max_daily_exposure_pct
        self.bankroll = bankroll
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.positions_file = self.data_dir / "positions.json"
        self.positions = self._load_positions()
        
        logger.info(
            "position_limits_initialized",
            max_per_market=max_position_per_market,
            max_daily_exposure_pct=max_daily_exposure_pct,
            bankroll=bankroll
        )
    
    def _load_positions(self) -> Dict:
        """Load open positions from file."""
        if self.positions_file.exists():
            with open(self.positions_file) as f:
                return json.load(f)
        return {
            "open": {},  # market_id -> position_size
            "daily_exposure": {}  # date -> total_exposure
        }
    
    def _save_positions(self):
        """Save positions to file."""
        with open(self.positions_file, "w") as f:
            json.dump(self.positions, f, indent=2)
    
    def check_can_trade(
        self,
        market_id: str,
        position_size: float,
        trade_date: Optional[date] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if trade is allowed.
        
        Args:
            market_id: Market identifier
            position_size: Proposed position size ($)
            trade_date: Date of trade (defaults to today)
        
        Returns:
            (can_trade, reason)
            - (True, None) if trade allowed
            - (False, "reason") if trade blocked
        """
        if trade_date is None:
            trade_date = date.today()
        
        date_str = trade_date.isoformat()
        
        # Check per-market limit
        current_position = self.positions["open"].get(market_id, 0.0)
        new_position = current_position + position_size
        
        if new_position > self.max_position_per_market:
            return False, f"Position limit exceeded for market {market_id}: ${new_position:.2f} > ${self.max_position_per_market:.2f}"
        
        # Check daily exposure limit
        current_exposure = self.positions["daily_exposure"].get(date_str, 0.0)
        new_exposure = current_exposure + position_size
        max_exposure = self.bankroll * self.max_daily_exposure_pct
        
        if new_exposure > max_exposure:
            return False, f"Daily exposure limit exceeded: ${new_exposure:.2f} > ${max_exposure:.2f} ({self.max_daily_exposure_pct*100:.0f}% of ${self.bankroll:.0f})"
        
        return True, None
    
    def record_trade(
        self,
        market_id: str,
        position_size: float,
        trade_date: Optional[date] = None
    ):
        """
        Record a new trade.
        
        Args:
            market_id: Market identifier
            position_size: Position size ($)
            trade_date: Date of trade (defaults to today)
        """
        if trade_date is None:
            trade_date = date.today()
        
        date_str = trade_date.isoformat()
        
        # Update open position
        if market_id not in self.positions["open"]:
            self.positions["open"][market_id] = 0.0
        
        self.positions["open"][market_id] += position_size
        
        # Update daily exposure
        if date_str not in self.positions["daily_exposure"]:
            self.positions["daily_exposure"][date_str] = 0.0
        
        self.positions["daily_exposure"][date_str] += position_size
        
        self._save_positions()
        
        logger.info(
            "position_recorded",
            market_id=market_id[:12],
            position_size=position_size,
            total_position=self.positions["open"][market_id],
            daily_exposure=self.positions["daily_exposure"][date_str]
        )
    
    def close_position(self, market_id: str):
        """Close a position (market resolved)."""
        if market_id in self.positions["open"]:
            del self.positions["open"][market_id]
            self._save_positions()
            logger.info("position_closed", market_id=market_id[:12])


class TradeFrequencyLimiter:
    """Trade frequency limits - prevent overtrading."""
    
    def __init__(
        self,
        max_trades_per_day: int,
        max_trades_per_scan: int,
        max_trades_per_city: int,
        data_dir: str = "data"
    ):
        """
        Initialize trade frequency limiter.
        
        Args:
            max_trades_per_day: Max total trades per day
            max_trades_per_scan: Max trades per scan cycle
            max_trades_per_city: Max trades per city per day
            data_dir: Directory for trade history
        """
        self.max_trades_per_day = max_trades_per_day
        self.max_trades_per_scan = max_trades_per_scan
        self.max_trades_per_city = max_trades_per_city
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.counts_file = self.data_dir / "trade_counts.json"
        self.counts = self._load_counts()
        
        logger.info(
            "frequency_limiter_initialized",
            max_per_day=max_trades_per_day,
            max_per_scan=max_trades_per_scan,
            max_per_city=max_trades_per_city
        )
    
    def _load_counts(self) -> Dict:
        """Load trade counts from file."""
        if self.counts_file.exists():
            with open(self.counts_file) as f:
                return json.load(f)
        return {
            "daily": {},  # date -> count
            "scan": 0,  # current scan count
            "city_daily": {}  # date -> {city -> count}
        }
    
    def _save_counts(self):
        """Save trade counts to file."""
        with open(self.counts_file, "w") as f:
            json.dump(self.counts, f, indent=2)
    
    def start_scan(self):
        """Start a new scan cycle."""
        self.counts["scan"] = 0
        self._save_counts()
    
    def check_can_trade(
        self,
        city: str,
        trade_date: Optional[date] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if trade is allowed.
        
        Args:
            city: City name (e.g., "warsaw")
            trade_date: Date of trade (defaults to today)
        
        Returns:
            (can_trade, reason)
        """
        if trade_date is None:
            trade_date = date.today()
        
        date_str = trade_date.isoformat()
        
        # Check daily limit
        daily_count = self.counts["daily"].get(date_str, 0)
        if daily_count >= self.max_trades_per_day:
            return False, f"Daily trade limit reached: {daily_count}/{self.max_trades_per_day}"
        
        # Check scan limit
        if self.counts["scan"] >= self.max_trades_per_scan:
            return False, f"Scan trade limit reached: {self.counts['scan']}/{self.max_trades_per_scan}"
        
        # Check city limit
        if date_str not in self.counts["city_daily"]:
            self.counts["city_daily"][date_str] = {}
        
        city_count = self.counts["city_daily"][date_str].get(city, 0)
        if city_count >= self.max_trades_per_city:
            return False, f"City trade limit reached for {city}: {city_count}/{self.max_trades_per_city}"
        
        return True, None
    
    def record_trade(self, city: str, trade_date: Optional[date] = None):
        """Record a trade."""
        if trade_date is None:
            trade_date = date.today()
        
        date_str = trade_date.isoformat()
        
        # Update daily count
        if date_str not in self.counts["daily"]:
            self.counts["daily"][date_str] = 0
        self.counts["daily"][date_str] += 1
        
        # Update scan count
        self.counts["scan"] += 1
        
        # Update city count
        if date_str not in self.counts["city_daily"]:
            self.counts["city_daily"][date_str] = {}
        
        if city not in self.counts["city_daily"][date_str]:
            self.counts["city_daily"][date_str][city] = 0
        
        self.counts["city_daily"][date_str][city] += 1
        
        self._save_counts()
        
        logger.info(
            "trade_counted",
            city=city,
            daily=self.counts["daily"][date_str],
            scan=self.counts["scan"],
            city_daily=self.counts["city_daily"][date_str][city]
        )
