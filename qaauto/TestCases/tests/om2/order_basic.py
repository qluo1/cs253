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
                  get_passive_price,
                  opposite_side,
                  getPegOrderType,
                  PegType,
                  AckFailed,
                  active_wait,
                  )
from clientOrderId import clientOrderId

from om2Order import Order

from conf import settings
import importlib
mod = importlib.import_module(settings.RDS_TEST_DATA)
## load reg test data from module
rdsTestData = mod.RDSTestData()
## select sample of test xrefs with SI, SI will cover separtely
test_xrefs = rdsTestData.sample_tests(qualifier="xref",with_si=False)
test_oeids = rdsTestData.sample_tests(qualifier="oeid")
test_starids = rdsTestData.sample_tests(qualifier="starid")
test_tams = rdsTestData.sample_tests(qualifier="tam")

from val_regdata import val_reg_data,val_si_data

class Test_Order_Basic:

    """ @Test: Test all standard order types for new/amend/cancel.

    @Feature: 1) regulatory data validation


    """

    scenarios = []

    tifs = ("Day","GoodTillCancelled","GoodTillDate")

    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)
    test_order_types.update(settings.DARK_ORDER_TYPES)
    ## 'Validation failed: Direct orders to Sigma-X are not supported'
    if 'sigmax' in test_order_types:
        test_order_types.pop("sigmax")

    for sor in test_order_types:
        for xref in test_xrefs:
            for tif in tifs:
                ## GTD only asx
                if tif != "Day" and sor not in ("asx","asxs") : continue
                data = dict(tif=tif,sor=sor,xref=xref,qualifier="xref")
                scenarios.append(data)
        for oeid in test_oeids:
                data = dict(tif="Day",sor=sor,xref=oeid,qualifier="oeid")
                scenarios.append(data)
        for starid in test_starids:
                data = dict(tif="Day",sor=sor,xref=starid,qualifier="starid")
                scenarios.append(data)
        for tam in test_tams:
                data = dict(tif="Day",sor=sor,xref=tam,qualifier="tam")
                scenarios.append(data)

    def test_new_amend_cancel(self,tif,sor,xref,qualifier,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        if sor in settings.ASXCP + settings.SOR_DARK:
            symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote,attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True,top300=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## random side reduce amount of tests
        side = random.choice(settings.TEST_SIDES)
        delta = -1 if side == "Buy" else 1

        # using ticker
        mxq = attrs.get("MINEXECUTABLEQTY")
        ## check price not breach priceStep
        price = get_passive_price(side,quote)
        print "=== market quote / passsive price ==="
        pprint(quote)
        print price, side, attrs
        ## lookup reg data
        regdata = rdsTestData.get(xref,qualifier=qualifier)
        assert "SORSTRATEGYOVERRIDE" not in regdata
        print " === regdata === "
        pprint(regdata)

        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     qty    =random.randint(500,600),
                     tif    =tif,
                     extra = {},
                     )

        if 'oeid' == qualifier:
            order['extra']['customerOeId'] = xref
        elif 'starid' == qualifier:
            order['extra']['clientStarId'] = xref
        elif 'xref' == qualifier:
            order['xref'] = xref
        elif 'tam' == qualifier:
            order['account'] = xref
        else:
            assert False, "unknown qualifier"

        ## set 
        if sor in settings.DARK_ORDER_TYPES:
            order['extra']['crossConsent'] = random.choice(['OkToCross',
                                                            'DoNotCross',
                                                           ## not supported
                                                           # 'CrossOnly',
                                                            'INVALID'
                                                            ])

        ## update tags
        order.update(self.test_order_types[sor])

        ## expire in 3 days
        if tif == "GoodTillDate":
            utcnow = datetime.utcnow() + timedelta(days=3)
            order['extra']['expirationDateTime'] = time.mktime(utcnow.timetuple())

        print " ==== order data === "
        pprint(order)
        ##
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()

        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)

        ######################################
        ### validate order regdata for new
        val_reg_data(test_order.orderInst,qualifier,xref,regdata)

        ## amend qty down
        clOrdId,_ = test_order.amend(qty = order['qty']-100)
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend qty, %s, %s" % (clOrdId,acks)
        ## amend price passive
        clOrdId,_ = test_order.amend(price = price  + tickSize(price,delta))
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend price, %s, %s" % (clOrdId,acks)
        ## amend both price/qty
        clOrdId,_ = test_order.amend(price = price + tickSize(price,delta),
                                     qty = order['qty'] + 200)
        #print "amend: %s, %s" % amend_ack
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend qty/price, %s, %s" % (clOrdId,acks)
        ######################################
        ### validate order regdata for amend
        val_reg_data(test_order.orderInst,qualifier,xref,regdata)
        ######################################
        clOrdId,_ = test_order.cancel()
        acks =  test_order.events(clOrdId)
        print "cancel: %s , %s" % (clOrdId,acks)

