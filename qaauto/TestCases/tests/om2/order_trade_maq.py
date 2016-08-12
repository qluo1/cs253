""" test order/trade with maq behaviour.

- maq for chia lit IOC, note: ASX/IOC not supported.
- maq for chia dark order type for peg mid/bid/ask
- maq for ASXS/ASXC
- maq for SOR/MinQty
- maq amend for SOR/MinQty i.e. 344

"""

import time
import random
import copy
from pprint import pprint
import pytest
import gevent
from utils import (
              valid_rf_ack,
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              AckFailed,
              )
from om2Order import Order
from utils import DepthStyle
from conf import settings


class Test_Order_Trade_MXQ_Lit:

    """ test lit order FAK/FOK maq order/trade.

    - test available qty below/above maq, FAK/FOC order take/not take liquidity.
    - for CHIA/ASX lit order.
    """

    scenarios = []
    ## below/above maq
    belowMaqs = (True,False)

    for sor in [
                #'asx',  # MAQ/IOC not available in ASX lit
                'chia',
                ]:
        for side in settings.TEST_SIDES:
            for belowMaq in belowMaqs:
                data = dict(sor=sor,side=side,belowMaq=belowMaq)

                scenarios.append(data)

    def test_new_order_mxq_trade(self,side,sor,belowMaq,symbol_depth):

        """ test new order with mxq not traded. """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))

        price = last
        order_t = dict(symbol  = symbol,
                        side   = side,
                        price  = price,
                        qty    = mxq + 100,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )
        ## setup facil order with qty below/above minQty, with fix price at last
        fac_order = order_t.copy()
        fac_order['side'] = opposite_side(side)
        fac_order['price'] = last
        if belowMaq:
            fac_order['qty'] = mxq -1
        else:
            fac_order['qty'] = mxq + 1

        fac_order.update(settings.ORDER_TYPES[sor])

        test_facOrder = Order(**fac_order)
        test_facOrder.new()
        print (" ========== facil order ===========")
        print(test_facOrder)
        test_facOrder.expect_ok()

        ## wait for market quote updated this is CHIA qty become visible.
        gevent.sleep(2)

        order = order_t.copy()
        order['xref'] = random.choice(settings.HOUSE_XREFS)
        ## ioc
        order['tif'] = "ImmediateOrCancel"
        order['allOrNone'] = False
        order.update(settings.ORDER_TYPES[sor])
        ## set maq after set common order attrs
        order['maq'] = mxq

        print ("========== sor order ============")
        ## test sor order
        test_order = Order(**order)
        ##
        test_order.new()
        print(test_order)

        try:
            #pytest.set_trace()
            if belowMaq:
                test_order.expect("AttachExecution",negate=True,wait=1)
                test_facOrder.expect("AttachExecution",negate=True,wait=1)
            else:
                test_order.expect("AttachExecution")
                test_facOrder.expect("AttachExecution")

        finally:
            if test_order.orderStatus.primaryStatus != "Complete":
                test_order.cancel(validate=False)
            if test_facOrder.orderStatus.primaryStatus != "Complete":
                test_facOrder.cancel(validate=False)


