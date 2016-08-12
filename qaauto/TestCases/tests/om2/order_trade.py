""" om2 test cases for trade.

"""
import os
import time
import random
import copy
import itertools
from pprint import pprint
from datetime import datetime, timedelta
from  dateutil import parser
import calendar
import pytest

from utils import (
              valid_rf_ack,
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              round_price,
              check_halfTick,
              )
from om2Order import Order
from clientOrderId import clientOrderId

from conf import settings

## cross trade map
TEST_MAP = {
        'PP': ('FC1','FC2'),
        'PA': ('FC1','MD2'),
        'PM': ('FC1','OF1'),
        'AA': ('MD2','MD1'),
        'AP': ('MD1','FC2'),
        'AM': ('MD2','OF2'),
        'MM': ('OF1','OF2'),
        'MA': ('OF1','MD1'),
        'MP': ('OF1','FC3'),
    }
## enable execution validation
EXEC_VALIDATION = True

class Test_Order_Trade:

    """ test order execution.

    validate: versus account for au execution
    http://eq-trading.jira.services.gs.com/jira/browse/ANZIN-483
    no cross trade versus account: 043947308

    """

    scenarios = []

    for sor in settings.SOR_NODIRECT_DARK:
        if sor not in ('chia_ask','chia_bid','chia_mid'):
            for side in settings.TEST_SIDES:
                for key in TEST_MAP.keys():

                    data = dict(sor=sor,side=side,key=key)
                    scenarios.append(data)

    def test_new_cross_trade(self,side,sor,key,symbol_depth):
        """ @Test: test new order cross trade for all order types except CHIA Peg order type.

        """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol()

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        test_data = TEST_MAP[key]
        buy_xref = test_data[0]
        sell_xref = test_data[1]

        tags = settings.ORDER_TYPES[sor]

        pprint(quote)

        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =random.randint(100,300),
                   xref   =buy_xref)

        ## asxcb need big size
        if sor in ('asxcb',):
            buy['qty'] = round(settings.ASXCB_ORDER_MINIMUM_SIZE/last) + 10

        sell = copy.deepcopy(buy)
        sell['side'] = opposite_side(side)
        sell['xref'] = sell_xref
        sell['qty'] = buy['qty'] + 100
        ## set new order maq = 0
        buy.update(tags)
        sell.update(tags)
        pprint(buy)
        pprint(sell)

        first_order = Order(**buy)
        second_order = Order(**sell)

        ###########################################
        first_order.new()
        ## not traded yet
        first_order.expect("AttachExecution",negate=True,wait=5)

        second_order.new()
        print "first Order", first_order
        print "second Order", second_order
        ## order traded
        first_order.expect("AttachExecution")
        second_order.expect("AttachExecution")

        print "first order, %s, %s" % (first_order.orderId,first_order.events())
        print "second order, %s, %s" % (second_order.orderId,second_order.events())
        print "  ------------------ "
        assert len(first_order.fills) > 0
        assert len(second_order.fills) > 0
        print "first order fill:" , first_order.fills
        print "second order fill:", second_order.fills

        ## validate fill / versus account
        ## validate execVenue
        ## liquidity indicator
        if EXEC_VALIDATION:

            first_liquidityIndicator = first_order.fills[0].executionData['liquidityIndicator']
            second_liquidityIndicator = second_order.fills[0].executionData['liquidityIndicator']

            ## asxc always providedLiquidity
            if  second_order.fills[0].executionData.get('subExecutionPoint') == 'ASXC':
                assert second_liquidityIndicator == "ProvidedLiquidity"
            else:
                assert second_liquidityIndicator == "TookLiquidity"

            assert first_liquidityIndicator == "ProvidedLiquidity"

            venue = first_order.fills[0].executionData['executionVenue']

            ## validate executionCapacity and crossPartyOrderCapacity
            capacity = first_order.fills[0].executionData['executionCapacity']

            crossCapacity = first_order.fills[0].executionData['crossPartyOrderCapacity']['orderCapacity']
            ## trade condition code
            tradeCode = first_order.fills[0].executionData['execFlowSpecificAustralia']["australiaTradeConditionCode"]

        assert second_order.orderStatus.primaryStatus == "Working", second_order.orderStatus

        second_order.cancel()
        assert second_order.orderStatus.primaryStatus == "Complete", second_order.orderStatus

    def test_amend_cross_trade(self,side,sor,key,symbol_depth):

        """ @Test: test amend price aggressive for cross trade for all order types except CHIA Peg type. """

        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol()

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        test_data = TEST_MAP[key]
        buy_xref = test_data[0]
        sell_xref = test_data[1]

        tags = settings.ORDER_TYPES[sor]

        pprint(quote)

        if side == 'Buy':
            delta = tickSize(last,-2)
        else:
            delta = tickSize(last,2)

        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =random.randint(100,300),
                   xref   =buy_xref)

        sell = copy.deepcopy(buy)
        sell['side'] = opposite_side(side)
        sell['xref'] = sell_xref
        sell['qty'] = buy['qty'] + 100
        #sell['maq'] = 50
        # set buy price passive
        buy['price'] = buy['price'] + delta

        buy.update(tags)
        sell.update(tags)
        pprint(buy)
        pprint(sell)

        first_order = Order(**buy)
        second_order = Order(**sell)

        ###########################################
        first_order.new()
        ## order acked
        ## not traded yet
        first_order.expect("AttachExecution",negate=True,wait=6)

        second_order.new()

        ## still not traded yet
        first_order.expect("AttachExecution",negate=True,wait=0.5)
        second_order.expect("AttachExecution",negate=True,wait=0.5)
        ## amend aggressive
        first_order.amend(price=last)
        ## traded
        first_order.expect("AttachExecution")
        second_order.expect("AttachExecution")
        ##TODO: check it is cross

        print "first order, %s, %s" % (first_order.orderId,first_order.events())
        print "second order, %s, %s" % (second_order.orderId,second_order.events())
        print "  ------------------ "
        assert len(first_order.fills) > 0
        assert len(second_order.fills) > 0
        print "first order fill:" , first_order.fills
        print "second order fill:", second_order.fills

        ## validate fill / versus account
        ## validate execVenue
        ## liquidity indicator
        if EXEC_VALIDATION:
            first_liquidityIndicator = first_order.fills[0].executionData['liquidityIndicator']
            second_liquidityIndicator = second_order.fills[0].executionData['liquidityIndicator']
            assert second_liquidityIndicator == "ProvidedLiquidity"
            ## cp always provide liquidity
            if first_order.fills[0].executionData.get('subExecutionPoint') == 'ASXC':
                assert first_liquidityIndicator == "ProvidedLiquidity"
            else:
                assert first_liquidityIndicator == "TookLiquidity"

            venue = first_order.fills[0].executionData['executionVenue']
            ## validate executionCapacity and crossPartyOrderCapacity
            capacity = first_order.fills[0].executionData['executionCapacity']
            crossCapacity = first_order.fills[0].executionData['crossPartyOrderCapacity']['orderCapacity']
            ## trade condition code
            tradeCode = first_order.fills[0].executionData['execFlowSpecificAustralia']["australiaTradeConditionCode"]

        assert second_order.orderStatus.primaryStatus == "Working", second_order.orderStatus

        second_order.cancel()
        assert second_order.orderStatus.primaryStatus == "Complete", second_order.orderStatus


