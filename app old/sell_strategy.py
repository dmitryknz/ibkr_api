import threading
import time
import wx
from strategy_monitor import StrategyMonitorFrame

class SellRiseStrategy:
    def __init__(self, ib, contract, quantity, diff, frame):
        self.ib = ib
        self.contract = contract
        self.qty = quantity
        self.diff = diff
        self.frame = frame
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

        # Фаза трейлинга индикативной цены
        while self.active:
            last_price = self.frame.last_price
            if last_price is None:
                time.sleep(0.2)
                continue

            if last_price > max_price:
                max_price = last_price

            self.indic_price = max_price - self.diff
            wx.CallAfter(self.monitor_frame.update_info, self.indic_price, last_price)

            # Как только откат от максимума >= diff — фиксируем трейлинг
            if last_price <= max_price - self.diff:
                break

            time.sleep(0.2)

        # Фаза ожидания пробоя индикативной цены вниз
        while self.active:
            last_price = self.frame.last_price
            wx.CallAfter(self.monitor_frame.update_info, self.indic_price, last_price)
            if last_price is not None and last_price <= self.indic_price:
                self.ib.pending_limit_order = {
                    "action": "SELL",
                    "price": round(self.indic_price, 2),
                    "qty": self.qty,
                    "market_price": round(last_price, 2)
                }
                self.ib.reqIds(1)
                wx.CallAfter(
                    self.monitor_frame.set_message,
                    f"Лимитная заявка SELL выставлена по {self.indic_price:.2f}"
                )
                self.active = False
                break
            time.sleep(0.2)