class Test_Order_Trade_MXQ_Dark:

    """ test chia dark maq order/trade.

    - test available qty below/above maq, test order take/not take liquidity.
    - for CHIA dark peg order
    """

    scenarios = []
    ## below/above maq
    belowMaqs = (True,False)

    for sor in [
                'chia_mid',
                'chia_bid',
                'chia_ask'
                ]:
        for side in settings.TEST_SIDES:
            for belowMaq in belowMaqs:
                data = dict(sor=sor,side=side,belowMaq=belowMaq)

                scenarios.append(data)

    def test_new_order_mxq_trade(self,side,sor,belowMaq,symbol_depth):

        """ test new order with mxq not traded. """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))

        buyPrice = sellPrice = last

        ## for primary peg order give an aggresive price for facil order
        if side == 'Buy':
            testPrice = last + tickSize(last,1)
            ## primary peg, sell order by aggressive price
            if sor == 'chia_bid':
                facPrice = last - tickSize(last,1)
            else:
                ## market/mid peg
                facPrice = last
        else:
            testPrice = last - tickSize(last,1)
            ## primary peg 
            if sor == 'chia_ask':
                facPrice = last + tickSize(last,1)
            else:
                facPrice = last

        ## setup depth
        order_t = dict(symbol  = symbol,
                        side   = side,
                        price  = testPrice,
                        qty    = mxq + 100,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )
        ## setup facil order with qty below/above minQty, with fix price at last
        fac_order = order_t.copy()
        fac_order['side'] = opposite_side(side)
        fac_order['price'] = facPrice
        if belowMaq:
            fac_order['qty'] = mxq -1
        else:
            fac_order['qty'] = mxq + 1

        fac_order.update(settings.ORDER_TYPES[sor])

        test_facOrder = Order(**fac_order)
        test_facOrder.new()
        print (" ========== facil order ===========")
        print(test_facOrder)
        test_facOrder.expect_ok()

        order = order_t.copy()
        order['xref'] = random.choice(settings.HOUSE_XREFS)
        order.update(settings.ORDER_TYPES[sor])
        ## set maq after set common order attrs
        order['maq'] = mxq

        print ("========== sor order ============")
        ## test sor order
        test_order = Order(**order)
        ##
        test_order.new()
        print(test_order)

        try:
            #pytest.set_trace()
            if belowMaq:
                test_order.expect("AttachExecution",negate=True,wait=1)
                test_facOrder.expect("AttachExecution",negate=True,wait=1)
            else:
                test_order.expect("AttachExecution")
                test_facOrder.expect("AttachExecution")

        finally:
            if test_order.orderStatus.primaryStatus != "Complete":
                test_order.cancel(validate=False)
            if test_facOrder.orderStatus.primaryStatus != "Complete":
                test_facOrder.cancel(validate=False)