class Test_TradeReport:

    """ test two legs trade report. """

    scenarios = []

    for cond in (
                    'NX',
                    'BP',   # booking purpose
                    'ET',   # ETF 
                    #'S1',   # Block trade
                    #'SX',   # large portfolio trade
                    #'L1',   # L1-5
                    #'L2',   #
                    #'L3',   #
                    #'L4',   #
                    #'L5',   #
                    ## out of hour
                    #'LT',
                    #'OS',
                    #'OR',
                    ):
        for T in (
                  0,
                  #1 ## T+1 trade report
                  ):
            for key in TEST_MAP.keys():
                for sor in settings.TRADE_REPORTS:
                    data = dict(sor=sor,cond=cond,t=T,key=key)
                    scenarios.append(data)

    def test_new_cross_trade(self,sor,cond,t,key,symbol_depth):
        """ test trade report . """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## test xref
        test_data = TEST_MAP[key]
        buy_xref = test_data[0]
        sell_xref = test_data[1]

        tags = settings.TRADE_REPORTS[sor]

        pprint(quote)
        ## ------------------
        t_order = dict( symbol = symbol,
                        price  = last,
                        qty    = random.randint(100,300),
                        extra = {}
                       )
        ##
        yesterday = (datetime.now()- timedelta(days=t)).strftime("%Y-%m-%d")
        tplus_1 = parser.parse(yesterday)
        if t:
            t_order['extra']['tradeAgreementDate'] = int(calendar.timegm(tplus_1.timetuple()))
        ## sigma order leg
        t_order.update(tags)

        buy = t_order.copy()
        sell = t_order.copy()

        buy['xref']  = buy_xref
        buy['clOrdId'] =  clientOrderId(buy['xref'])
        buy['side'] = 'Buy'

        sell['xref']  = sell_xref
        sell['clOrdId'] = clientOrderId(sell['xref'])
        sell['side'] = 'Sell'
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

        print "buy: ", buy_order
        print "sell: ", sell_order
        ## trade reported
        buy_order.expect("AttachExecution")
        sell_order.expect("AttachExecution")

        print 'buy leg:', buy_order.fills
        print 'sell leg:', sell_order.fills

        ## validate trade condition code
        ## trade condition code
        if EXEC_VALIDATION:
            tradeCode = buy_order.fills[0].executionData['execFlowSpecificAustralia']["australiaTradeConditionCode"]
            venue = buy_order.fills[0].executionData['executionVenue']
            subExecPoint = buy_order.fills[0].executionData['subExecutionPoint']
            assert venue == "SYDE"
            #assert subExecPoint == "ASXT"
            ## crossingMatchId match xref otherwise will be ASXT
            assert subExecPoint == "SIGA"

            if cond == "NX":
                assert tradeCode == "NXXT"
            elif cond == "BP":
                assert tradeCode == "BPXT"
            elif cond == "ET":
                assert tradeCode == "ETXT"
            else:
                pass

            ## versus account
            #versus = [o for o in buy_order.fills[0].executionData['accounts'] if o['accountRole'] == 'Versus']
            #assert len(versus) == 1
            #accountAliases = versus[0]["accountAliases"]
            #assert len(accountAliases) == 1
            #versus_account = accountAliases[0]['accountSynonym']
            #assert  versus[0]['entity'] == "GSJP"

            #assert tradeCode.endswith("XT")
            #assert versus_account == "043947290"

        ## validate asDate i.e. tradeAggrementDate
        #pytest.set_trace()
        for order in (buy_order,sell_order):
            for snapshot in order.hist():
                _asDate = snapshot.order.tradeAgreementDate
                asDate = datetime.fromtimestamp(_asDate)
                assert asDate.year == tplus_1.year and asDate.month == tplus_1.month and asDate.day == tplus_1.day

                if hasattr(snapshot,'execution'):
                    assert snapshot.execution.executionData["marketTradeDate"]
                    tradeDate = datetime.fromtimestamp(snapshot.execution.executionData["marketTradeDate"])
                    assert tradeDate.year == tplus_1.year and tradeDate.month == tplus_1.month and tradeDate.day == tplus_1.day


        assert buy_order.orderStatus.primaryStatus == "Complete"
        assert sell_order.orderStatus.primaryStatus == "Complete"

