import time
import wx
from .base_strategy import BaseStrategy

class BuyDipStrategy(BaseStrategy):
    def __init__(self, ib, contract, quantity, diff, frame, start_price=None):
        super().__init__(ib, contract, quantity, diff, frame, "Buy", start_price)

    def _run(self):
        min_price = self.last_price

        # Если указана стартовая цена, ждем ее достижения
        if self.start_price is not None:
            while self.active:
                last_price = self.frame.last_price
                if last_price is None:
                    time.sleep(0.2)
                    continue

                wx.CallAfter(self.monitor_frame.update_info, self.start_price, last_price)
                wx.CallAfter(
                    self.monitor_frame.set_message,
                    f"Ожидание достижения стартовой цены {self.start_price:.2f}"
                )

                if last_price <= self.start_price:
                    min_price = last_price
                    break

                time.sleep(0.2)

        # Фаза трейлинга индикативной цены
        while self.active:
            last_price = self.frame.last_price
            if last_price is None:
                time.sleep(0.2)
                continue

            if last_price < min_price:
                min_price = last_price

            self.indic_price = min_price + self.diff
            wx.CallAfter(self.monitor_frame.update_info, self.indic_price, last_price)

            # Как только рост от минимума >= diff — фиксируем трейлинг
            if last_price >= min_price + self.diff:
                break

            time.sleep(0.2)

        # Фаза ожидания пробоя индикативной цены вверх
        while self.active:
            last_price = self.frame.last_price
            wx.CallAfter(self.monitor_frame.update_info, self.indic_price, last_price)
            if last_price is not None and last_price >= self.indic_price:
                self.ib.pending_limit_order = {
                    "action": "BUY",
                    "price": round(self.indic_price, 2),
                    "qty": self.qty,
                    "market_price": round(last_price, 2)
                }
                self.ib.reqIds(1)
                wx.CallAfter(
                    self.monitor_frame.set_message,
                    f"Лимитная заявка BUY выставлена по {self.indic_price:.2f}"
                )
                self.active = False
                break
            time.sleep(0.2) 