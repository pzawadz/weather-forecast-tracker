"""
Bot status dashboard - CLI tool for monitoring bot health.

Usage:
    python -m bot.monitoring.status_dashboard
"""

from datetime import datetime, date
from pathlib import Path
import json
import structlog

logger = structlog.get_logger()


class StatusDashboard:
    """Display bot status information."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize status dashboard."""
        self.data_dir = Path(data_dir)
    
    def get_circuit_breaker_status(self) -> dict:
        """Get circuit breaker status."""
        state_file = self.data_dir / "circuit_breaker_state.json"
        
        if not state_file.exists():
            return {"status": "OK", "triggered": False}
        
        with open(state_file) as f:
            state = json.load(f)
        
        today_pnl = state.get("daily_pnl", {}).get(date.today().isoformat(), 0.0)
        
        return {
            "status": "TRIGGERED" if state.get("triggered") else "OK",
            "triggered": state.get("triggered", False),
            "trigger_date": state.get("trigger_date"),
            "trigger_loss": state.get("trigger_loss"),
            "today_pnl": today_pnl
        }
    
    def get_positions_status(self) -> dict:
        """Get open positions status."""
        positions_file = self.data_dir / "positions.json"
        
        if not positions_file.exists():
            return {"open_positions": 0, "total_exposure": 0.0}
        
        with open(positions_file) as f:
            positions = json.load(f)
        
        open_positions = positions.get("open", {})
        total_exposure = sum(open_positions.values())
        
        today = date.today().isoformat()
        today_exposure = positions.get("daily_exposure", {}).get(today, 0.0)
        
        return {
            "open_positions": len(open_positions),
            "total_exposure": total_exposure,
            "today_exposure": today_exposure,
            "markets": list(open_positions.keys())[:5]  # Show first 5
        }
    
    def get_trade_frequency_status(self) -> dict:
        """Get trade frequency status."""
        counts_file = self.data_dir / "trade_counts.json"
        
        if not counts_file.exists():
            return {"today_trades": 0, "scan_trades": 0}
        
        with open(counts_file) as f:
            counts = json.load(f)
        
        today = date.today().isoformat()
        today_trades = counts.get("daily", {}).get(today, 0)
        scan_trades = counts.get("scan", 0)
        
        city_daily = counts.get("city_daily", {}).get(today, {})
        
        return {
            "today_trades": today_trades,
            "scan_trades": scan_trades,
            "city_trades": city_daily
        }
    
    def get_simulation_status(self) -> dict:
        """Get simulation mode status."""
        sim_dir = self.data_dir / "simulation"
        trades_file = sim_dir / "simulated_trades.jsonl"
        
        if not trades_file.exists():
            return {"mode": "simulation", "total_trades": 0}
        
        # Count trades
        with open(trades_file) as f:
            trades = [json.loads(line) for line in f]
        
        total_trades = len(trades)
        today_trades = [
            t for t in trades
            if t["timestamp"].startswith(date.today().isoformat())
        ]
        
        resolved = [t for t in trades if t["result"] is not None]
        wins = [t for t in resolved if t["result"] == "WIN"]
        
        return {
            "mode": "simulation",
            "total_trades": total_trades,
            "today_trades": len(today_trades),
            "resolved_trades": len(resolved),
            "win_count": len(wins),
            "win_rate": len(wins) / len(resolved) if resolved else 0.0,
            "total_pnl": sum(t["pnl"] for t in resolved if t["pnl"])
        }
    
    def display_status(self):
        """Display full status dashboard."""
        print("="*60)
        print("POLYMARKET BOT - STATUS DASHBOARD")
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Circuit Breaker
        cb_status = self.get_circuit_breaker_status()
        print("🔒 CIRCUIT BREAKER:")
        print(f"  Status: {cb_status['status']}")
        if cb_status['triggered']:
            print(f"  ⚠️  Triggered on: {cb_status['trigger_date']}")
            print(f"  Loss: ${cb_status['trigger_loss']:.2f}")
        else:
            print(f"  Today P&L: ${cb_status['today_pnl']:+.2f}")
        print("")
        
        # Positions
        pos_status = self.get_positions_status()
        print("📊 POSITIONS:")
        print(f"  Open markets: {pos_status['open_positions']}")
        print(f"  Total exposure: ${pos_status['total_exposure']:.2f}")
        print(f"  Today exposure: ${pos_status['today_exposure']:.2f}")
        if pos_status['markets']:
            print(f"  Markets: {', '.join(m[:8] + '...' for m in pos_status['markets'])}")
        print("")
        
        # Trade Frequency
        freq_status = self.get_trade_frequency_status()
        print("📈 TRADE FREQUENCY:")
        print(f"  Today: {freq_status['today_trades']}")
        print(f"  Current scan: {freq_status['scan_trades']}")
        if freq_status['city_trades']:
            print(f"  By city: {freq_status['city_trades']}")
        print("")
        
        # Simulation
        sim_status = self.get_simulation_status()
        print("🎮 SIMULATION MODE:")
        print(f"  Status: {sim_status['mode'].upper()}")
        print(f"  Total trades: {sim_status['total_trades']}")
        print(f"  Today: {sim_status['today_trades']}")
        print(f"  Resolved: {sim_status['resolved_trades']}")
        print(f"  Wins: {sim_status['win_count']} ({sim_status['win_rate']:.1%})")
        print(f"  Total P&L: ${sim_status['total_pnl']:+.2f}")
        print("")
        
        print("="*60)


def main():
    """CLI entry point."""
    dashboard = StatusDashboard()
    dashboard.display_status()


if __name__ == "__main__":
    main()