class Test_CP_Trade_MidTick:

    """ test direct order type. """

    scenarios = []


    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)
    test_order_types.update(settings.DARK_ORDER_TYPES)

    for sor in settings.ASXCP:
        data = dict(sor=sor)

        scenarios.append(data)

    def test_new_cp_offtick_trade(self,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,tick=0.5)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        pprint(quote)
        ## prepare test order, buy side is asxc resting
        asxc_tags = settings.ORDER_TYPES['asxc']
        tags = self.test_order_types[sor]

        ## ------------------
        buy = dict(symbol =symbol,
                   side   ='Buy',
                   price  =last + tickSize(last,1),
                   qty    =random.randint(100,300),
                   xref   =random.choice(settings.CLIENT_XREFS))

        buy.update(asxc_tags)

        sell = copy.deepcopy(buy)
        sell['side'] = 'Sell'
        sell['xref'] = random.choice(settings.HOUSE_XREFS)
        sell['qty'] = buy['qty'] + 500
        sell['price'] = last
        sell.update(tags)

        buy_order = Order(**buy)
        sell_order = Order(**sell)

        buy_order.new()
        print "buy:", buy_order
        sell_order.new()
        print "sell:", sell_order

        buy_order.expect("AttachExecution")
        sell_order.expect("AttachExecution")


        print "bought:", buy_order.fills
        print "sold:", sell_order.fills

        assert check_halfTick(buy_order.fills[0].executionData['executionPrice'])
        assert check_halfTick(sell_order.fills[0].executionData['executionPrice'])
        try:
            sell_order.cancel()
        except Exception,e:
            pass

        assert buy_order.orderStatus.primaryStatus == "Complete"
        assert sell_order.orderStatus.primaryStatus == "Complete"

    def test_new_cp_halfTick_price(self,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,tick=0.5)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        pprint(quote)
        ## prepare test order
        asxc_tags = settings.ORDER_TYPES['asxc']
        tags = self.test_order_types[sor]

        ## ------------------
        buy = dict(symbol =symbol,
                   side   ='Buy',
                   price  =last + halfTick(last),
                   qty    =random.randint(100,300),
                   xref   =random.choice(settings.CLIENT_XREFS))

        buy.update(asxc_tags)

        sell = copy.deepcopy(buy)
        sell['side'] = 'Sell'
        sell['xref'] = random.choice(settings.HOUSE_XREFS)
        sell['qty'] = buy['qty'] + 100
        sell['price'] = last + halfTick(last)
        sell.update(tags)

        buy_order = Order(**buy)
        sell_order = Order(**sell)

        buy_order.new()
        print "buy: ", buy_order
        sell_order.new()
        print "sell: ", sell_order

        buy_order.expect("AttachExecution")
        sell_order.expect("AttachExecution")

        print "bought:", buy_order.fills
        print "sold:", sell_order.fills
        ############################################
        ### validate trade price is half tick
        assert check_halfTick(buy_order.fills[0].executionData['executionPrice'])
        assert check_halfTick(sell_order.fills[0].executionData['executionPrice'])

        try:
            sell_order.cancel()
        except Exception,e:
            pass
        assert buy_order.orderStatus.primaryStatus == "Complete"
        assert sell_order.orderStatus.primaryStatus == "Complete"

