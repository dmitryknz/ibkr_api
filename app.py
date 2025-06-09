import wx, threading, time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from order_utils import create_unh_contract, create_limit_order
from buy_strategy import BuyDipStrategy
from sell_strategy import SellRiseStrategy
from order_log import OrderLogger

class StrategyMonitorFrame(wx.Frame):
    def __init__(self, parent, start_price, init_indic_price, strategy_type="Buy"):
        super().__init__(parent, title=f"{strategy_type}-стратегия", size=(350, 240))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer(4, 2, 10, 10)
        grid.Add(wx.StaticText(panel, label="Стартовая цена:"))
        self.init_price_lbl = wx.StaticText(panel, label=f"{start_price:.2f}" if start_price else "-")
        grid.Add(self.init_price_lbl)

        grid.Add(wx.StaticText(panel, label="Старт индик. цена:"))
        self.init_indic_lbl = wx.StaticText(panel, label=f"{init_indic_price:.2f}" if init_indic_price else "-")
        grid.Add(self.init_indic_lbl)

        grid.Add(wx.StaticText(panel, label="Текущая индик. цена:"))
        self.indic_lbl = wx.StaticText(panel, label="-")
        grid.Add(self.indic_lbl)

        grid.Add(wx.StaticText(panel, label="Текущая цена:"))
        self.market_lbl = wx.StaticText(panel, label="-")
        grid.Add(self.market_lbl)

        sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 15)

        self.msg_lbl = wx.StaticText(panel, label="")
        sizer.Add(self.msg_lbl, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(sizer)

    def update_info(self, cur_indic, cur_market):
        # Use wx.CallAfter to ensure UI updates happen on the main thread
        def do_update():
            # Check widgets are still valid before updating
            if hasattr(self, "indic_lbl") and self.indic_lbl:
                try:
                    self.indic_lbl.SetLabel(f"{cur_indic:.2f}" if cur_indic is not None else "-")
                except RuntimeError:
                    pass  # Widget likely deleted, ignore update
            if hasattr(self, "market_lbl") and self.market_lbl:
                try:
                    self.market_lbl.SetLabel(f"{cur_market:.2f}" if cur_market is not None else "-")
                except RuntimeError:
                    pass

        wx.CallAfter(do_update)

    def set_message(self, msg):
        # Use wx.CallAfter for thread safety
        wx.CallAfter(self._set_message, msg)

    def _set_message(self, msg):
        if hasattr(self, "msg_lbl") and self.msg_lbl:
            try:
                self.msg_lbl.SetLabel(msg)
            except RuntimeError:
                pass

class IBapi(EWrapper, EClient):
    def __init__(self, frame):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.frame = frame
        self.pending_limit_order = None

    def nextValidId(self, orderId: int):
        if self.pending_limit_order:
            p = self.pending_limit_order
            order = create_limit_order(action=p["action"], quantity=p["qty"], price=p["price"])
            self.placeOrder(orderId, create_unh_contract(), order)
            self.frame.logger.add_entry(
                order_id=orderId,
                symbol="UNH",
                market_price=p["market_price"],
                ind_start=p["price"],
                side=p["action"]
            )
            self.pending_limit_order = None
        else:
            self.frame.place_pending_market(orderId)

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4 and price > 0:
            self.frame.last_price = price
            wx.CallAfter(self.frame.update_price, price)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        wx.CallAfter(self.frame.logger.update_entry, orderId, final_price=avgFillPrice)
        wx.CallAfter(self.frame.show_message,
                     f"Ордер {orderId}: {status}, исполнено {filled}, цена {avgFillPrice}")

    def error(self, reqId, errorTime, errorCode, errorMsg, advancedOrderRejectJson=None):
        print(f"Error: {reqId}, {errorTime}, {errorCode}, {errorMsg}, {advancedOrderRejectJson}")

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="UNH — стратегии + лог")
        pnl = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(pnl, label="UNH")
        fnt = title.GetFont()
        fnt.MakeBold()
        fnt.PointSize += 6
        title.SetFont(fnt)
        main.Add(title, 0, wx.TOP | wx.CENTER, 10)

        # Порт подключения
        port_row = wx.BoxSizer(wx.HORIZONTAL)
        port_label = wx.StaticText(pnl, label="Порт:")
        self.port_input = wx.TextCtrl(pnl, value="7497", size=(70, -1))
        port_row.Add(port_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        port_row.Add(self.port_input, 0, wx.ALL, 5)
        main.Add(port_row, 0, wx.CENTER)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_connect = wx.Button(pnl, label="Подключиться и подписаться")
        self.price_lbl = wx.StaticText(pnl, label="Цена: -")
        row1.Add(self.btn_connect, 0, wx.ALL | wx.CENTER, 5)
        row1.Add(self.price_lbl, 0, wx.ALL | wx.CENTER, 5)
        main.Add(row1, 0, wx.CENTER)

        qty_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_qty = wx.Button(pnl, label="Стандартный размер заявки")
        self.qty_in = wx.TextCtrl(pnl, value="1", size=(60, -1))
        qty_row.Add(self.btn_qty, 0, wx.ALL, 5)
        qty_row.Add(self.qty_in, 0, wx.ALL, 5)
        main.Add(qty_row, 0, wx.CENTER)

        row_buy = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_set_diff_buy = wx.Button(pnl, label="Задать Δ (Buy)")
        self.diff_buy_in = wx.TextCtrl(pnl, value="1.0", size=(60, -1))
        self.diff_buy_lbl = wx.StaticText(pnl, label="Buy-Δ = 1.0")
        row_buy.Add(self.btn_set_diff_buy, 0, wx.ALL, 5)
        row_buy.Add(self.diff_buy_in, 0, wx.ALL, 5)
        row_buy.Add(self.diff_buy_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        main.Add(row_buy, 0, wx.CENTER)

        row_sell = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_set_diff_sell = wx.Button(pnl, label="Задать Δ (Sell)")
        self.diff_sell_in = wx.TextCtrl(pnl, value="1.5", size=(60, -1))
        self.diff_sell_lbl = wx.StaticText(pnl, label="Sell-Δ = 1.5")
        row_sell.Add(self.btn_set_diff_sell, 0, wx.ALL, 5)
        row_sell.Add(self.diff_sell_in, 0, wx.ALL, 5)
        row_sell.Add(self.diff_sell_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        main.Add(row_sell, 0, wx.CENTER)

        trade = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_buy = wx.Button(pnl, label="Купить UNH", size=(180, 60))
        self.btn_buy.SetBackgroundColour(wx.Colour(0, 200, 0))
        self.btn_sell = wx.Button(pnl, label="Продать UNH", size=(180, 60))
        self.btn_sell.SetBackgroundColour(wx.Colour(200, 0, 0))
        trade.Add(self.btn_buy, 0, wx.ALL, 10)
        trade.AddStretchSpacer()
        trade.Add(self.btn_sell, 0, wx.ALL, 10)
        main.Add(trade, 0, wx.EXPAND)

        self.btn_cancel_all = wx.Button(pnl, label="Отменить все заявки")
        main.Add(self.btn_cancel_all, 0, wx.ALL | wx.CENTER, 10)

        self.logger = OrderLogger(pnl)
        main.Add(self.logger.get_ctrl(), 1, wx.EXPAND | wx.ALL, 10)

        pnl.SetSizer(main)

        self.ib = IBapi(self)
        self.default_qty = 1
        self.diff_buy = 1.0
        self.diff_sell = 1.5
        self.pending_market_action = None
        self.awaiting_market = False
        self.last_price = None
        self.strategy_buy = None
        self.strategy_sell = None

        self.btn_connect.Bind(wx.EVT_BUTTON, self.subscribe_price)
        self.btn_qty.Bind(wx.EVT_BUTTON, self.set_qty)
        self.btn_set_diff_buy.Bind(wx.EVT_BUTTON, self.set_diff_buy)
        self.btn_set_diff_sell.Bind(wx.EVT_BUTTON, self.set_diff_sell)
        self.btn_buy.Bind(wx.EVT_BUTTON, self.run_buy_strategy)
        self.btn_sell.Bind(wx.EVT_BUTTON, self.run_sell_strategy)
        self.btn_cancel_all.Bind(wx.EVT_BUTTON, self.cancel_all_orders)

        self.Show()

    def connect_ib(self):
        if not self.ib.isConnected():
            try:
                port = int(self.port_input.GetValue())
            except ValueError:
                self.show_message("Некорректный порт. Введите число.")
                return
            self.ib.connect("127.0.0.1", port, clientId=20)
            threading.Thread(target=self.ib.run, daemon=True).start()
            time.sleep(1)

    def subscribe_price(self, _):
        self.connect_ib()
        self.ib.reqMktData(1, create_unh_contract(), "", False, False, [])

    def set_qty(self, _):
        try:
            q = int(self.qty_in.GetValue())
            if q <= 0:
                raise ValueError
            self.default_qty = q
            self.show_message(f"Размер заявки = {q}")
        except ValueError:
            self.show_message("Введите положительное целое")

    def set_diff_buy(self, _):
        self._set_diff(self.diff_buy_in, "buy")

    def set_diff_sell(self, _):
        self._set_diff(self.diff_sell_in, "sell")

    def _set_diff(self, ctrl, which):
        try:
            d = float(ctrl.GetValue())
            if d <= 0:
                raise ValueError
            if which == "buy":
                self.diff_buy = d
                self.diff_buy_lbl.SetLabel(f"Buy-Δ = {d}")
            else:
                self.diff_sell = d
                self.diff_sell_lbl.SetLabel(f"Sell-Δ = {d}")
            self.show_message(f"{which.capitalize()}-Δ установлена: {d}")
        except ValueError:
            self.show_message("Введите положительное число")

    def prepare_market_order(self, action):
        self.connect_ib()
        self.pending_market_action = action
        self.awaiting_market = True
        self.ib.reqIds(1)

    def place_pending_market(self, order_id):
        if not self.awaiting_market:
            return
        order = create_limit_order(self.pending_market_action, self.default_qty)
        self.ib.placeOrder(order_id, create_unh_contract(), order)
        self.awaiting_market = False

    def run_buy_strategy(self, _):
        if self.strategy_buy and self.strategy_buy.active:
            self.show_message("Buy-стратегия уже запущена")
            return
        self.connect_ib()
        qty = self.default_qty
        diff = self.diff_buy
        start_price = self.last_price
        self.strategy_buy = BuyDipStrategy(
            ib=self.ib,
            contract=create_unh_contract(),
            quantity=qty,
            diff=diff,
            frame=self,
        )
        msg = (
            f"Buy-стратегия запущена.\n"
            f"Текущая цена: {start_price if start_price is not None else '-'}\n"
            f"Δ: {diff}\n"
            f"Объём: {qty}"
        )
        self.show_message(msg)

    def run_sell_strategy(self, _):
        if self.strategy_sell and self.strategy_sell.active:
            self.show_message("Sell-стратегия уже запущена")
            return
        self.connect_ib()
        qty = self.default_qty
        diff = self.diff_sell
        start_price = self.last_price
        self.strategy_sell = SellRiseStrategy(
            ib=self.ib,
            contract=create_unh_contract(),
            quantity=qty,
            diff=diff,
            frame=self,
        )
        msg = (
            f"Sell-стратегия запущена.\n"
            f"Текущая цена: {start_price if start_price is not None else '-'}\n"
            f"Δ: {diff}\n"
            f"Объём: {qty}"
        )
        self.show_message(msg)

    def cancel_all_orders(self, _):
        if not self.ib.isConnected():
            self.show_message("Нет подключения к IBKR")
            return
        self.ib.reqGlobalCancel()
        self.show_message("Отменены все активные заявки (через API)")
        if self.strategy_buy:
            self.strategy_buy.active = False
        if self.strategy_sell:
            self.strategy_sell.active = False

    def update_price(self, p):
        self.price_lbl.SetLabel(f"Цена: {p:.2f}")

    def show_message(self, txt):
        wx.MessageBox(txt, "Информация")

if __name__ == "__main__":
    app = wx.App()
    MyFrame()
    app.MainLoop()