class Test_TradeReport:

    """ @TEst: test two legs trade report.

    @Features: 1) regulatory data validation for each leg

    """

    scenarios = []

    shorts = (True,False)

    for cond in ('NX','BP'):
        for bxref in test_xrefs:
            for short in shorts:
                data = dict(sor='asx',cond=cond,buyXref=bxref,sellXref=test_xrefs[0],short=short)
                scenarios.append(data)

    def test_new_cross_trade(self,sor,cond,buyXref,sellXref,short,symbol_depth):
        """ test trade report . """

        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## lookup reg data
        b_regdata = rdsTestData.get(buyXref)
        s_regdata = rdsTestData.get(sellXref)

        tags = settings.TRADE_REPORTS[sor]

        pprint(quote)
        ## ------------------
        t_order = dict( symbol = symbol,
                        price  = last,
                        qty    = random.randint(1000,3000),
                       )

        ## sigma order leg
        t_order.update(tags)

        buy = t_order.copy()
        sell = t_order.copy()

        buy['xref']  = buyXref
        buy['clOrdId'] =  clientOrderId(buy['xref'])
        buy['side'] = 'Buy'

        sell['xref']  = sellXref
        sell['clOrdId'] = clientOrderId(sell['xref'])
        if short:
            sell['side'] = 'Short'
        else:
            sell['side'] = 'Sell'
        ## set crossMatchId
        buy['crossMatchId'] = sell['crossMatchId'] = "%s:%s" % (buy['xref'],sell['xref'])
        ## condition code for trade report
        buy['conditionCode'] = sell['conditionCode'] = cond

        buy_order = Order(**buy)
        sell_order = Order(**sell)

        buy_order.new(validate=False)
        sell_order.new(validate=False)
        # accept after both legs
        buy_order.expect("OrderAccept")
        sell_order.expect("OrderAccept")
        #import pdb;pdb.set_trace()

        print "buy: ", buy_order
        print "sell: ", sell_order
        ## trade reported
        buy_order.expect("AttachExecution")
        sell_order.expect("AttachExecution")

        print 'buy leg:', buy_order.fills
        print 'sell leg:', sell_order.fills

        assert buy_order.orderStatus.primaryStatus == "Complete"
        assert sell_order.orderStatus.primaryStatus == "Complete"
        ######################################
        ### validate order regdata for buyOrder
        val_reg_data(buy_order.orderInst,"xref",buyXref,b_regdata)
        ######################################
        ### validate order regdata for sellOrder
        val_reg_data(sell_order.orderInst,"xref",sellXref,s_regdata)

