from ib_insync import *

def create_unh_contract():
    return Stock('UNH', 'SMART', 'USD')

def create_limit_order(action="BUY", quantity=1, price=0.01):
    return LimitOrder(action, quantity, price)
