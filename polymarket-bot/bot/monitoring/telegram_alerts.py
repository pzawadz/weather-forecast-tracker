"""
Telegram alert system for bot monitoring.

Sends notifications for:
- Trades executed
- Markets resolved
- Circuit breaker triggered
- Calibration drift warnings
- Daily summary
"""

import os
from typing import Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

# Optional telegram dependency
try:
    import telegram
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("telegram_not_available", note="Install python-telegram-bot for alerts")


class TelegramAlerter:
    """Send alerts via Telegram bot."""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram alerter.
        
        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Telegram chat ID to send alerts to
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        self.enabled = bool(self.bot_token and self.chat_id and TELEGRAM_AVAILABLE)
        
        if self.enabled:
            self.bot = telegram.Bot(token=self.bot_token)
            logger.info("telegram_alerts_enabled", chat_id=self.chat_id[:4] + "...")
        else:
            self.bot = None
            logger.info("telegram_alerts_disabled", reason="Missing credentials or telegram library")
    
    async def send_alert(self, message: str, parse_mode: str = "Markdown"):
        """
        Send alert message.
        
        Args:
            message: Alert message text
            parse_mode: "Markdown" or "HTML"
        """
        if not self.enabled:
            logger.debug("telegram_alert_skipped", reason="Alerts disabled")
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info("telegram_alert_sent", message_preview=message[:50])
        except Exception as e:
            logger.error("telegram_alert_failed", error=str(e))
    
    async def alert_trade_executed(
        self,
        market_question: str,
        side: str,
        price: float,
        size: float,
        edge: float,
        simulation: bool = True
    ):
        """Alert: Trade executed."""
        emoji = "📊" if simulation else "💰"
        mode = "SIMULATION" if simulation else "LIVE"
        
        message = f"""
{emoji} *Trade {mode}*

Market: {market_question[:80]}...
Side: {side}
Price: ${price:.2f}
Size: ${size:.2f}
Edge: {edge:.1%}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        await self.send_alert(message)
    
    async def alert_market_resolved(
        self,
        market_question: str,
        result: str,
        pnl: float
    ):
        """Alert: Market resolved."""
        emoji = "✅" if result == "WIN" else "❌"
        
        message = f"""
{emoji} *Market Resolved: {result}*

Market: {market_question[:80]}...
P&L: ${pnl:+.2f}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        await self.send_alert(message)
    
    async def alert_circuit_breaker_triggered(self, loss: float, limit: float):
        """Alert: Circuit breaker triggered."""
        message = f"""
🚨 *CIRCUIT BREAKER TRIGGERED*

Daily loss: ${loss:.2f}
Limit: ${limit:.2f}

Trading paused. Manual intervention required.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        await self.send_alert(message)
    
    async def alert_calibration_drift(
        self,
        location: str,
        current_sigma: float,
        recommended_sigma: float,
        drift_pct: float
    ):
        """Alert: Calibration drift detected."""
        message = f"""
⚠️ *Calibration Drift Warning*

Location: {location.upper()}
Current sigma: {current_sigma:.1f}°C
Recommended: {recommended_sigma:.1f}°C
Drift: {drift_pct:+.0f}%

Consider running calibration.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        await self.send_alert(message)
    
    async def alert_daily_summary(
        self,
        trades_count: int,
        win_count: int,
        loss_count: int,
        total_pnl: float,
        win_rate: float,
        simulation: bool = True
    ):
        """Alert: Daily summary."""
        mode = "SIMULATION" if simulation else "LIVE"
        emoji = "📊" if simulation else "💰"
        
        message = f"""
{emoji} *Daily Summary ({mode})*

Trades: {trades_count}
Wins: {win_count}
Losses: {loss_count}
Win rate: {win_rate:.1%}
Total P&L: ${total_pnl:+.2f}

Date: {datetime.now().strftime('%Y-%m-%d')}
"""
        await self.send_alert(message)


# Synchronous wrapper for non-async contexts
class SyncTelegramAlerter:
    """Synchronous wrapper for TelegramAlerter."""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.alerter = TelegramAlerter(bot_token, chat_id)
    
    def send_alert(self, message: str):
        """Send alert (sync)."""
        import asyncio
        asyncio.run(self.alerter.send_alert(message))
    
    def alert_trade_executed(self, **kwargs):
        import asyncio
        asyncio.run(self.alerter.alert_trade_executed(**kwargs))
    
    def alert_market_resolved(self, **kwargs):
        import asyncio
        asyncio.run(self.alerter.alert_market_resolved(**kwargs))
    
    def alert_circuit_breaker_triggered(self, **kwargs):
        import asyncio
        asyncio.run(self.alerter.alert_circuit_breaker_triggered(**kwargs))
    
    def alert_calibration_drift(self, **kwargs):
        import asyncio
        asyncio.run(self.alerter.alert_calibration_drift(**kwargs))
    
    def alert_daily_summary(self, **kwargs):
        import asyncio
        asyncio.run(self.alerter.alert_daily_summary(**kwargs))
