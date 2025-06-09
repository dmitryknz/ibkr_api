
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.order import Order
import wx
from order_utils import create_unh_contract


class IBapi(EWrapper, EClient):
    def __init__(self, frame):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.frame = frame
        self.pending_limit_order = None

    def nextValidId(self, orderId: int):
        print("==> nextValidId вызван, orderId:", orderId, "pending_limit_order:", self.pending_limit_order)
        if self.pending_limit_order:
            order = create_limit_order(
                action=self.pending_limit_order["action"],
                quantity=self.pending_limit_order["qty"],
                price=self.pending_limit_order["price"]
            )
            print("Перед отправкой ордера:", vars(order))
            contract = create_unh_contract()
            self.placeOrder(orderId, contract, order)
            self.frame.log_order(orderId, "UNH", self.pending_limit_order["market_price"],
                                 self.pending_limit_order["price"], self.pending_limit_order["action"])

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4 and price > 0:
            wx.CallAfter(self.frame.update_price, price)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        if status in ("Filled", "filled"):
            wx.CallAfter(self.frame.update_order_exec, orderId, avgFillPrice)

    def error(self, reqId, errCode, errString):
        print(f"Ошибка [{errCode}]: {errString}")
        if hasattr(self.frame, "show_message"):
            wx.CallAfter(self.frame.show_message, f"Ошибка {errCode}: {errString}")
