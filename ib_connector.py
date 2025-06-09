
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.order import Order
from ibapi.contract import Contract
import wx
import logging
import json
from order_utils import create_unh_contract

# Лог в файл
logging.basicConfig(filename="order_submit.log", level=logging.INFO, format="%(asctime)s %(message)s")

class IBapi(EWrapper, EClient):
    def __init__(self, frame):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.frame = frame
        self.pending_limit_order = None
        self.user_id = "U16306752"

    def nextValidId(self, orderId: int):
        if self.pending_limit_order:
            try:
                order = Order()
                order.action = self.pending_limit_order["action"]
                order.orderType = "LMT"
                order.totalQuantity = self.pending_limit_order["qty"]
                order.lmtPrice = self.pending_limit_order["price"]

                contract = create_unh_contract()

                order_details = {
                    "user_id": self.user_id,
                    "order_id": orderId,
                    "action": order.action,
                    "order_type": order.orderType,
                    "quantity": order.totalQuantity,
                    "limit_price": order.lmtPrice,
                    "contract": {
                        "symbol": contract.symbol,
                        "secType": contract.secType,
                        "exchange": contract.exchange,
                        "currency": contract.currency
                    }
                }

                log_msg = f"[ORDER] {json.dumps(order_details, ensure_ascii=False, indent=2)}"
                print(log_msg)
                logging.info(log_msg)

                with open("order_debug.json", "a", encoding="utf-8") as f:
                    json.dump(order_details, f, ensure_ascii=False)
                    f.write("\n")

                self.placeOrder(orderId, contract, order)

                self.frame.log_order(orderId, "UNH", self.pending_limit_order["market_price"],
                                     self.pending_limit_order["price"], self.pending_limit_order["action"])
            except Exception as e:
                logging.exception("Ошибка при формировании и отправке заявки: %s", str(e))

    def tickPrice(self, reqId, tickType, price, attrib):
        try:
            if tickType == 4 and price > 0:
                wx.CallAfter(self.frame.update_price, price)
        except Exception as e:
            logging.exception("Ошибка tickPrice: %s", str(e))

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        try:
            order_status_log = {
                "event": "orderStatus",
                "order_id": orderId,
                "status": status,
                "filled": filled,
                "remaining": remaining,
                "avg_fill_price": avgFillPrice,
                "last_fill_price": lastFillPrice,
                "client_id": clientId
            }
            logging.info(f"[ORDER STATUS] {json.dumps(order_status_log, ensure_ascii=False)}")

            if status in ("Filled", "filled"):
                wx.CallAfter(self.frame.update_order_exec, orderId, avgFillPrice)
        except Exception as e:
            logging.exception("Ошибка orderStatus: %s", str(e))

    def error(self, *args):
        try:
            # Поддержка до 6 аргументов: reqId, errorCode, errorMsg, errorTime, advancedOrderRejectJson
            if len(args) == 6:
                reqId, errorTime, errorCode, errorMsg, advancedOrderRejectJson, _ = args
            elif len(args) == 5:
                reqId, errorTime, errorCode, errorMsg, advancedOrderRejectJson = args
            elif len(args) == 4:
                reqId, errorCode, errorMsg, _ = args
                errorTime = advancedOrderRejectJson = None
            else:
                reqId = errorCode = errorMsg = errorTime = advancedOrderRejectJson = None

            error_log = {
                "event": "error",
                "req_id": reqId,
                "code": errorCode,
                "message": errorMsg
            }
            print(f"Ошибка [{errorCode}]: {errorMsg}")
            logging.error(f"[ERROR] {json.dumps(error_log, ensure_ascii=False)}")

            if hasattr(self.frame, "show_message"):
                wx.CallAfter(self.frame.show_message, f"Ошибка {errorCode}: {errorMsg}")
        except Exception as e:
            logging.exception("Ошибка в обработчике error(): %s", str(e))
