import threading
import time
import wx
from strategy_monitor import StrategyMonitorFrame
from order_utils import create_unh_contract, create_limit_order

class SellRiseStrategy:
    def __init__(self, ib, quantity, diff, frame, logger):
        self.ib = ib
        self.qty = quantity
        self.diff = diff
        self.frame = frame
        self.logger = logger
        self.active = True
        self.last_price = frame.last_price
        self.indic_price = None
        self.monitor_frame = StrategyMonitorFrame(
            None, self.last_price, self.last_price - self.diff if self.last_price else None, "Sell"
        )
        self.monitor_frame.Show()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        max_price = self.last_price

        while self.active:
            last_price = self.frame.last_price
            if last_price is None:
                time.sleep(0.2)
                continue

            if last_price > max_price:
                max_price = last_price

            self.indic_price = max_price - self.diff
            wx.CallAfter(self.monitor_frame.update_info, self.indic_price, last_price)

            if last_price <= max_price - self.diff:
                break
            time.sleep(0.2)

        while self.active:
            last_price = self.frame.last_price
            wx.CallAfter(self.monitor_frame.update_info, self.indic_price, last_price)
            if last_price is not None and last_price <= self.indic_price:
                contract = create_unh_contract()
                order = create_limit_order("SELL", self.qty, round(self.indic_price, 2))
                trade = self.ib.placeOrder(contract, order)
                self.logger.add_entry(order.orderId, "UNH", self.qty, "SELL", last_price, self.indic_price, "pending")
                wx.CallAfter(
                    self.monitor_frame.set_message,
                    f"Лимитная заявка SELL выставлена по {self.indic_price:.2f}"
                )
                self.active = False
                break
            time.sleep(0.2)
