""" OM2 test cases for order.

test limit order basic i.e. new, amend, cancel
test FAK/FOK order
test trade report
test market order reject
test SOR order priority
test stale order reject

test order limit order, FAKFOK, trae report will have RDS test data validated including SI.
RDS test data can either load from sybase or local snapshot data.

"""
import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
import gevent
from datetime import datetime,timedelta
import gevent
from functools import partial
## local scripts
from utils import (
                  tickSize,
                  halfTick,
                  opposite_side,
                  getPegOrderType,
                  PegType,
                  AckFailed,
                  active_wait,
                  )
from clientOrderId import clientOrderId

from om2Order import Order

from conf import settings

class Test_Order_Amend_OrderTyep:

    """ check amend direct order type:

        i.e. from ASXC  -> ASX Limit, will not work.
        - orderAccept ok
        - but amend order still filled in ASXC
    """

    def test_new_amend_cancel(self,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## random side reduce amount of tests
        side = random.choice(settings.TEST_SIDES)
        delta = 1 if side == "Buy" else -1

        # using ticker
        mxq = attrs.get("MINEXECUTABLEQTY")

        print "======= market quote / side ==========="
        print quote, side
        ## lookup reg data

        order = dict(symbol =symbol,
                     side   =side,
                     price  =last,
                     qty    =random.randint(200,300),
                     tif    ="Day",
                     extra = {},
                     )

        order.update(settings.ORDER_TYPES['asxc'])

        test_order = Order(**order)
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        ## amend order  type  no limit
        extra = {'orderType': "Limit"}
        test_order.amend(price=last + tickSize(last,delta),extra=extra)

        #pytest.set_trace()
        order['side'] = opposite_side(order['side'])

        test_order_2 = Order(**order)
        test_order_2.new()

        test_order_2.expect("AttachExecution")
        test_order.expect("AttachExecution")

        assert test_order.fills[0].executionData['executionVenue'] == "SYDE"
        assert test_order.fills[0].executionData['subExecutionPoint'] == "ASXC"

