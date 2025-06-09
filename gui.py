"""wxPython GUI for interacting with :mod:`ibkr_client`."""

from __future__ import annotations

import datetime
import logging
from typing import List

import wx

from ibkr_client import IBKRClient


TABLE_COLUMNS = [
    "Тикер",
    "Дата",
    "Тип",
    "Цена (рын.)",
    "Индик. нач.",
    "Индик. тек.",
    "Цена исп.",
    "Статус",
]


LOGGER = logging.getLogger(__name__)


class MainFrame(wx.Frame):
    """Main application window."""

    def __init__(self, ibkr: IBKRClient) -> None:
        super().__init__(parent=None, title="UNH — стратегии + лог", size=(850, 700))
        self.ibkr = ibkr
        self.delta_buy = 1.0
        self.delta_sell = 1.5
        self.orders_log: List[List] = []
        self.price: float | str = "-"
        self.init_ui()

        self.ibkr.ib.pendingTickersEvent += self.on_tick_price
        self.ibkr.subscribe_to_market_data()

    def init_ui(self) -> None:
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        font_title = wx.Font(22, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        title = wx.StaticText(panel, label="UNH")
        title.SetFont(font_title)
        vbox.Add(title, 0, wx.ALIGN_CENTER | wx.TOP, 12)

        hbox_conn = wx.BoxSizer(wx.HORIZONTAL)
        hbox_conn.Add(wx.StaticText(panel, label="Порт:"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 6)
        self.port_ctrl = wx.TextCtrl(panel, value="7497", size=(60, -1))
        hbox_conn.Add(self.port_ctrl, 0, wx.RIGHT, 8)
        self.connect_btn = wx.Button(panel, label="Подключиться и подписаться")
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        hbox_conn.Add(self.connect_btn, 0, wx.RIGHT, 10)
        hbox_conn.Add(wx.StaticText(panel, label="Цена:"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        self.price_text = wx.StaticText(panel, label="-")
        hbox_conn.Add(self.price_text, 0, wx.RIGHT, 8)
        vbox.Add(hbox_conn, 0, wx.TOP | wx.LEFT, 8)

        hbox_qty = wx.BoxSizer(wx.HORIZONTAL)
        hbox_qty.Add(
            wx.StaticText(panel, label="Стандартный размер заявки"),
            0,
            wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
            6,
        )
        self.qty_ctrl = wx.TextCtrl(panel, value="1", size=(60, -1))
        hbox_qty.Add(self.qty_ctrl)
        vbox.Add(hbox_qty, 0, wx.TOP | wx.LEFT, 8)

        hbox_dbuy = wx.BoxSizer(wx.HORIZONTAL)
        self.set_delta_buy_btn = wx.Button(panel, label="Задать Δ (Buy)")
        self.set_delta_buy_btn.Bind(wx.EVT_BUTTON, self.on_set_delta_buy)
        hbox_dbuy.Add(self.set_delta_buy_btn, 0, wx.RIGHT, 6)
        self.delta_buy_ctrl = wx.TextCtrl(panel, value="1.0", size=(60, -1))
        hbox_dbuy.Add(self.delta_buy_ctrl, 0, wx.RIGHT, 6)
        self.delta_buy_text = wx.StaticText(panel, label=f"Buy-Δ = {self.delta_buy}")
        hbox_dbuy.Add(self.delta_buy_text)
        vbox.Add(hbox_dbuy, 0, wx.TOP | wx.LEFT, 8)

        hbox_dsell = wx.BoxSizer(wx.HORIZONTAL)
        self.set_delta_sell_btn = wx.Button(panel, label="Задать Δ (Sell)")
        self.set_delta_sell_btn.Bind(wx.EVT_BUTTON, self.on_set_delta_sell)
        hbox_dsell.Add(self.set_delta_sell_btn, 0, wx.RIGHT, 6)
        self.delta_sell_ctrl = wx.TextCtrl(panel, value="1.5", size=(60, -1))
        hbox_dsell.Add(self.delta_sell_ctrl, 0, wx.RIGHT, 6)
        self.delta_sell_text = wx.StaticText(panel, label=f"Sell-Δ = {self.delta_sell}")
        hbox_dsell.Add(self.delta_sell_text)
        vbox.Add(hbox_dsell, 0, wx.TOP | wx.LEFT, 8)

        self.cancel_all_btn = wx.Button(panel, label="Отменить все заявки")
        self.cancel_all_btn.Bind(wx.EVT_BUTTON, self.on_cancel_all)
        vbox.Add(self.cancel_all_btn, 0, wx.TOP | wx.LEFT, 8)

        hbox_trading = wx.BoxSizer(wx.HORIZONTAL)
        self.buy_btn = wx.Button(panel, label="Купить UNH", size=(150, 40))
        self.buy_btn.SetBackgroundColour(wx.Colour(0, 160, 0))
        self.buy_btn.Bind(wx.EVT_BUTTON, self.on_buy)
        hbox_trading.Add(self.buy_btn, 0, wx.RIGHT, 16)
        self.sell_btn = wx.Button(panel, label="Продать UNH", size=(150, 40))
        self.sell_btn.SetBackgroundColour(wx.Colour(180, 0, 0))
        self.sell_btn.Bind(wx.EVT_BUTTON, self.on_sell)
        hbox_trading.Add(self.sell_btn)
        vbox.Add(hbox_trading, 0, wx.TOP | wx.LEFT, 16)

        self.table = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        for idx, col in enumerate(TABLE_COLUMNS):
            self.table.InsertColumn(idx, col, width=100 if idx != 0 else 70)
        vbox.Add(self.table, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(vbox)

    # event handlers -----------------------------------------------------

    def on_tick_price(self, tickers):
        LOGGER.debug("Received tickers event: %s", len(tickers))
        for ticker in tickers:
            LOGGER.debug("Update: %s -> %s", ticker.contract.symbol, ticker.marketPrice())
            if ticker.contract.symbol == "UNH":
                price = ticker.marketPrice()
                if price is not None:
                    self.price = round(price, 2)
                    self.price_text.SetLabel(str(self.price))

    def add_log(self, row: List) -> None:
        self.orders_log.append(row)
        idx = self.table.InsertItem(self.table.GetItemCount(), str(row[0]))
        for i in range(1, len(row)):
            self.table.SetItem(idx, i, str(row[i]))

    def on_connect(self, _event):
        try:
            port = int(self.port_ctrl.GetValue())
            self.ibkr.connect(port=port)
            self.ibkr.subscribe_to_market_data()
            wx.MessageBox("Подключено и подписано!", "OK", wx.OK | wx.ICON_INFORMATION)
        except Exception as exc:  # noqa: BLE001
            wx.MessageBox(f"Ошибка подключения: {exc}", "Ошибка", wx.OK | wx.ICON_ERROR)

    def on_set_delta_buy(self, _event):
        try:
            self.delta_buy = float(self.delta_buy_ctrl.GetValue())
            self.delta_buy_text.SetLabel(f"Buy-Δ = {self.delta_buy}")
        except Exception:  # noqa: BLE001
            wx.MessageBox("Некорректное значение Δ Buy!", "Ошибка", wx.OK | wx.ICON_ERROR)

    def on_set_delta_sell(self, _event):
        try:
            self.delta_sell = float(self.delta_sell_ctrl.GetValue())
            self.delta_sell_text.SetLabel(f"Sell-Δ = {self.delta_sell}")
        except Exception:  # noqa: BLE001
            wx.MessageBox("Некорректное значение Δ Sell!", "Ошибка", wx.OK | wx.ICON_ERROR)

    def on_buy(self, _event):
        if not self.ibkr.connected or not self.ibkr.contract:
            wx.MessageBox("Нет подключения к IB", "Ошибка", wx.OK | wx.ICON_ERROR)
            return
        try:
            qty = int(self.qty_ctrl.GetValue())
            price = self.price
            if price == "-":
                wx.MessageBox("Нет рыночной цены!", "Ошибка", wx.OK | wx.ICON_ERROR)
                return
            order_price = round(float(price) + self.delta_buy, 2)
            self.ibkr.place_order("BUY", qty, order_price)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log([
                "UNH",
                now,
                "Buy",
                round(float(price), 2),
                round(float(price), 2),
                order_price,
                "",
                "Создана",
            ])
        except Exception as exc:  # noqa: BLE001
            wx.MessageBox(f"Ошибка Buy: {exc}", "Ошибка", wx.OK | wx.ICON_ERROR)

    def on_sell(self, _event):
        if not self.ibkr.connected or not self.ibkr.contract:
            wx.MessageBox("Нет подключения к IB", "Ошибка", wx.OK | wx.ICON_ERROR)
            return
        try:
            qty = int(self.qty_ctrl.GetValue())
            price = self.price
            if price == "-":
                wx.MessageBox("Нет рыночной цены!", "Ошибка", wx.OK | wx.ICON_ERROR)
                return
            order_price = round(float(price) - self.delta_sell, 2)
            self.ibkr.place_order("SELL", qty, order_price)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log([
                "UNH",
                now,
                "Sell",
                round(float(price), 2),
                round(float(price), 2),
                order_price,
                "",
                "Создана",
            ])
        except Exception as exc:  # noqa: BLE001
            wx.MessageBox(f"Ошибка Sell: {exc}", "Ошибка", wx.OK | wx.ICON_ERROR)

    def on_cancel_all(self, _event):
        try:
            self.ibkr.cancel_all_orders()
            for i, _ in enumerate(self.orders_log):
                self.orders_log[i][7] = "Отменена"
                self.table.SetItem(i, 7, "Отменена")
        except Exception as exc:  # noqa: BLE001
            wx.MessageBox(f"Ошибка отмены: {exc}", "Ошибка", wx.OK | wx.ICON_ERROR)