class Test_Order_TradeCHIA:

    """ test direct order type. """

    scenarios = []

    #for sor in settings.ASXCP:
    for sor in settings.ORDER_TYPES:
        if sor in (
                   'chia_ask','chia_bid','chia_mid'
                   ):
            for side in settings.TEST_SIDES:
                data = dict(sor=sor,side=side)

                scenarios.append(data)

    @pytest.mark.skipif("True")
    def test_new_chia_trade(self,side,sor,symbol_depth):
        """ CHIA trade for broker perference. """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,tick=0.5)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        tags = settings.ORDER_TYPES[sor]

        if side == "Buy":
            buy = dict(symbol =symbol,
                    side   = side,
                    price  = ask,
                    qty    =random.randint(100,300),
                    xref   =random.choice(settings.CLIENT_XREFS))

            sell = copy.deepcopy(buy)
            sell['side'] = 'Sell'
            sell['price'] = bid
            sell['tif'] ="ImmediateOrCancel"
            sell['xref'] = random.choice(settings.HOUSE_XREFS)

            sell.update(settings.ORDER_TYPES["chia"])
            ##
            buy.update(tags)
            ## buy is passive
            test_buy = Order(**buy)
            test_buy.new()

            ## passive sell
            test_sell = Order(**sell)
            test_sell.new()

            ## aggr buy
            test_buy.expect("AttachExecution")
            test_sell.expect("AttachExecution")
        else:

            sell = dict(symbol =symbol,
                    side   = side,
                    price  = bid,
                    qty    =random.randint(1000,3000),
                    xref   =random.choice(settings.CLIENT_XREFS))

            buy = copy.deepcopy(sell)
            buy['side'] = 'Buy'
            buy['price'] = ask
            buy['tif'] ="ImmediateOrCancel"
            buy['xref'] = random.choice(settings.HOUSE_XREFS)

            buy.update(settings.ORDER_TYPES["chia"])
            ##
            sell.update(tags)

            ## passive sell
            test_sell = Order(**sell)
            test_sell.new()
            # aggr buy
            test_buy = Order(**buy)
            test_buy.new()

            test_buy.expect("AttachExecution")
            test_sell.expect("AttachExecution")


