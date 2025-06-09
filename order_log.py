# order_log.py
import wx
from datetime import datetime

class OrderLogger:
    def __init__(self, parent_panel):
        self.list_ctrl = wx.ListCtrl(parent_panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self._init_columns()
        self.rows = {}  # order_id -> row index

    def _init_columns(self):
        headers = [
            "Тикер", "Дата", "Тип", "Цена (рын.)", "Индик. нач", "Индик. тек", "Цена исп.", "Статус"
        ]
        for i, h in enumerate(headers):
            self.list_ctrl.InsertColumn(i, h, width=100 if i > 0 else 60)

    def get_ctrl(self):
        return self.list_ctrl

    def add_entry(self, order_id, symbol, market_price, ind_start, side):
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), symbol)
        self.list_ctrl.SetItem(row, 1, dt)
        self.list_ctrl.SetItem(row, 2, side.upper())  # BUY / SELL
        self.list_ctrl.SetItem(row, 3, f"{market_price:.2f}")
        self.list_ctrl.SetItem(row, 4, f"{ind_start:.2f}")
        self.list_ctrl.SetItem(row, 5, f"{ind_start:.2f}")
        self.list_ctrl.SetItem(row, 6, "-")
        self.list_ctrl.SetItem(row, 7, "Активна")
        self.rows[order_id] = row

    def update_entry(self, order_id, final_price=None, ind_now=None, status="Закрыта"):
        if order_id not in self.rows:
            return
        row = self.rows[order_id]
        if ind_now is not None:
            self.list_ctrl.SetItem(row, 5, f"{ind_now:.2f}")
        if final_price is not None:
            self.list_ctrl.SetItem(row, 6, f"{final_price:.2f}")
        self.list_ctrl.SetItem(row, 7, status)
