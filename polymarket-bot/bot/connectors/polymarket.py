"""
Polymarket connector using official py-clob-client SDK.

Replaces custom CLOB implementation + Web3 with official SDK.
Simpler, more maintainable, fewer bugs.
"""

from typing import Optional, Dict, List
import structlog

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

logger = structlog.get_logger()

POLYMARKET_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon


class PolymarketConnector:
    """Polymarket trading connector using official SDK."""
    
    def __init__(self, private_key: str, funder: Optional[str] = None):
        """
        Initialize Polymarket connector.
        
        Args:
            private_key: Wallet private key (hex string with 0x prefix)
            funder: Optional funder address (defaults to address derived from private_key)
        """
        self.private_key = private_key
        self.funder = funder
        
        try:
            self.client = ClobClient(
                POLYMARKET_HOST,
                key=private_key,
                chain_id=CHAIN_ID,
                funder=funder,
            )
            
            # Derive API credentials from wallet signature
            # This creates or retrieves API key/secret/passphrase
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)
            
            logger.info(
                "polymarket_connected",
                funder=funder or "derived",
                host=POLYMARKET_HOST
            )
        except Exception as e:
            logger.error("polymarket_connection_failed", error=str(e))
            raise
    
    def get_markets(
        self, 
        query: str = "temperature",
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search for markets.
        
        Args:
            query: Search query (e.g., "temperature", "weather", "rain")
            active_only: Only return active (non-resolved) markets
            limit: Maximum number of results
        
        Returns:
            List of market dictionaries with:
            - condition_id: unique market identifier
            - question: market question text
            - tokens: list of outcome tokens (YES/NO)
            - active: whether market is active
            - end_date: market resolution date
            - volume: trading volume (USD)
        """
        try:
            # SDK returns list of markets
            # Note: SDK API may vary, adjust based on actual py-clob-client version
            markets = self.client.get_markets(next_cursor="", query=query)
            
            # Filter by active status if requested
            if active_only:
                markets = [m for m in markets if m.get("active", False)]
            
            # Limit results
            markets = markets[:limit]
            
            logger.info(
                "markets_fetched",
                query=query,
                count=len(markets),
                active_only=active_only
            )
            
            return markets
        
        except Exception as e:
            logger.error("get_markets_failed", query=query, error=str(e))
            return []
    
    def get_orderbook(self, token_id: str) -> Optional[Dict]:
        """
        Get current orderbook for a market outcome token.
        
        Args:
            token_id: Token ID (outcome identifier, YES or NO token)
        
        Returns:
            Orderbook dict with:
            - bids: list of [{price, size}] (buy orders)
            - asks: list of [{price, size}] (sell orders)
            - mid: midpoint price
            - spread: bid-ask spread
            
            None if error
        """
        try:
            book = self.client.get_order_book(token_id)
            
            logger.debug(
                "orderbook_fetched",
                token_id=token_id[:8] + "...",
                mid=book.get("mid"),
                spread=book.get("spread")
            )
            
            return book
        
        except Exception as e:
            logger.error(
                "get_orderbook_failed",
                token_id=token_id[:8] + "...",
                error=str(e)
            )
            return None
    
    def get_midpoint(self, token_id: str) -> Optional[float]:
        """
        Get midpoint price for a token.
        
        Args:
            token_id: Token ID
        
        Returns:
            Midpoint price (0.00 to 1.00), None if error
        """
        book = self.get_orderbook(token_id)
        if book:
            return float(book.get("mid", 0))
        return None
    
    def place_limit_order(
        self, 
        token_id: str, 
        side: str, 
        price: float, 
        size: float
    ) -> Optional[Dict]:
        """
        Place a limit order.
        
        Args:
            token_id: Token ID (outcome to trade)
            side: "BUY" or "SELL"
            price: Limit price (0.01 to 0.99)
            size: Order size in USD
        
        Returns:
            Order result dict with:
            - orderID: unique order identifier
            - status: order status
            - fills: list of fills (if immediately matched)
            
            None if error
        """
        try:
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side,
            )
            
            # Create and sign order
            signed = self.client.create_order(order_args)
            
            # Post order (GTC = Good Till Cancelled)
            result = self.client.post_order(signed, OrderType.GTC)
            
            logger.info(
                "limit_order_placed",
                token_id=token_id[:8] + "...",
                side=side,
                price=price,
                size=size,
                order_id=result.get("orderID", "unknown")[:12] + "..."
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "place_limit_order_failed",
                token_id=token_id[:8] + "...",
                side=side,
                price=price,
                size=size,
                error=str(e)
            )
            return None
    
    def place_market_order(
        self, 
        token_id: str, 
        side: str, 
        amount: float
    ) -> Optional[Dict]:
        """
        Place a market order (FOK - Fill Or Kill).
        
        Market orders use aggressive pricing to ensure immediate fill.
        If can't be filled immediately, order is cancelled.
        
        Args:
            token_id: Token ID
            side: "BUY" or "SELL"
            amount: Order size in USD
        
        Returns:
            Order result dict, None if error
        """
        try:
            # Use aggressive price for market order
            # BUY: willing to pay up to 0.99
            # SELL: willing to accept down to 0.01
            price = 0.99 if side == "BUY" else 0.01
            
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=amount,
                side=side,
            )
            
            signed = self.client.create_order(order_args)
            
            # Post order (FOK = Fill Or Kill, immediate or cancel)
            result = self.client.post_order(signed, OrderType.FOK)
            
            logger.info(
                "market_order_placed",
                token_id=token_id[:8] + "...",
                side=side,
                amount=amount,
                order_id=result.get("orderID", "unknown")[:12] + "..."
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "place_market_order_failed",
                token_id=token_id[:8] + "...",
                side=side,
                amount=amount,
                error=str(e)
            )
            return None
    
    def cancel_order(self, order_id: str) -> Optional[Dict]:
        """
        Cancel a specific order.
        
        Args:
            order_id: Order identifier
        
        Returns:
            Cancellation result dict, None if error
        """
        try:
            result = self.client.cancel(order_id)
            
            logger.info(
                "order_cancelled",
                order_id=order_id[:12] + "..."
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "cancel_order_failed",
                order_id=order_id[:12] + "...",
                error=str(e)
            )
            return None
    
    def cancel_all(self) -> Optional[Dict]:
        """
        Cancel all open orders.
        
        Returns:
            Cancellation result dict, None if error
        """
        try:
            result = self.client.cancel_all()
            
            logger.info("all_orders_cancelled")
            
            return result
        
        except Exception as e:
            logger.error("cancel_all_failed", error=str(e))
            return None
    
    def get_positions(self) -> List[Dict]:
        """
        Get current open positions.
        
        Returns:
            List of position dicts with:
            - token_id: outcome token
            - size: position size
            - cost_basis: average entry price
            - unrealized_pnl: unrealized profit/loss
        """
        try:
            positions = self.client.get_positions()
            
            logger.info(
                "positions_fetched",
                count=len(positions)
            )
            
            return positions
        
        except Exception as e:
            logger.error("get_positions_failed", error=str(e))
            return []
    
    def get_balance(self) -> Optional[float]:
        """
        Get USDC balance.
        
        Returns:
            Balance in USDC, None if error
        """
        try:
            # SDK method for balance (may vary by version)
            balance = self.client.get_balance()
            
            logger.info("balance_fetched", balance_usdc=balance)
            
            return balance
        
        except Exception as e:
            logger.error("get_balance_failed", error=str(e))
            return None
