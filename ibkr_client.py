from __future__ import annotations

"""IBKR Client logic for connecting and placing orders."""

from ib_insync import IB, LimitOrder, Stock
from ib_insync.util import startLoop
import logging
from typing import Optional


LOGGER = logging.getLogger(__name__)


class IBKRClient:
    """Wrapper around :class:`IB` providing simple order helpers."""

    def __init__(self) -> None:
        self.ib = IB()
        self.contract: Optional[Stock] = None
        self.ticker = None
        self.connected = False

    def connect(
        self,
        port: int = 7497,
        ticker: str = "UNH",
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> None:
        """Connect to the Interactive Brokers client and subscribe to market data."""
        LOGGER.debug("Connecting to IBKR …")
        self.ib.disconnect()
        self.ib.connect("127.0.0.1", port, clientId=1)

        LOGGER.debug("Starting asyncio event loop")
        startLoop()

        self.contract = Stock(ticker, exchange, currency)
        self.contract.primaryExchange = "NYSE"
        LOGGER.debug("Created contract: %s", self.contract)

        self.connected = True
        LOGGER.debug("Connection established")

    def disconnect(self) -> None:
        LOGGER.debug("Disconnecting from IBKR")
        self.ib.disconnect()
        self.connected = False

    def get_market_price(self) -> Optional[float]:
        """Return the current market price if available."""
        if not self.ticker:
            LOGGER.warning("Ticker object not initialized")
            return None
        LOGGER.debug(
            "ticker.bid=%s ticker.ask=%s ticker.last=%s close=%s",
            self.ticker.bid,
            self.ticker.ask,
            self.ticker.last,
            self.ticker.close,
        )
        if self.ticker.last is not None:
            return float(self.ticker.last)
        if self.ticker.bid is not None and self.ticker.ask is not None:
            return (self.ticker.bid + self.ticker.ask) / 2
        if self.ticker.close is not None:
            return float(self.ticker.close)
        LOGGER.warning("All price fields are empty: bid/ask/last/close")
        return None

    def place_order(self, action: str, qty: int, price: float):
        LOGGER.debug("Placing order: %s %s @ %s", action, qty, price)
        order = LimitOrder(action, qty, price)
        return self.ib.placeOrder(self.contract, order)

    def cancel_all_orders(self) -> None:
        LOGGER.debug("Cancelling all orders")
        self.ib.cancelAllOrders()

    def subscribe_to_market_data(self) -> None:
        if not self.contract:
            LOGGER.error("Cannot subscribe: contract is None")
            return
        LOGGER.debug("Subscribing to market data for %s", self.contract.symbol)
        self.ticker = self.ib.reqMktData(
            self.contract, "", snapshot=False, regulatorySnapshot=False
        )
        LOGGER.debug("Subscription done, ticker object: %s", self.ticker)