class Test_FAKFOK:

    """ @Test IOC-FAK/FOK for all standard order types except FAK for ASXS/ASXCB.

    @Feature: FAK/FOK, no trade expected.

    all uni-sor, will be converted into NO uni sor internally.

    """

    scenarios = []

    ## FAK or IOC
    allOrNones = (True,False)

    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)
    #test_order_types.update(settings.DARK_ORDER_TYPES)

    ## ignore sigmaX 
    if 'sigmax' in test_order_types:
        test_order_types.pop("sigmax")

    for sor in test_order_types:
        for xref in test_xrefs:
            regdata = rdsTestData.get(xref)
            for allOrNone in allOrNones:
                ## not valid ASX order type
                if  allOrNone == True and sor in ('asxs','asxcb','asxsb','asxsweep'):
                    continue
                data = dict(sor=sor,xref=xref,allOrNone=allOrNone)
                scenarios.append(data)

    def test_order(self,sor,xref,allOrNone,symbol_depth):
        """ test FOK order type. """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = attrs.get("MINEXECUTABLEQTY")

        ## random side reduce amount of tests
        side = random.choice(settings.TEST_SIDES)

        price = get_passive_price(side,quote)
        ## lookup reg data
        regdata = rdsTestData.get(xref)
        assert "SORSTRATEGYOVERRIDE" not in regdata
        print " === regdata === "
        pprint(regdata)

        order = dict(symbol=symbol,
                     side=side,
                     price=price,
                     tif="ImmediateOrCancel",
                     allOrNone=allOrNone,
                     qty=random.randint(100,1000),
                     xref=xref)

        tags = self.test_order_types[sor]
        order.update(tags)
        #if sor in ('asxcb',) and 'blockLimit' in inst:
        #    order['qty'] = round(inst['blockLimit'] / price ) + 10
        pprint(order)

        print("======== quote ========")
        pprint(quote)
        test_order = Order(**order)

        clOrdId,_ = test_order.new()

        print " new order  %s" % test_order
        ### validate order regdata for new
        val_reg_data(test_order.orderInst,"xref",xref,regdata)
        ## active wait for order complete
        order_complete = lambda order: order.orderStatus.primaryStatus == "Complete"
        assert active_wait(partial(order_complete,test_order))
        ##############################
        ## wait OM2 cancel event
        ## sor is "ForceCancel", direct is "DoneForDay"
        ## due to SI, can't tell easily without lookup reference.
        events = test_order.events()
        if "AttachExecution" in events:
            if test_order.orderStatus != "Complete":
                assert "ForceCancelFailure" in events
        else:
            assert "ForceCancel" in events or "DoneForDay" in events

        assert test_order.orderStatus.primaryStatus == "Complete", test_order.events()
        print test_order.orderStatus

class Test_MarketOrder:

    """ test market order type.  """

    scenarios = []

    for side in settings.TEST_SIDES:
        for ordType in settings.MKT_ORDERS:
            data = dict(sor=ordType,side=side)

            scenarios.append(data)

    def test_order_reject(self,side,sor,symbol_depth):

        """ @Test: test market order type being rejected.

        - asx mkt order type will be rejected.
        - asx mktToLmt will be accepted and traded at other side i.e. bid/ask. price will be ignored.
        - chia mkt order will be rejected, by viking, JIRA 176
        - chia market on close will be supported, JIRA 488
        """
        symbol, quote, cha_quote, attrs= symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        print (" === market === ")
        pprint(quote)

        order = dict(symbol=symbol,
                     side=side,
                     price=0,
                     qty=random.randint(1000,3000),
                     xref=random.choice(settings.CLIENT_XREFS))

        tags = settings.MKT_ORDERS[sor]
        order.update(tags)
        print("======== order ========")
        test_order = Order(**order)
        try:
            test_order.new()
            print test_order
            test_order.expect("AttachExecution")
            fill = test_order.fills[0]
            if side == "Buy":
                assert abs(fill.executionData['executionPrice'] - ask) < 0.001
            else:
                assert abs(fill.executionData['executionPrice'] - bid) < 0.001

            assert test_order.orderStatus.primaryStatus == "Working"

            ## asx direct marketLmt/market 
            assert sor in ("asxmkt","asxmklt")
            test_order.amend(qty =order['qty'] + 100)
            gevent.sleep(1)
            assert len(test_order.fills) == 1
            ## asx direct marketLmt/market 
            test_order.cancel()

        except (AckFailed,ValueError), e:
            print e
            if sor in ("cxamkt","cxamoc"):
                #assert e.args[0]['rejectReasons'][0]['rejectReasonText'] == u'Invalid orderType column in mapping to FIX field OrdType (40).'
                assert e.args[0]['rejectReasons'][0]['rejectReasonText'] == u'Validation failed: CHIA Market leaf order is not supported'

            else:
                error = e.args[0]['rejectReasons'][0]['rejectReasonText']
                assert re.search("Validation failed: Unsupported (SOR) order type",error)

            assert sor in ('asxmkt','cxamkt','cxamoc','asxonly','bestprice')


