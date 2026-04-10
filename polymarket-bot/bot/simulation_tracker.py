"""
Simulation mode tracker - records "would have" trades.

When SIMULATION_MODE=true, bot doesn't place real trades but tracks:
- What trades would have been placed
- At what prices
- Expected P&L (if market resolves)
- Accuracy of predictions

This allows testing strategy without risk.
"""

from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import json
import structlog

logger = structlog.get_logger()


class SimulationTracker:
    """Track simulated trades for backtesting."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize simulation tracker.
        
        Args:
            data_dir: Directory for simulation logs
        """
        self.data_dir = Path(data_dir) / "simulation"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.trades_file = self.data_dir / "simulated_trades.jsonl"
        self.summary_file = self.data_dir / "simulation_summary.json"
        
        self.session_start = datetime.now()
        self.session_trades = []
        
        logger.info(
            "simulation_tracker_initialized",
            trades_file=str(self.trades_file),
            session_start=self.session_start.isoformat()
        )
    
    def record_trade(
        self,
        market_id: str,
        market_question: str,
        token_id: str,
        side: str,
        price: float,
        size: float,
        edge: float,
        fair_probability: float,
        market_probability: float,
        forecast_temp: float,
        forecast_sigma: float,
        reasoning: str,
        metadata: Optional[Dict] = None
    ):
        """
        Record a simulated trade.
        
        Args:
            market_id: Market identifier
            market_question: Market question text
            token_id: Token ID (YES or NO)
            side: "BUY" or "SELL"
            price: Trade price (0.0-1.0)
            size: Position size ($)
            edge: Calculated edge (fair_prob - market_prob)
            fair_probability: Bot's estimated probability
            market_probability: Market's implied probability
            forecast_temp: Weather forecast temperature
            forecast_sigma: Forecast uncertainty
            reasoning: Trade reasoning
            metadata: Additional metadata
        """
        trade = {
            "timestamp": datetime.now().isoformat(),
            "session_start": self.session_start.isoformat(),
            "market_id": market_id,
            "market_question": market_question,
            "token_id": token_id,
            "side": side,
            "price": price,
            "size": size,
            "edge": edge,
            "fair_probability": fair_probability,
            "market_probability": market_probability,
            "forecast_temp": forecast_temp,
            "forecast_sigma": forecast_sigma,
            "reasoning": reasoning,
            "metadata": metadata or {},
            "result": None,  # Filled in after market resolves
            "pnl": None,  # Filled in after market resolves
        }
        
        # Append to JSONL file
        with open(self.trades_file, "a") as f:
            f.write(json.dumps(trade) + "\n")
        
        # Add to session trades
        self.session_trades.append(trade)
        
        logger.info(
            "simulated_trade_recorded",
            market_id=market_id[:12] + "...",
            side=side,
            price=price,
            size=size,
            edge=f"{edge:.1%}",
            fair_prob=f"{fair_probability:.1%}"
        )
    
    def update_trade_result(
        self,
        market_id: str,
        result: str,
        pnl: float,
        actual_outcome: Optional[str] = None
    ):
        """
        Update trade result after market resolves.
        
        Args:
            market_id: Market identifier
            result: "WIN", "LOSS", or "PUSH"
            pnl: Actual profit/loss
            actual_outcome: Actual market outcome
        """
        # Load all trades
        trades = []
        if self.trades_file.exists():
            with open(self.trades_file) as f:
                trades = [json.loads(line) for line in f]
        
        # Update matching trades
        updated = False
        for trade in trades:
            if trade["market_id"] == market_id and trade["result"] is None:
                trade["result"] = result
                trade["pnl"] = pnl
                trade["actual_outcome"] = actual_outcome
                trade["resolved_at"] = datetime.now().isoformat()
                updated = True
        
        if updated:
            # Rewrite file
            with open(self.trades_file, "w") as f:
                for trade in trades:
                    f.write(json.dumps(trade) + "\n")
            
            logger.info(
                "simulated_trade_resolved",
                market_id=market_id[:12] + "...",
                result=result,
                pnl=pnl
            )
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session trades."""
        if not self.session_trades:
            return {
                "session_start": self.session_start.isoformat(),
                "trade_count": 0,
                "total_exposure": 0.0,
                "avg_edge": 0.0,
                "avg_fair_prob": 0.0,
            }
        
        total_exposure = sum(t["size"] for t in self.session_trades)
        avg_edge = sum(t["edge"] for t in self.session_trades) / len(self.session_trades)
        avg_fair_prob = sum(t["fair_probability"] for t in self.session_trades) / len(self.session_trades)
        
        return {
            "session_start": self.session_start.isoformat(),
            "trade_count": len(self.session_trades),
            "total_exposure": total_exposure,
            "avg_edge": avg_edge,
            "avg_fair_prob": avg_fair_prob,
            "trades": self.session_trades
        }
    
    def get_historical_summary(self, days: Optional[int] = None) -> Dict:
        """
        Get summary of all historical simulated trades.
        
        Args:
            days: Number of recent days to include (None = all)
        
        Returns:
            Summary statistics
        """
        if not self.trades_file.exists():
            return {
                "total_trades": 0,
                "resolved_trades": 0,
                "pending_trades": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
            }
        
        # Load all trades
        with open(self.trades_file) as f:
            trades = [json.loads(line) for line in f]
        
        # Filter by days if specified
        if days:
            cutoff = datetime.now().timestamp() - (days * 86400)
            trades = [
                t for t in trades
                if datetime.fromisoformat(t["timestamp"]).timestamp() >= cutoff
            ]
        
        total_trades = len(trades)
        resolved_trades = [t for t in trades if t["result"] is not None]
        pending_trades = [t for t in trades if t["result"] is None]
        
        wins = [t for t in resolved_trades if t["result"] == "WIN"]
        losses = [t for t in resolved_trades if t["result"] == "LOSS"]
        
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / len(resolved_trades) if resolved_trades else 0.0
        
        total_pnl = sum(t["pnl"] for t in resolved_trades)
        avg_pnl = total_pnl / len(resolved_trades) if resolved_trades else 0.0
        
        return {
            "total_trades": total_trades,
            "resolved_trades": len(resolved_trades),
            "pending_trades": len(pending_trades),
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_edge": sum(t["edge"] for t in trades) / len(trades) if trades else 0.0,
        }
    
    def export_report(self, output_file: Optional[str] = None) -> str:
        """
        Export simulation report.
        
        Args:
            output_file: Output file path (defaults to simulation_report_YYYYMMDD.txt)
        
        Returns:
            Path to exported report
        """
        if output_file is None:
            output_file = self.data_dir / f"simulation_report_{datetime.now().strftime('%Y%m%d')}.txt"
        else:
            output_file = Path(output_file)
        
        session_summary = self.get_session_summary()
        historical_summary = self.get_historical_summary()
        
        report = []
        report.append("=" * 60)
        report.append("POLYMARKET BOT - SIMULATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        report.append("CURRENT SESSION:")
        report.append(f"  Start: {session_summary['session_start']}")
        report.append(f"  Trades: {session_summary['trade_count']}")
        report.append(f"  Total exposure: ${session_summary['total_exposure']:.2f}")
        report.append(f"  Avg edge: {session_summary['avg_edge']:.1%}")
        report.append(f"  Avg fair prob: {session_summary['avg_fair_prob']:.1%}")
        report.append("")
        
        report.append("HISTORICAL PERFORMANCE:")
        report.append(f"  Total trades: {historical_summary['total_trades']}")
        report.append(f"  Resolved: {historical_summary['resolved_trades']}")
        report.append(f"  Pending: {historical_summary['pending_trades']}")
        report.append(f"  Wins: {historical_summary['win_count']}")
        report.append(f"  Losses: {historical_summary['loss_count']}")
        report.append(f"  Win rate: {historical_summary['win_rate']:.1%}")
        report.append(f"  Total P&L: ${historical_summary['total_pnl']:.2f}")
        report.append(f"  Avg P&L per trade: ${historical_summary['avg_pnl']:.2f}")
        report.append(f"  Avg edge: {historical_summary['avg_edge']:.1%}")
        report.append("")
        
        report.append("=" * 60)
        
        with open(output_file, "w") as f:
            f.write("\n".join(report))
        
        logger.info("simulation_report_exported", path=str(output_file))
        
        return str(output_file)
