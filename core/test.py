from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time

class TestApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        print("[INFO] nextValidId received")

        contract = Contract()
        contract.symbol = "UNH"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        order = Order()
        order.action = "SELL"
        order.orderType = "LMT"
        order.totalQuantity = 1
        order.lmtPrice = 300.00
        order.account = "U16306752"  # ← Укажи свой точный IB Account ID
        order.transmit = True

        print("[INFO] Sending order...")
        self.placeOrder(orderId, contract, order)

    def error(self, reqId, errorTime, errorCode, errorMsg, advancedOrderRejectJson=None):
        print(f"[ERROR] {errorCode}: {errorMsg}")


def run_loop(app):
    app.run()

if __name__ == '__main__':
    app = TestApp()
    app.connect("127.0.0.1", 7496, clientId=0)  # clientId = 0 критично

    thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    thread.start()

    time.sleep(5)
    app.disconnect()