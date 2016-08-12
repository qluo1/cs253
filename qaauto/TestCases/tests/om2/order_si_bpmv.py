""" test cases : SOR BPMV with SI override.

- BestPriceMinValue (i.e. BPMV)
- for order value < $120k, will be treated as asx direct
- for order value > $120k, will become BPMV
- BPMV:

The specification for the JCP strategy, BestPriceMinValue, are:
    .   The strategy is not a Uni strategy.
    .   Trades on any dark venue (Chi-X dark or ASXC) can be only for more than AUD$100k (in our case please consider that we have a buffer, AUD$120k) notional value.
    .   Chi-X lit trades (since this isn.t a Uni strategy we.re talking only about Chi-X lit sweeps here) can happen only if Chi-X is better than the ASX touch. So if the aggressive Buy order is for 10@10, when Chi-X is offered at 9 and ASX at 10 . we.ll take volume from Chi-X, again for minimum of $120k notional, however if ASX is offered at 9 or at 8, then ASX is better or equal, and we.ll not attempt to take out volume from Chi-X. The same applies to Sell orders, in reverse of course.


"""
import os
import math
import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
from datetime import datetime,timedelta
import gevent

from utils import (
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              getPegOrderType,
              PegType,
              AckFailed,
              )

from om2Order import Order
from conf import settings
import zerorpc

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

MIN_VALUE = 120000
MIN_BUFFER = 100
## test xref 
XREF = "SAM99"

