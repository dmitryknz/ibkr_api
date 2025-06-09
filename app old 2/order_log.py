import wx
import datetime

class OrderLogger:
    def __init__(self, parent):
        self.orders = []
        self.list_ctrl = wx.ListCtrl(parent, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        for i, col in enumerate([
            "ID", "Тикер", "Дата/Время", "Объём", "Сторона", "Старт. цена", "Индик. цена", "Статус", "Цена исп."]):
            self.list_ctrl.InsertColumn(i, col)
        self.list_ctrl.SetMinSize((850, 120))

    def get_ctrl(self):
        return self.list_ctrl

    def add_entry(self, order_id, symbol, qty, side, market_price, ind_price, status="pending", exec_price=None):
        row = [
            str(order_id),
            symbol,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(qty),
            side,
            f"{market_price:.2f}",
            f"{ind_price:.2f}",
            status,
            f"{exec_price:.2f}" if exec_price else "-"
        ]
        self.orders.append(row)
        idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), row[0])
        for col, val in enumerate(row[1:], 1):
            self.list_ctrl.SetItem(idx, col, val)

    def update_entry(self, order_id, status, exec_price=None):
        for i in range(self.list_ctrl.GetItemCount()):
            if self.list_ctrl.GetItemText(i) == str(order_id):
                self.list_ctrl.SetItem(i, 7, status)
                if exec_price:
                    self.list_ctrl.SetItem(i, 8, f"{exec_price:.2f}")