class Test_Order_Trade_SOR_MXQ_New:

    """ test new order sor maq order/trade.

    - test available qty below/above maq, test order take/not take liquidity.
    - for CHIA dark liquidity
    - and CHIA lit  liquidity

    """

    scenarios = []
    ## below/above maq
    belowMaqs = (True,False)

    facilTypes = ('chia','chia_mid')

    for sor in [
                'sor4', ## BPMQ
                'sor5', ## BPMQUni
                'sor6', ## BPMQNoLit
                'sor7', ## BPMQNoLitUni
                ]:
        for side in settings.TEST_SIDES:
            for belowMaq in belowMaqs:
                for facilType in facilTypes:
                    data = dict(sor=sor,side=side,belowMaq=belowMaq,facilType=facilType)

                    scenarios.append(data)

    def test_new_order_mxq_trade(self,side,sor,belowMaq,facilType,symbol_depth):

        """ test new sor order with mxq take liquidity above mxq, not hit liquidity below mxq.

        - liquidity available in CXA Dark/Mid
        - liquidity available in CXA lit, NoLit should ignore lit

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))

        price = last
        order_t = dict(symbol  = symbol,
                        side   = side,
                        price  = price,
                        qty    = mxq + 100,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )
        ## setup facil order with qty below/above minQty, with fix price at last
        fac_order = order_t.copy()
        fac_order['side'] = opposite_side(side)
        fac_order['price'] = last
        if belowMaq:
            fac_order['qty'] = mxq -1
        else:
            fac_order['qty'] = mxq + 1

        fac_order.update(settings.ORDER_TYPES[facilType])

        test_facOrder = Order(**fac_order)
        test_facOrder.new()
        print (" ========== facil order ===========")
        print(test_facOrder)
        test_facOrder.expect_ok()

        order = order_t.copy()
        order['xref'] = random.choice(settings.HOUSE_XREFS)
        order.update(settings.ORDER_TYPES[sor])
        ## set maq after update order attrs
        order['maq'] = mxq

        print ("========== sor order ============")
        ## test sor order
        test_order = Order(**order)
        ##
        test_order.new()
        print(test_order)

        try:
            ## nolit sor shouldn't hit CHIA lit order.
            ## for belowMaq or sor6/7/cxa lit available, it shouldn't trade.
            if belowMaq or sor in ('sor6', 'sor7') and facilType == 'chia':
                test_order.expect("AttachExecution",negate=True,wait=1)
                test_facOrder.expect("AttachExecution",negate=True,wait=1)
            else:
                test_order.expect("AttachExecution")
                test_facOrder.expect("AttachExecution")

        finally:
            if test_order.orderStatus.primaryStatus != "Complete":
                test_order.cancel(validate=False)
            if test_facOrder.orderStatus.primaryStatus != "Complete":
                test_facOrder.cancel(validate=False)


class Test_Order_Trade_SOR_MXQ_Amend:

    """ test sor amend maq order/trade.

    - test available qty below/above maq, test order take/not take liquidity.
    - for CHIA dark peg order
    """

    scenarios = []

    facilTypes = ('chia',
                  #'chia_mid',  ## dark liquidity will not be resweep unless amend aggressive
                  )

    for sor in [
                'sor4', ## BPMQ
                'sor5', ## BPMQUni
                'sor6', ## BPMQNoLit
                'sor7', ## BPMQNoLitUni
                ]:
        for side in settings.TEST_SIDES:
            for facilType in facilTypes:
                data = dict(sor=sor,side=side,facilType=facilType)

                scenarios.append(data)


    def test_amend_order_mxq_trade(self,side,sor,facilType,symbol_depth):

        """ test amend sor order with mxq initial below above mxq, amend above mxq
        sor should take out liquidity after mxq being amended.

        - liquidity available in CXA lit,
        - NoLit SOR should ignore lit liquidity.

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))

        price = last
        order_t = dict(symbol  = symbol,
                        side   = side,
                        price  = price,
                        qty    = mxq + 100,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )
        ## setup facil order with qty below/above minQty, with fix price at last
        fac_order = order_t.copy()
        fac_order['side'] = opposite_side(side)
        fac_order['price'] = last
        fac_order['qty'] = mxq + 10

        fac_order.update(settings.ORDER_TYPES[facilType])

        test_facOrder = Order(**fac_order)
        test_facOrder.new()
        print (" ========== facil order ===========")
        print(test_facOrder)
        test_facOrder.expect_ok()

        order = order_t.copy()
        order['xref'] = random.choice(settings.HOUSE_XREFS)
        order.update(settings.ORDER_TYPES[sor])
        ## set maq after update order attrs, maq above available qty
        order['maq'] = mxq + 20
        print ("========== sor order ============")
        ## test sor order
        test_order = Order(**order)
        ##
        test_order.new()
        print(test_order)
        test_order.expect("AttachExecution",negate=True,wait=1)
        test_facOrder.expect("AttachExecution",negate=True,wait=1)

        ## amend order maq below available qty
        test_order.amend(maq=mxq-30)
        print (test_order)
        try:
            ## nolit sor shouldn't hit CHIA lit order.
            ## for belowMaq or sor6/7/cxa lit available, it shouldn't trade.
            if sor in ('sor6', 'sor7') and facilType == 'chia':
                test_order.expect("AttachExecution",negate=True,wait=1)
                test_facOrder.expect("AttachExecution",negate=True,wait=1)
            else:
                test_order.expect("AttachExecution")
                test_facOrder.expect("AttachExecution")

        finally:
            if test_order.orderStatus.primaryStatus != "Complete":
                test_order.cancel(validate=False)
            if test_facOrder.orderStatus.primaryStatus != "Complete":
                test_facOrder.cancel(validate=False)


