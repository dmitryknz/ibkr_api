
from ibapi.contract import Contract
from ibapi.order import Order

def create_unh_contract():
    contract = Contract()
    contract.symbol = "UNH"
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    return contract

def create_limit_order(action="BUY", quantity=1, price=None, account="U16306752"):
    order = Order()
    order.action = action
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = price if price else 0.01  # default dummy price
    order.account = account
    order.transmit = True
    return order
