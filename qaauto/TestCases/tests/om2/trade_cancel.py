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
              active_wait,
              )
from om2Order import Order
from clientOrderId import clientOrderId

from conf import settings
import gevent

from functools import partial

## cross trade map
TEST_MAP = {
        'PP': ('FC1','FC2'),
        'PA': ('FC1','JF5'),
        'PM': ('FC1','OF1'),
        'AA': ('JF5','JF4'),
        'AP': ('JF4','FC2'),
        'AM': ('JF5','OF2'),
        'MM': ('OF1','OF2'),
        'MA': ('OF1','JF4'),
        'MP': ('OF1','FC3'),
    }
## enable execution validation
EXEC_VALIDATION = True

class Test_TradeReport_Cancel:

    """ test two legs trade report cancellation. """

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

    def test_new_cross_trade_cancel(self,sor,cond,t,key,symbol_depth):
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
                        qty    = random.randint(1000,3000),
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
        tradeCode = buy_order.fills[0].executionData['execFlowSpecificAustralia']["australiaTradeConditionCode"]
        venue = buy_order.fills[0].executionData['executionVenue']
        subExecPoint = buy_order.fills[0].executionData['subExecutionPoint']
        assert venue == "SYDE"
        assert subExecPoint == "SIGA"

        if cond == "NX":
            assert tradeCode == "NXXT"
        elif cond == "BP":
            assert tradeCode == "BPXT"
        elif cond == "ET":
            assert tradeCode == "ETXT"
        else:
            pass

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
        gevent.sleep(20)

        #pytest.set_trace()
        ## cancel trade report
        assert len(buy_order.fills) == 1
        assert len(sell_order.fills) == 1
        buy_order_execId = buy_order.fills[0].executionData['executionId']
        sell_order_execId = sell_order.fills[0].executionData['executionId']

        res_b = buy_order.requestCancelExecution(executionId=buy_order_execId)
        assert res_b
        gevent.sleep(3)
        ## viking should hold up cancel wait for next leg also canceled.
        b_exec_image = buy_order.requestExecutionImage(buy_order_execId)
        assert b_exec_image['executionData']['executionStatus'] == "Alive"

        res_s = sell_order.requestCancelExecution(executionId=sell_order_execId)
        assert res_s

        def expect_cancel(order,execId):
            """ """
            image = order.requestExecutionImage(execId)
            return image['executionData']['executionStatus'] == "Canceled"
        ## both order should be canceled
        active_wait(partial(expect_cancel,order=sell_order,execId=sell_order_execId),raise_timeout=True)
        active_wait(partial(expect_cancel,order=buy_order,execId=buy_order_execId),raise_timeout=True)
