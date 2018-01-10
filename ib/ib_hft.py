import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
import time

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *
from ibapi.order import *

from lib import util


class IBHftWrapper(wrapper.EWrapper):
    def __init__(self):
        wrapper.EWrapper.__init__(self)

class IBHftClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)



class IBHft(IBHftWrapper, IBHftClient):
    SPEED_RATIO_THRESHOLD = 1.5
    MAX_STORED_SPEEDS = 10

    def __init__(self, test_mode=False):
        IBHftWrapper.__init__(self)
        IBHftClient.__init__(self, wrapper=self)

        # state variables
        self.req_id_to_monitor_map = {}
        self.order_id_to_monitor_map = {}

        # tws variables
        self.current_req_id = 0
        self.current_order_id = None

        # state variables
        self.test_mode = test_mode

        self.connect("127.0.0.1", 7496, 2)

        # Try without calling self.run() ??
        thread = Thread(target = self.run)
        thread.start()
        # self.run()

        self.wait_for_readiness()


    def keyboardInterrupt(self):
        self.clear_all()


    def clear_all(self):
        print("Clearing all...")
        
        for req_id in self.req_id_to_monitor_map.keys():
            self.cancelMktData(req_id)
        time.sleep(5)
        self.disconnect()

        print("Finished clearing.")


    def start_monitoring(self, monitor):
        next_req_id = self.get_next_req_id()
        self.req_id_to_monitor_map[next_req_id] = monitor
        self.request_market_data(next_req_id, monitor.contract)


    def request_market_data(self, req_id, contract):
        self.reqMktData(req_id, contract, "", False, False, [])


    def tickPrice(self, reqId, tickType, price:float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)

        self.req_id_to_monitor_map[reqId].price_change(tickType, price)


    def is_ready(self):
        return self.current_order_id is not None


    def wait_for_readiness(self):
        for i in range(120):
            if self.is_ready():
                break
            else:
                time.sleep(1)
        if self.is_ready():
            print("IB Ready")
        else:
            # raise exception ?
            print("IB was not reported ready after 120 seconds")


    # callback to client.reqIds(-1)
    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        self.current_order_id = orderId

    # App functions
    def get_next_order_id(self):
        self.current_order_id += 1
        return self.current_order_id

    def get_next_req_id(self):
        self.current_req_id += 1
        return self.current_req_id


    # Orders
    def place_order(self, monitor, action, quantity, price, orderId=None):
        order = Order()
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.action = action # "BUY"|"SELL"
        order.lmtPrice = price

        if orderId is None:
            order_id = self.get_next_order_id()
            self.order_id_to_monitor_map[next_order_id] = monitor
        else:
            order_id = orderId

        self.placeOrder(order_id, monitor.contract, order)


    def orderStatus(self, orderId, status, filled,
                    remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId,
                    whyHeld):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, 
                lastFillPrice, clientId, whyHeld)

        self.order_id_to_monitor_map[orderId].order_change(orderId, status, remaining)

    def openOrder(self, orderId, contract, order,
                  orderState):
        super().openOrder(orderId, contract, order, orderState)

        # self.order_id_to_monitor_map[orderId].order_change()


    # Overload methods for test mode
    def reqMktData(self, reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions):
        if self.test_mode:
            # manually call tickPrice
            pass
        else:
            super().reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)

