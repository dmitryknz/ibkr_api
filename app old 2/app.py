import wx
from ib_insync import *
from buy_strategy import BuyDipStrategy
from sell_strategy import SellRiseStrategy
from order_log import OrderLogger
from order_utils import create_unh_contract

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="UNH — ib-insync")
        pnl = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        self.ib = IB()
        self.ib.connect('127.0.0.1', 7496, clientId=1)

        self.last_price = 100.0
        self.diff_buy = 1.0
        self.diff_sell = 1.5
        self.default_qty = 1

        # Кнопки и UI
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_buy = wx.Button(pnl, label="Купить UNH")
        self.btn_sell = wx.Button(pnl, label="Продать UNH")
        row.Add(self.btn_buy, 0, wx.ALL, 5)
        row.Add(self.btn_sell, 0, wx.ALL, 5)
        main.Add(row, 0, wx.CENTER)

        # Текущее значение цены
        self.price_lbl = wx.StaticText(pnl, label="Цена: -")
        main.Add(self.price_lbl, 0, wx.ALL | wx.CENTER, 5)

        # Лог
        self.logger = OrderLogger(pnl)
        main.Add(self.logger.get_ctrl(), 0, wx.ALL | wx.EXPAND, 5)

        pnl.SetSizer(main)

        # Подписка на поток котировок (в реальном IB подключении)
        self.ticker = self.ib.reqMktData(create_unh_contract(), "", False, False)
        self.ticker.updateEvent += self.on_price_update

        self.btn_buy.Bind(wx.EVT_BUTTON, self.run_buy_strategy)
        self.btn_sell.Bind(wx.EVT_BUTTON, self.run_sell_strategy)

        self.Show()

    def run_buy_strategy(self, _):
        BuyDipStrategy(self.ib, self.default_qty, self.diff_buy, self, self.logger)

    def run_sell_strategy(self, _):
        SellRiseStrategy(self.ib, self.default_qty, self.diff_sell, self, self.logger)

    def on_price_update(self, ticker):
        if ticker.marketPrice() is not None:
            self.last_price = ticker.marketPrice()
            self.price_lbl.SetLabel(f"Цена: {self.last_price:.2f}")

if __name__ == "__main__":
    app = wx.App()
    MyFrame()
    app.MainLoop()
