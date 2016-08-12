""" test SOR_AULitDualPost algo.


split order into ASXC, CXAD, SIGMX (either plutus or X3 based on symbol configuraiton.


use trading_tech_common
go
select * from om_preferences
--where preferenceValue = 'SGMX'
go


venue dual posting: SYDE,CHIA with maq


test cases:

    new order 0.3 * qty > 2 * maq, make sure enought qty to be posted to CHIA.
        70% qty post to SYDE
        30% qty post to CHIA


"""
import gevent
import random
from pprint import pprint
from itertools import chain,groupby
import math
import re
import pytest
from datetime import datetime,timedelta
import numpy as np

from utils import (
                  tickSize,
                  halfTick,
                  get_passive_price,
                  opposite_side,
                  getPegOrderType,
                  PegType,
                  active_wait,
                  )
from clientOrderId import clientOrderId
from om2Order import Order
from conf import settings

def query_child_orders(test_order):
    """ helper for query child orders."""
    gevent.sleep(2)
    child_orders = []
    for child in test_order._childs:
        child_order = test_order.requestOrderImage(child)
        child_orders.append(child_order)
    return child_orders

def validate_child_order_qtys(test_order, parent_qty):
    """ check child order qtys in 70/30 split."""

    assert parent_qty == test_order._data['qty']
    ## validate child order status, qty
    child_orders = query_child_orders(test_order)

    ##  child order qty evently splitted.
    child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
    child_order_qtys = [(o['orderInstructionData']['executionPointOverride'], o['orderInstructionData']['quantity']) \
            for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]

    ## must sorted before group by
    child_order_qtys = sorted(child_order_qtys)
    ## group child order qtys by exchange
    child_qtys_grouped = [(k,sum(j for i, j in group)) for k,group in groupby(child_order_qtys,key=lambda x:x[0])]

    ## 2/3 in asx, 1/3 in chia
    child_qtys = dict(child_qtys_grouped)
    assert 'SYDE' in child_qtys
    assert 'CHIA' in child_qtys

    assert child_qtys['SYDE'] + child_qtys['CHIA'] == parent_qty

    assert abs(child_qtys['SYDE']/parent_qty - 7/10.0) < 0.001
    assert abs(child_qtys['CHIA']/parent_qty - 3/10.0) < 0.001
    #############################################


class Test_AULit_DuPost:

    scenarios = []

    for crosstype in (True,False):
        for side in settings.TEST_SIDES:
            scenarios.append({'cross':crosstype,
                              'side': side}
                              )

    def test_new_amend_cancel_on_OPEN_OkToCross(self,side,cross,symbol_depth):
        """ order basic - new/amend/cancel .

        validate:
            - new order qty equally split into working childs.
            - amend order qty up, qty equally split into working childs.
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## default symbol mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        factor = 3
        qty = random.randint(500,1000) * factor + factor * mxq
        order = dict(symbol = symbol,
                     side   = side,
                     price  = price,
                     qty    = qty,
                     xref   = 'FC2',
                     maq    = mxq,
                     )
        if cross:
            order['extra'] = {'crossConsent': 'OkToCross'}

        order.update(settings.DARK_ORDER_TYPES['audupost'])

        test_order = Order(**order)
        clOrdId,_ = test_order.new()
        active_wait(lambda: test_order._childs == 2)
        print("====== order =========")
        pprint(test_order)

        assert len(test_order._childs) == 2
        validate_child_order_qtys(test_order,qty)

        #############################################
        ## amend qty down 
        test_order.amend(qty=qty+100)
        validate_child_order_qtys(test_order,qty+100)

        #############################################
        ## amend qty up, spill more child orders
        test_order.amend(qty=qty + 500)
        validate_child_order_qtys(test_order,qty+500)

        test_order.cancel()
        ## validate child order status completed.

        assert test_order.orderStatus.primaryStatus == "Complete"