class Test_Order_BPMV_SI:

    """ test sor BPMV.

    Test Design:

    - order value less than $120k, will be asx direct
    - order value greater than $120k
    - 1) dark sweep CHIA minVal > $120k
    - 2) dark sweep ASXC minVal > $120k
    - 3) lit sweep CHIA for better price /trade value > $120k
    - 4) lit sweep ASX for better or equal, no attemp for CHIA
    - 5) order start life as direct or SOR and keep it for life of order
    - 6) sor order subsequent amend aggr shouldn't dark sweep CHIA
    - 7) SI override for selected XREF i.e. JFB, D02

    """

    scenarios = []
    ## asxonly, BPMQ , only sor will be SI override, direct order will pass through
    sors = ['sor1','sor4']

    for side in settings.TEST_SIDES:
        for sor in sors:
            data = dict(sor=sor,side=side)

            scenarios.append(data)

    def setup_class(cls):
        """ setup SI override test data for test xref. """
        ## QAE/PPE only, PME need manual load snapshot
        print "setup rds data. "
        with open(os.path.join(CUR_DIR,"data_si_bpmv.out"),"r") as f:
            for ln in f:
                line = ln.strip()
                if  line.startswith("Insert"):
                    command = {
                        'cmd': 'updateSharedMemoryFeederRecord',
                        'handle': 'updateSharedMemoryFeederRecord',
                        'argumentVector': [
                            {'arg': line },
                        ],
                    }
                    #print cmd
                    ack = Order.sendRdsHermes(command)
                    assert "Success" == ack['status']

    def test_amend_below(self,side,sor,symbol_depth):
        """ order amend qty down.

        - new order value > 120k, order as BPMV
        - amend order value below MinVal,
        - order still keep as BPMV
        - no unireflect after amend
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     ## xref is configured within data_si_bpmv.out
                     xref   =XREF ,
                     )
        tags = settings.ORDER_TYPES[sor]
        order.update(tags)

        ## minQty
        minQty = (MIN_VALUE  + MIN_BUFFER)/ order['price']
        order['qty'] = math.ceil(minQty)

        pprint(order)

        print("======== quote ========")
        pprint(quote)
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')

        ##########################################
        ## amend value below $120
        minQty = math.floor(5000 / order['price'])

        clOrdId,_ = test_order.amend(qty=minQty)
        #print "amend: %s, %s" % amend_ack
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend, %s, %s" % (clOrdId,acks)
        ## validate JCP strategy
        assert test_order.orderType.startswith("BPMV")

        clOrdId,_ = test_order.cancel()
        acks =  test_order.events(clOrdId)
        print "cancel: %s , %s" % (clOrdId,acks)

    def test_amend_above(self,side,sor,symbol_depth):
        """ order amend qty up.

        - new order value < 120k
        - amend order qty up, order value exceed MinVal,
        - order keep as ASX Limit.

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     qty    =random.randint(10,20),
                     xref   =XREF,
                     )
        tags = settings.ORDER_TYPES[sor]
        order.update(tags)
        pprint(order)
        ##
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType == "SYDE-Limit"

        ##########################################
        ## amend value above $120
        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ order['price'])

        clOrdId,_ = test_order.amend(qty=minQty)
        #print "amend: %s, %s" % amend_ack
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend, %s, %s" % (clOrdId,acks)
        ## still keep as SYDE-LIMIT
        assert test_order.orderType == "SYDE-Limit"

        clOrdId,_ = test_order.cancel()
        acks =  test_order.events(clOrdId)
        print "cancel: %s , %s" % (clOrdId,acks)

    def test_new_sweep_chia_dark(self,side,sor,symbol_depth):
        """ order new sweep CHIX dark.

        - new aggressive order, value greater minVal
        - CHIA got better price.
        - order hit CHIA dark for full amount.
        - initial sweep behave as if BP

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['side'] = opposite_side(side)
        order_chia['xref'] = "FC8"
        order_chia.update(settings.ORDER_TYPES['chia_mid'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        print("======== quote ========")
        pprint(quote)

        ## sumbit chia dark order
        chia_dark = Order(**order_chia)
        chia_dark.new()
        chia_dark.expect_ok()

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')
        ## both order filled.
        test_order.expect("AttachExecution")
        chia_dark.expect("AttachExecution")

    def test_new_sweep_chia_lit(self,side,sor,symbol_depth):
        """ order new sweep CHIX dark.

        - new aggressive order, value greater minVal
        - CHIA got better price.
        - order hit CHIA dark for full amount.
        - initial sweep behave as if BP?

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['side'] = opposite_side(side)
        order_chia['xref'] = "FC8"
        order_chia.update(settings.ORDER_TYPES['chia'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        print("======== quote ========")
        pprint(quote)

        ## sumbit chia dark order
        chia_dark = Order(**order_chia)
        chia_dark.new()
        chia_dark.expect_ok()

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        #test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')
        ## both order filled.
        test_order.expect("AttachExecution")
        chia_dark.expect("AttachExecution")

    def test_new_sweep_chia_dark_below_minVal(self,side,sor,symbol_depth):
        """ order new sweep CHI dark.

        - new aggressive order, value below minVal
        - CHIA got better price.
        - order NOT hit CHIA dark for full amount.

        """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['side'] = opposite_side(side)
        order_chia['qty'] = random.randint(10,200)
        order_chia['xref'] = "FC8"
        order_chia.update(settings.ORDER_TYPES['chia_mid'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        print("======== quote ========")
        pprint(quote)

        ## sumbit chia dark order
        chia_dark = Order(**order_chia)
        chia_dark.new()
        chia_dark.expect_ok()

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')
        ## both order filled.
        test_order.expect("AttachExecution",negate=True)
        chia_dark.expect("AttachExecution",negate=True)
        test_order.cancel()
        chia_dark.cancel()

    def test_new_sweep_chia_lit_below_minVal(self,side,sor,symbol_depth):
        """ order new sweep CHIX lit.

        - new aggressive order, value below  minVal
        - CHIA got better price.
        - order NOT hit CHIA lit for full amount.

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['qty'] = random.randint(20,200)
        order_chia['xref'] = "FC8"
        order_chia['side'] = opposite_side(side)
        order_chia.update(settings.ORDER_TYPES['chia'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        ##
        print("======== quote ========")
        pprint(quote)

        ## sumbit chia dark order
        chia_dark = Order(**order_chia)
        chia_dark.new()
        chia_dark.expect_ok()

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')
        ## both order filled.
        test_order.expect("AttachExecution",negate=True)
        chia_dark.expect("AttachExecution",negate=True)
        test_order.cancel()
        chia_dark.cancel()

    def test_new_resting_chia_lit_notrade(self,side,sor,symbol_depth):
        """ order new resting , no unireflect.

        - new order, value greater minVal
        - no unireflect
        - after new order, CHIA test order with a better price, NO trade
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['side'] = opposite_side(side)
        order_chia['xref'] = "FC8"
        order_chia.update(settings.ORDER_TYPES['chia'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        ##
        print("======== quote ========")
        pprint(quote)

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')

        time.sleep(0.5)

        ## sumbit chia lit order
        chia_order = Order(**order_chia)
        chia_order.new()
        chia_order.expect_ok()

        time.sleep(1)

        test_order.expect("AttachExecution",negate=True)
        chia_order.expect("AttachExecution",negate=True)
        test_order.cancel()
        chia_order.cancel()


    def test_amend_resting_chia_lit_resweep(self,side,sor,symbol_depth):
        """ order amend aggr , resweep.

        - new order, value greater minVal
        - no unireflect
        - after new order, CHIA test order with a better price, no trade
        - amend order aggr, resweep hit CHIA

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE + MIN_BUFFER)/ last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['side'] = opposite_side(side)
        order_chia['xref'] = "FC8"
        order_chia.update(settings.ORDER_TYPES['chia'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        print("======== quote ========")
        pprint(quote)

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')

        gevent.sleep(0.5)

        ## sumbit chia lit order
        chia_order = Order(**order_chia)
        chia_order.new()
        chia_order.expect_ok()

        gevent.sleep(1)

        test_order.expect("AttachExecution",negate=True)
        chia_order.expect("AttachExecution",negate=True)

        ## amend order aggr
        delta = 1 if side =='Buy' else -1
        test_order.amend(price=last + tickSize(last,delta))
        ## amend price aggr on sell, might change order value
        if test_order._data['price'] * test_order._data['qty'] > MIN_VALUE:
            if side == 'short':
                #pytest.skip("aggressive short will be rejected by exchange: Short Sell < Last traded price; Short Sell < Last traded price")
                test_order.expect("RejectOrderCorrect")
                cha_order.cancel()
            else:
                test_order.expect("AttachExecution")
                chia_order.expect("AttachExecution")
        else:
           test_order.expect("AttachExecution",negate=True)
           chia_order.expect("AttachExecution",negate=True)
           test_order.cancel(validate=False)
           chia_order.cancel(validate=False)


    def test_amend_resting_chia_lit_resweep_below_minVal(self,side,sor,symbol_depth):
        """ order amend aggr , resweep.

        - new order, value greater minVal
        - no unireflect
        - after new order, CHIA test order with a better price, NO trade
        - amend order aggr,val below minVal, resweep not hit CHIA

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        minQty = math.ceil((MIN_VALUE  + MIN_BUFFER)/ last)

        belowQty = math.floor((MIN_VALUE - MIN_BUFFER)/last)

        order = dict(symbol = symbol,
                     side   = side,
                     price  = last,
                     qty    = minQty,
                     xref   = XREF,
                    )

        order_chia = order.copy()
        order_chia['side'] = opposite_side(side)
        order_chia['xref'] = "FC8"
        order_chia.update(settings.ORDER_TYPES['chia'])

        order.update(settings.ORDER_TYPES[sor])
        pprint("======= test order =========")
        pprint(order)
        ## setup CHIA dark test order
        pprint("======= facil order ======")
        pprint(order_chia)

        print("======== quote ========")
        pprint(quote)

        ## submit sor test order
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        assert test_order.orderType.startswith('BPMV')

        gevent.sleep(0.5)

        ## sumbit chia lit order
        chia_order = Order(**order_chia)
        chia_order.new()
        chia_order.expect_ok()

        gevent.sleep(1)

        test_order.expect("AttachExecution",negate=True)
        chia_order.expect("AttachExecution",negate=True)

        ## amend order aggr
        delta = 1 if side =='Buy' else -1
        test_order.amend(qty=belowQty, price=last + tickSize(last,delta))
        test_order.expect("AttachExecution",negate=True)
        chia_order.expect("AttachExecution",negate=True)

        test_order.cancel()
        chia_order.cancel()