class Test_SOR_Priority:

    """ test order priority.

    - asx amend order qty down, still keep order priority
    - direct/sor order typs

    """

    order_types = (
        'asx',
        'chia',
        'asxs',
        'asxsweep',
        'sor2',
        'sor3',
        'sor4',
        'sor5',
        'sor6',
        'sor7',
    )
    scenarios = []

    for sor in order_types:
        for side in settings.TEST_SIDES:
            data = dict(sor=sor,side=side)

            if side == 'Buy':
                data['delta'] =1
            else:
                data['delta'] = 1

            scenarios.append(data)

    def test_order_amend_qty_down(self,side,delta,sor,symbol_depth):

        """ @Test: test order amend qty down, both sor/direct order should keep priority.

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## test order passive price
        price = last + tickSize(last,delta)

        print symbol, sor, last
        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     qty    =random.randint(500,800),
                     xref   =random.choice(settings.CLIENT_XREFS))

        tags = settings.ORDER_TYPES[sor]
        order.update(tags)
        pprint(quote)
        test_order1 = Order(**order)
        test_order2 = Order(**order)

        try:

            ###########################################
            ## new order
            test_order1.new()
            print "test order 1: ",test_order1
            gevent.sleep(2)

            test_order2.new()
            print "test order 2:", test_order2

            ## amend order1
            test_order1.amend(qty=order['qty'] -100)

            ###
            ## aggressive tets order
            order_t = order.copy()
            order_t['side'] = opposite_side(order['side'])
            order_t['qty'] = 200

            test_order3 = Order(**order_t)
            test_order3.new()
            print "test order 3", test_order3
            ############################################
            ## validate results
            test_order3.expect("AttachExecution")
            test_order1.expect("AttachExecution")
            test_order2.expect("AttachExecution",negate=True,wait=1)

            assert test_order3.orderStatus.primaryStatus == "Complete"
        finally:
            ## cleanup
            if 'test_order3' in locals() and test_order3.orderStatus.primaryStatus != 'Complete':
                test_order3.cancel()
            test_order1.cancel()
            test_order2.cancel()

    def test_order_amend_qty_up(self,side,delta,sor,symbol_depth):

        """ @Test: amend qty up, sor will keep priority, direct should lost priority.

        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## test order passive price
        price = last + tickSize(last,delta)

        print symbol, sor, last
        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     qty    =1000,
                     xref   =random.choice(settings.CLIENT_XREFS))

        tags = settings.ORDER_TYPES[sor]
        order.update(tags)
        pprint(quote)
        test_order1 = Order(**order)
        test_order2 = Order(**order)

        try:
            ###########################################
            ## new order
            test_order1.new()
            print "test order 1: ",test_order1
            gevent.sleep(2)

            test_order2.new()
            print "test order 2:", test_order2

            ## amend order1
            test_order1.amend(qty=order['qty'] + 100)

            ###
            ## aggressive tets order
            order_t = order.copy()
            order_t['side'] = opposite_side(order['side'])
            order_t['qty'] = 200

            test_order3 = Order(**order_t)
            test_order3.new()
            print "test order 3", test_order3
            ############################################
            ## validate results
            test_order3.expect("AttachExecution")
            if sor in ('asx','chia','asxs','asxsweep'):
                test_order2.expect("AttachExecution")
                test_order1.expect("AttachExecution",negate=True,wait=1)
            else:
                test_order1.expect("AttachExecution")
                test_order2.expect("AttachExecution",negate=True,wait=1)

            assert test_order3.orderStatus.primaryStatus == "Complete"
        finally:
            if 'test_order3' in locals() and test_order3.orderStatus.primaryStatus != "Complete":
                test_order3.cancel()
            test_order1.cancel()
            test_order2.cancel()

class Test_StaleOrder:

    """ @Test: test om2 stale order feature for all standard order type.  """

    scenarios = []

    ## random generated test parameters caused issue on xdist load testing
    for sor in settings.ORDER_TYPES:
        data = dict(sor=sor,side='Buy')

        scenarios.append(data)

    def test_order_reject(self,side,sor,symbol_depth):
        """ test order type. """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol()
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        price = get_passive_price(side,quote)

        print datetime.now()
        now = datetime.now() - timedelta(seconds=35)

        order = dict(symbol=symbol,
                     side=side,
                     price=price,
                     qty=random.randint(4000,5000),
                     xref=random.choice(settings.CLIENT_XREFS),
                     now=now.isoformat())

        tags = settings.ORDER_TYPES[sor]
        order.update(tags)
        print("======== order ========")

        test_order = Order(**order)
        try:
            test_order.new()
            assert False, "order accepted: %s" % test_order
        except AckFailed,e:
            print(e)
            assert e.args[0]['rejectReasons'][0]['rejectReasonText'] == u'Received stale command'


