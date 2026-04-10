"""Configuration management for the Polymarket Weather Bot."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Config(BaseSettings):
    """Bot configuration from environment variables."""

    # ============================================================================
    # POLYMARKET AUTHENTICATION
    # ============================================================================
    
    polygon_wallet_private_key: str = Field(..., alias="POLYMARKET_PRIVATE_KEY")
    polymarket_funder_address: Optional[str] = Field(None, alias="POLYMARKET_FUNDER_ADDRESS")
    polymarket_proxy_address: Optional[str] = Field(None, alias="POLYMARKET_PROXY_ADDRESS")

    # ============================================================================
    # WEATHER DATA SOURCE
    # ============================================================================
    
    tracker_db_path: Optional[str] = Field(None, alias="TRACKER_DB_PATH")
    weatherapi_key: Optional[str] = Field(None, alias="WEATHERAPI_KEY")
    default_temp_unit: str = Field("F", alias="DEFAULT_TEMP_UNIT")

    # ============================================================================
    # RISK CONTROLS
    # ============================================================================
    
    simulation_mode: bool = Field(True, alias="SIMULATION_MODE")
    circuit_breaker_daily_loss: float = Field(-50.00, alias="CIRCUIT_BREAKER_DAILY_LOSS")
    max_position_per_market: float = Field(10.00, alias="MAX_POSITION_PER_MARKET")
    max_trades_per_day: int = Field(25, alias="MAX_TRADES_PER_DAY")
    max_trades_per_scan: int = Field(20, alias="MAX_TRADES_PER_SCAN")
    max_single_trade_usd: float = Field(5.00, alias="MAX_SINGLE_TRADE_USD")
    max_daily_exposure_pct: float = Field(0.05, alias="MAX_DAILY_EXPOSURE_PCT")

    # ============================================================================
    # MARKET FILTERS
    # ============================================================================
    
    min_market_liquidity_usd: float = Field(500, alias="MIN_MARKET_LIQUIDITY_USD")
    min_price_cents: int = Field(3, alias="MIN_PRICE_CENTS")
    max_forecast_days: int = Field(5, alias="MAX_FORECAST_DAYS")
    min_model_count: int = Field(3, alias="MIN_MODEL_COUNT")

    # ============================================================================
    # STRATEGY PARAMETERS
    # ============================================================================
    
    base_sigma_f: float = Field(4.0, alias="BASE_SIGMA_F")
    base_sigma_c: float = Field(2.2, alias="BASE_SIGMA_C")
    min_edge: float = Field(0.05, alias="MIN_EDGE")
    
    # Extreme value strategy parameters (from original bot)
    extreme_yes_max_price: float = Field(0.12, alias="EXTREME_YES_MAX_PRICE")
    extreme_yes_min_price: float = Field(0.03, alias="EXTREME_YES_MIN_PRICE")
    extreme_yes_ideal_price: float = Field(0.08, alias="EXTREME_YES_IDEAL_PRICE")
    extreme_no_min_yes_price: float = Field(0.50, alias="EXTREME_NO_MIN_YES_PRICE")
    extreme_no_ideal_yes_price: float = Field(0.60, alias="EXTREME_NO_IDEAL_YES_PRICE")
    extreme_no_min_price: float = Field(0.03, alias="EXTREME_NO_MIN_PRICE")
    extreme_min_position: float = Field(1.50, alias="EXTREME_MIN_POSITION")
    extreme_max_position: float = Field(2.50, alias="EXTREME_MAX_POSITION")
    extreme_aggressive_max: float = Field(5.00, alias="EXTREME_AGGRESSIVE_MAX")

    # ============================================================================
    # MONITORING & ALERTS
    # ============================================================================
    
    telegram_bot_token: Optional[str] = Field(None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, alias="TELEGRAM_CHAT_ID")

    # ============================================================================
    # LOGGING
    # ============================================================================
    
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: str = Field("logs/bot.log", alias="LOG_FILE")

    # ============================================================================
    # ADVANCED SETTINGS
    # ============================================================================
    
    locations_config_path: str = Field("config/locations.json", alias="LOCATIONS_CONFIG_PATH")
    calibration_config_path: str = Field("config/calibration.json", alias="CALIBRATION_CONFIG_PATH")
    db_path: str = Field("data/bot.db", alias="DB_PATH")
    weather_cache_ttl: int = Field(900, alias="WEATHER_CACHE_TTL")
    
    # Bot runner config
    bankroll: float = Field(1000.0, alias="BANKROLL")
    scan_interval_hours: int = Field(4, alias="SCAN_INTERVAL_HOURS")
    max_trades_per_city: int = Field(2, alias="MAX_TRADES_PER_CITY")
    resolution_check_hours: int = Field(1, alias="RESOLUTION_CHECK_HOURS")
    poll_interval_minutes: int = Field(15, alias="POLL_INTERVAL_MINUTES")
    
    # Data storage
    cache_dir: str = Field("./data/cache", alias="CACHE_DIR")
    log_dir: str = Field("./logs", alias="LOG_DIR")

    # ============================================================================
    # POLYMARKET CONSTANTS
    # ============================================================================
    
    clob_url: str = "https://clob.polymarket.com"
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    chain_id: int = 137  # Polygon mainnet
    
    # Contract addresses (Polygon)
    neg_risk_exchange_address: str = "0xC5d563A36AE78145C45a50134d48A1215220f80a"
    ctf_exchange_address: str = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"
    usdc_address: str = "0x3c499c542cEF5E3811e1192ce70d8cc03d5c3359"
    ctf_address: str = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        Path("data").mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode (not simulation)."""
        return not self.simulation_mode

    def validate_required_fields(self) -> list[str]:
        """Validate required configuration fields and return missing ones."""
        missing = []
        
        # Polymarket requires wallet private key
        if not self.polygon_wallet_private_key:
            missing.append("POLYMARKET_PRIVATE_KEY")
        
        return missing


# Global config instance
config = Config()


# Convenience function
def get_config() -> Config:
    """Get the global config instance."""
    return config