class Test_Order_ExecVenue_ExecCapacity_CrossConditionCode:

    """ test direct order/trade for execVenue.

    do a cross trade for test order types.

    for asxsweep , opposite order will be asxc and expect it will be trade on ASXC.

    note: asxsweep == asxs

    executionCapacity & crossPartyOrderCapacity
    http://eq-trading.jira.services.gs.com/jira/browse/ANZIN-369

    trade condition code for cross
    http://eq-trading.jira.services.gs.com/jira/browse/ANZIN-370

    trade report will be done in separate test case.

    """

    scenarios = []

    test_order_types = [
                    'chia',
                    'asx',
                    'asxc',
                    'asxs',
                    'asxsweep'
                    ]

    for sor in test_order_types:
        for side in settings.TEST_SIDES:
            for  key in TEST_MAP:
                data = dict(sor=sor,side=side,key=key)

                scenarios.append(data)

    def test_new_cross_trade(self,side,sor,key,symbol_depth):
        """
        test order fill on exchange and validate execVenue.
        """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        tags = settings.ORDER_TYPES[sor]

        test_data = TEST_MAP[key]
        buy_xref = test_data[0]
        sell_xref = test_data[1]

        print "== market =="
        pprint(quote)
        ## ------------------
        buy = dict(symbol =symbol,
                   side   =side,
                   price  =last,
                   qty    =random.randint(100,300),
                   xref   =buy_xref)

        sell = copy.deepcopy(buy)
        sell['side'] = opposite_side(side)
        sell['xref'] = sell_xref
        sell['qty'] = buy['qty'] + 100

        buy.update(tags)
        ## for ASXSWEEP, it should be same as ASXS, but we want it filled in ASXC
        if sor == "asxsweep":
            tags = settings.ORDER_TYPES['asxc']

        sell.update(tags)


        buy_order = Order(**buy)
        sell_order = Order(**sell)

        if sor != 'asxsweep':
            ###########################################
            buy_order.new()
            ## not traded yet
            buy_order.expect("AttachExecution",negate=True,wait=3)

            sell_order.new()
        else:
            ## asxsweep hit ASXC first, then resting
            sell_order.new()
            sell_order.expect("AttachExecution",negate=True,wait=3)
            buy_order.new()

        print "== buy order == "
        pprint(buy_order)
        print "== sell order == "
        pprint(sell_order)
        ## order traded
        buy_order.expect("AttachExecution")
        sell_order.expect("AttachExecution")

        ## validate execVenue
        if EXEC_VALIDATION:
            venue = buy_order.fills[0].executionData['executionVenue']

            if sor in('chia','chia_mid'):
                assert venue == 'CHIA'
            else:
                ## asx validate subExecutionPoint
                subVenue = buy_order.fills[0].executionData['subExecutionPoint']
                if sor in ( 'asx','asxs',):
                    assert subVenue == 'ASXT'
                else:
                    ## asxc or asxsweep
                    assert subVenue == 'ASXC'

            # validate executionCapacity and crossPartyOrderCapacity
            capacity = buy_order.fills[0].executionData['executionCapacity']
            crossCapacity = buy_order.fills[0].executionData['crossPartyOrderCapacity']['orderCapacity']
            # trade condition code
            tradeCode = buy_order.fills[0].executionData['execFlowSpecificAustralia']["australiaTradeConditionCode"]

            ## UCP crossing
            if key == "PP":
                if sor == "chia":
                    assert tradeCode == "XXT"
                else:
                    if sor in ("asxsweep","asxc"):
                        assert tradeCode == "BPCXXT"
                    else:
                        assert tradeCode == "BPXT"
            else:
                if sor in ("asxsweep","asxc"):
                    assert tradeCode == "CPCXXT"
                else:
                    assert tradeCode == "XT"

            if key == 'PP':
                assert buy_order.orderInst.orderCapacity == "Principal"
                assert sell_order.orderInst.orderCapacity == "Principal"
                assert capacity == "CrossAsPrincipal"
                assert crossCapacity == "Principal"

            elif key == 'PA':
                assert buy_order.orderInst.orderCapacity == "Principal"
                assert sell_order.orderInst.orderCapacity == "Agency"
                assert capacity == "CrossAsAgent"
                assert crossCapacity == "Agency"
            elif key == 'PM':
                assert buy_order.orderInst.orderCapacity == "Principal"
                assert capacity == "CrossAsPrincipal"
                assert crossCapacity == "Combined"
            elif key == 'AA':
                assert buy_order.orderInst.orderCapacity == "Agency"
                assert sell_order.orderInst.orderCapacity == "Agency"
                assert capacity == "CrossAsAgent"
                assert crossCapacity == "Agency"
            elif key == 'AP':
                assert buy_order.orderInst.orderCapacity == "Agency"
                assert sell_order.orderInst.orderCapacity == "Principal"
                assert capacity == "CrossAsPrincipal"
                assert crossCapacity == "Principal"
            elif key == 'AM':
                assert buy_order.orderInst.orderCapacity == "Agency"
                assert sell_order.orderInst.orderCapacity == "Combined"
                assert capacity == "CrossAsPrincipal"
                assert crossCapacity == "Combined"
            elif key == 'MA':
                assert buy_order.orderInst.orderCapacity == "Combined"
                assert sell_order.orderInst.orderCapacity == "Agency"
                assert capacity == "CrossAsAgent"
                assert crossCapacity == "Agency"
            elif key == 'MP':
                assert buy_order.orderInst.orderCapacity == "Combined"
                assert sell_order.orderInst.orderCapacity == "Principal"
                assert capacity == "CrossAsPrincipal"
                assert crossCapacity == "Principal"
            elif key == 'MM':
                assert buy_order.orderInst.orderCapacity == "Combined"
                assert sell_order.orderInst.orderCapacity == "Combined"
                assert capacity == "CrossAsPrincipal"
                assert crossCapacity == "Combined"
            else:
                raise ValueError("unexpected value: %s" %key)


        print "buyorder, %s, %s" % (buy_order.orderId,buy_order.events())
        print "sellorder, %s, %s" % (sell_order.orderId,sell_order.events())
        print "  ------------------ "
        assert len(buy_order.fills) > 0
        assert len(sell_order.fills) > 0
        print "buyorder fill:" , buy_order.fills
        print "sellorder fill:", sell_order.fills

        assert sell_order.orderStatus.primaryStatus == "Working", sell_order.orderStatus

        sell_order.cancel()
        assert sell_order.orderStatus.primaryStatus == "Complete", sell_order.orderStatus