class Test_Order_Trade_CP_MXQ_New_Amend:

    """ test CP MXQ behave.

    new order :
    - MXQ not trade below MXQ
    - MXQ trade on qty above MXQ

    amend order MXQ/ available qty:
    - new order MXQ not trade below MXQ, amend MXQ up, trade
    - new order MXQ not trade below MXQ, amend test order qty up, traded

    """

    scenarios = []

    for sor in ('asxc','asxs','chia_mid'):
        for side in settings.TEST_SIDES:
            data = dict(sor=sor,side=side)

            scenarios.append(data)

    def test_new_order_below_mxq(self,side,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        maq = mxq

        pprint(quote)

        tags = settings.ORDER_TYPES[sor]

        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =mxq -1,
                   xref   =random.choice(settings.CLIENT_XREFS))

        buy.update(tags)

        sell = copy.deepcopy(buy)
        sell['side'] = opposite_side(side)
        sell['xref'] = random.choice(settings.HOUSE_XREFS)
        if sor == 'asxs':
            sell.update(settings.ORDER_TYPES['asxc'])

        ## buy order with maq
        buy['maq'] = maq
        buy['qty'] = maq + random.randint(100,300)


        order_sell = Order(**sell)
        order_sell.new()
        print "sell: ", order_sell
        order_buy = Order(**buy)
        order_buy.new()
        print "buy: ", order_buy

        order_sell.expect("AttachExecution",negate=True,wait=1)
        order_buy.expect("AttachExecution",negate=True,wait=1)

        print "sold: ", order_sell.fills
        print "bought: ", order_buy.fills
        order_sell.cancel()
        order_buy.cancel()

    def test_new_order_above_mxq(self,side,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        maq = mxq

        tags = settings.ORDER_TYPES[sor]

        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =maq + 1,
                   xref   =random.choice(settings.CLIENT_XREFS))

        buy.update(tags)

        sell = copy.deepcopy(buy)
        sell['side'] = opposite_side(side)
        sell['xref'] = random.choice(settings.HOUSE_XREFS)
        if sor == 'asxs':
            sell.update(settings.ORDER_TYPES['asxc'])

        ## buy order with maq
        buy['maq'] = maq
        buy['qty'] = random.randint(150,160) + maq


        order_sell = Order(**sell)
        order_sell.new()
        print "sell: ", order_sell
        order_buy = Order(**buy)
        order_buy.new()
        print "buy: ", order_buy

        order_sell.expect("AttachExecution")
        order_buy.expect("AttachExecution")
        order_buy.cancel()
        #
        print "sold:", order_sell.fills
        print "bought:", order_buy.fills

    def test_amend_order_mxq(self,side,sor,symbol_depth):
        """  new order below mxq,amend mxq up. """

        if sor == 'asxs':
            pytest.skip("asxs amend mxq will not resweep ASXC")

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        maq = mxq

        tags = settings.ORDER_TYPES[sor]

        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =maq -1,
                   xref   =random.choice(settings.CLIENT_XREFS))

        buy.update(tags)

        sell = copy.deepcopy(buy)
        sell['side'] = opposite_side(side)
        sell['xref'] = random.choice(settings.HOUSE_XREFS)
        if sor == 'asxs':
            sell.update(settings.ORDER_TYPES['asxc'])

        ## buy order with maq
        buy['maq'] = maq
        buy['qty'] = random.randint(150,160) + maq

        order_sell = Order(**sell)
        order_buy = Order(**buy)
        try:
            order_sell.new()
            print "sell: ", order_sell
            order_buy.new()
            print "buy: ", order_buy

            order_sell.expect("AttachExecution",negate=True,wait=1)
            order_buy.expect("AttachExecution",negate=True,wait=1)

            ## amend maq down to match available qty
            order_buy.amend(maq=maq - 1)
            order_buy.expect("AttachExecution")
            order_sell.expect("AttachExecution")
            print "sold: ", order_sell.fills
            print "bought: ", order_buy.fills
        finally:
            order_buy.cancel()
            order_sell.cancel(validate=False)


    def test_new_order_below_mxq_amend_available(self,side,sor,symbol_depth):
        """  new order below mxq,amend available qty up """

        if sor == 'asxs':
            pytest.skip("asxs amend mxq will not resweep ASXC")

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        maq = mxq

        tags = settings.ORDER_TYPES[sor]

        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =maq -1,
                   xref   =random.choice(settings.CLIENT_XREFS))

        buy.update(tags)

        sell = buy.copy()
        sell['side'] = opposite_side(side)
        sell['xref'] = random.choice(settings.HOUSE_XREFS)
        if sor == 'asxs':
            sell.update(settings.ORDER_TYPES['asxc'])

        ## buy order with maq
        buy['maq'] = maq
        buy['qty'] = random.randint(100,200) + maq

        order_buy = Order(**buy)
        order_sell = Order(**sell)
        try:
            order_sell.new()
            print "sell: ", order_sell
            order_buy.new()
            print "buy: ", order_buy

            order_sell.expect("AttachExecution",negate=True,wait=1)
            order_buy.expect("AttachExecution",negate=True,wait=1)

            ## amend maq down to match available qty
            order_sell.amend(qty=maq)
            order_buy.expect("AttachExecution")
            order_sell.expect("AttachExecution")

            print "sold: ", order_sell.fills
            print "bought: ", order_buy.fills
        finally:
            order_buy.cancel()
            order_sell.cancel(validate=False)

