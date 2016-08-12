""" viking test cases for order.

basic test for Viking
- SYDE/CHIA
- new/amend/cancel
- Day, FAK, FOK
- fill i.e. cross
- peg mid i.e. ASXC, CHIA Mid Peg

"""

import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
from datetime import datetime,timedelta
from conf import settings
from vikingOrder import VikingOrder
from utils import (
                  tickSize,
                  halfTick,
                  get_passive_price,
                  opposite_side,
                  )
import gevent


class Test_VkOrder_Basic:

    """

    """
    scenarios = []

    for exch in (
                "SYDE",
                "CHIA"
                ):
        for side in settings.TEST_SIDES:
                data = dict(exch=exch,side=side)
                scenarios.append(data)

    def test_new_amend_cancel(self,exch,side,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)

        last = quote['last']

        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        order = VikingOrder(exch=exch)

        assert order.new(symbol=symbol,side=side,price=price,qty=109), order._acks

        assert order.amend(qty=209), order._acks

        assert order.amend(qty=309, price=price + tickSize(last,1)), order._acks

        assert order.cancel()

    def test_ioc(self,exch,side,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        order = VikingOrder(exch=exch)

        assert order.new(symbol=symbol,side=side,price=price,qty=109,tif="ImmediateOrCancel",allOrNone=False), order._acks

        assert order.cancel() == False

        assert "VikingDoneForDay" in order.acks, order.acks

    def test_fak(self,exch,side,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)

        last = quote['last']
        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        order = VikingOrder(exch=exch)

        assert order.new(symbol=symbol,side=side,price=price,qty=109,tif="ImmediateOrCancel",allOrNone=True), order._acks

        assert order.cancel() == False

        assert "VikingDoneForDay" in order.acks, order.acks


    def test_fill(self,exch,side,symbol_depth):
        """ order fills. """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        last = quote['last']

        other_side = opposite_side(side)

        order = VikingOrder(exch=exch)
        order.new(symbol=symbol,side=side,price=last,qty=100)

        otherOrder = VikingOrder(exch=exch)
        otherOrder.new(symbol=symbol,side=other_side,price=last,qty=1000)

        gevent.sleep(2)
        assert 'VikingExecution' in order.acks
        print order.acks

        ## don't check fail
        otherOrder.cancel()

    def test_peg_mid(self,exch,side,symbol_depth):
        """ peg cp order type """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        last = quote['last']

        ## check price not breach priceStep
        other_side = opposite_side(side)

        ## facil order build spread for CP order
        cl_ord_buy = VikingOrder(exch="SYDE")
        cl_ord_sell = VikingOrder(exch="SYDE")
        cl_ord_buy_2 = VikingOrder(exch="CHIA")
        cl_ord_sell_2 = VikingOrder(exch="CHIA")

        fc_ord_buy = VikingOrder(exch="SYDE")
        fc_ord_sell = VikingOrder(exch="SYDE")
        order = VikingOrder(exch=exch)
        other_order = VikingOrder(exch=exch)

        #import pdb;pdb.set_trace()
        try:
            spread = 5 # 5 tick spread

            ## IOC clear depth for ASX/CXA
            assert cl_ord_buy.new(symbol=symbol,side="Buy",price=last + tickSize(last,spread),qty=50000,tif="ImmediateOrCancel",allOrNone=False) 
            assert cl_ord_sell.new(symbol=symbol,side="Sell",price=last - tickSize(last,spread),qty=50000,tif="ImmediateOrCancel",allOrNone=False) 
            assert cl_ord_buy_2.new(symbol=symbol,side="Buy",price=last + tickSize(last,spread),qty=50000,tif="ImmediateOrCancel",allOrNone=False) 
            assert cl_ord_sell_2.new(symbol=symbol,side="Sell",price=last - tickSize(last,spread),qty=50000,tif="ImmediateOrCancel",allOrNone=False) 
            ## setup depth on asx
            assert fc_ord_buy.new(symbol=symbol,side="Buy",price=last-tickSize(last,spread),qty=1000)
            assert  fc_ord_sell.new(symbol=symbol,side="Sell",price=last + tickSize(last,spread),qty=1000)
            ## test peg order
            qty = random.randint(1000,2000)
            assert order.new(symbol=symbol,side=side,price=last,qty=qty, pegType="Mid"), order._acks
            #assert order.amend(qty=209), order._acks
            #assert order.amend(qty=309, price=last+tickSize(last,1)), order._acks
            assert other_order.new(symbol=symbol,side=other_side,price=last,qty=qty,pegType="Mid"),order._acks

        finally:
            fc_ord_buy.cancel()
            fc_ord_sell.cancel()
            order.cancel()
            other_order.cancel()


class Test_VkOrder_GTCGTD:
    """ """
    scenarios = []

    tifs = ("Day","GoodTillCancelled","GoodTillDate")
    for exch in (
                "SYDE",
                "CHIA"
                ):
        for side in settings.TEST_SIDES:
            for tif in tifs:
                if exch == "CHIA" and tif != "Day": continue
                data = dict(exch=exch,tif=tif,side=side)
                scenarios.append(data)

    def test_new_amend_cancel(self,exch,tif,side,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        last = quote['last']

        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        order_t = {'symbol': symbol,
                   'side': side,
                   'price': price,
                   'qty': random.randint(1000,2000),
                   'tif': tif,
                }

        if tif in ("GoodTillDate","GoodTillTime"):
            if  exch == "SYDE":
                utcnow = datetime.utcnow() + timedelta(days=3)
                order_t['expirationDateTime'] = time.mktime(utcnow.timetuple())
            else:
                utcnow = datetime.utcnow() + timedelta(hours=3)
                order_t['expirationDateTime'] = time.mktime(utcnow.timetuple())

        order = VikingOrder(exch=exch)

        assert order.new(**order_t), order._acks

        assert order.amend(qty=2009), order._acks

        assert order.amend(qty=909, price=price + tickSize(last,1)), order._acks

        assert order.cancel()



