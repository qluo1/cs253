""" test SOR_AUDark algo.

AUDark is to replace ATP sonarDark algo.

split order into ASXC, CXAD, SIGMX (either plutus or X3 based on symbol configuraiton.


use trading_tech_common
go
select * from om_preferences
--where preferenceValue = 'SGMX'
go

venue preference: ASXC,SIX,CXAD

test scenarios:

    1) new dark order qty > 3 x MXQ, split qty into 3 childs i.e. (SIGA/ASXC/CXAD).
    2) amend order qty up , rebalance additional qty into 3 childs
    3) new order qty < 1 x MXQ resting on preferred venues - SIGA
    4) new order qty > 2 x MXQ and < 3 x MXQ  resting on preferred venues - SIGA,ASXC

    5) fill 1 child order, rebalance qty into remaining childs
       5.1 - fill one child order at CXAD
       5.2 - fill one child order at ASXC
       5.3 - fill one child order at SIGA

    6) fill 1 child order on one venue, remaining qty below MXQ, remaining qty move to other venues.


    7) amend price, new price reflect to all child orders.


    8) amend qty down < 3 x MXQ, rebalance qty to SIGA/ASXC
       amend qty down < 2 x MXQ, rebalance qty to SIGA


"""
import gevent
import random
from pprint import pprint
from itertools import chain
from functools import partial
import math
import re
import pytest
from datetime import datetime,timedelta
import numpy as np

from vikingOrder import VikingOrder

from utils import (
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              getPegOrderType,
              PegType,
              AckFailed,
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
        assert child_order
        child_orders.append(child_order)
    return child_orders

def validate_child_Exchix(test_order,**kw):
    """ child will be in ASXC or SIX.

    input:
        - test_order
        - cross i.e. whether it is crossing
        - price i.e. current order price
        - qty i.e. current order qty i.e. remaining qty

    only validate working child orders. either in ASXC or SIX.

    """
    cross = kw['cross']
    price = kw['price']
    qty   = kw['qty']
    sor   = kw.get('sor')
    with_maq = kw.get("with_maq")

    child_orders = [o for o in test_order.query_child_orders() if o['orderStatusData']['primaryStatus'] != "Complete"]
    venues = [o['orderInstructionData']['subExecutionPointOverride'] for o in child_orders]
    ##check child orders not rest in CHIA 
    child_order_qtys = [o['orderStatusData']['quantityRemaining'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]
    child_order_prices = [o['orderInstructionData']['limitPrice'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]

    if cross:
        assert len(child_orders) == 2
        assert set(venues) == set(['SIX','ASXC'])
        assert np.mean(child_order_qtys)/(qty/len(child_order_qtys)) - 1 < 0.01

    else:
        assert len(child_orders) == 1
        assert venues == ['ASXC']

    assert np.sum(child_order_qtys) == qty
    ## price
    assert np.isclose(np.mean(child_order_prices),price)

def validate_child_audark(test_order,**kw):
    """ child order will be in ASXC/SIGMA/CXA. """

    cross = kw['cross']
    price = kw['price']
    qty   = kw['qty']
    sor   = kw.get('sor')
    with_maq = kw.get("with_maq")

    child_orders = [o for o in test_order.query_child_orders() if o['orderStatusData']['primaryStatus'] != "Complete"]
    venues = [o['orderInstructionData']['subExecutionPointOverride'] for o in child_orders]

    child_order_qtys = [o['orderStatusData']['quantityRemaining'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]
    child_order_prices = [o['orderInstructionData']['limitPrice'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]

    if cross:
        assert len(child_orders) == 3
        assert set(venues) == set(['SIX','ASXC','CXAD'])
        assert np.mean(child_order_qtys)/(qty/3) - 1 < 0.01
    else:
        assert len(child_orders) == 2
        assert set(venues) == set(['ASXC','CXAD'])
        assert np.mean(child_order_qtys)/(qty/2) - 1 < 0.01

    ## qty evenly distributed
    assert np.sum(child_order_qtys) == qty
    assert np.std(child_order_qtys) < 1
    ## price
    assert np.isclose(np.mean(child_order_prices),price)


class Test_AUDark:

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
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## default symbol mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        factor = 3 if cross else 2
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

        order.update(settings.DARK_ORDER_TYPES['audark'])
        print("====== order =========")
        pprint(order)

        test_order = Order(**order)
        clOrdId,_ = test_order.new()
        ## helper
        val_child_audark = partial(validate_child_audark,test_order,cross=cross,price=price)
        ## validate child order 
        val_child_audark(price=price,qty=qty)

        ##############################################
        ## amend qty up, child order evently splitted.
        price = last
        qty = qty + 10 * factor
        test_order.amend(price=price,qty=qty,timeout=20)
        ## validate child order
        val_child_audark(price=price,qty=qty)

        ################################################
        ### cancel order
        test_order.cancel()
        child_orders = query_child_orders(test_order)
        child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
        assert set(child_order_status) == set(["Complete"])

    def test_new_amend_cancel_PRE_OPEN_OkToCross(self,side,cross,symbol_depth):
        """ order basic - new/amend/cancel on PRE_OPEN, no CHA child order..

        validate:
            - new order qty equally split into working childs.
            - amend order qty up, qty equally split into working childs.
        """

        symbol,quote,quote_cha,attrs = symbol_depth.get_pre_open_symbol(top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## default symbol mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        close = float(attrs.get('CLOSEPRICE',0))
        ## 
        price = get_passive_price(side,quote,attrs=attrs)

        factor = 2 if cross else 1
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

        order.update(settings.DARK_ORDER_TYPES['audark'])

        test_order = Order(**order)
        clOrdId,_ = test_order.new()
        print("====== order =========")
        pprint(test_order)
        gevent.sleep(1)

        if cross:
            assert len(test_order._childs) == 1
        else:
            assert len(test_order._childs) == 0
            assert test_order.orderStatus.primaryStatus == "Complete"
            return

        print ("======= childs ==========")
        pprint(test_order._childs)
        ## validate child order status, qty
        child_orders = query_child_orders(test_order)

        ##  child order qty evently splitted.
        child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
        child_order_qtys = [o['orderInstructionData']['quantity'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]

        ## order rejected by exchange
        if test_order.orderStatus.primaryStatus == "Complete" and \
            test_order.orderStatus.rejectReasonType == "ExchangeReject":
                pytest.skip("test order rejected by exchange: %s, %s" % (test_order.orderId,test_order.orderStatus.rejectReasonText))

        assert np.sum(child_order_qtys) == qty
        assert np.std(child_order_qtys) < 1
        assert np.mean(child_order_qtys)/(qty/len(child_order_qtys)) - 1 < 0.01

        ##############################################
        ## amend qty up, child order evently splitted.
        qty = qty + 100
        test_order.amend(qty=qty,timeout=50)
        child_orders = query_child_orders(test_order)
        ## 
        child_order_qtys = [o['orderInstructionData']['quantity'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]

        assert np.sum(child_order_qtys) == qty
        assert np.std(child_order_qtys) < 1
        assert np.mean(child_order_qtys)/(qty/len(child_order_qtys)) - 1 < 0.01

        ##############################################
        ## amend price child order price passive.
        if side == "Buy":
            price = price  - tickSize(price,1)
        else:
            price = price  + tickSize(price,1)

        test_order.amend(price=price)
        child_orders = query_child_orders(test_order)
        ## 
        child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
        child_order_prices = [o['orderInstructionData']['limitPrice'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]
        assert np.mean(child_order_prices) - price < 0.0001

        ################################################
        ### cancel order
        test_order.cancel()
        child_orders = query_child_orders(test_order)
        child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
        assert set(child_order_status) == set(["Complete"])
        assert test_order.orderStatus.primaryStatus == "Complete"


class Test_AUCentrePoint:
    """ dark algo reseting on ASXC."""

    scenarios = []

    for crosstype in (True,False):
        for side in settings.TEST_SIDES:
            for with_maq in (True,False):
                scenarios.append({'cross':crosstype,
                                  'side': side,
                                  'with_maq': with_maq}
                                  )

    def test_new_amend_cancel_fill_on_OPEN(self,side,cross,with_maq,symbol_depth):
        """ order basic - new/amend/cancel .

        validate:
            - new order qty equally split into working childs.
            - amend order qty up, qty equally split into working childs.
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## default symbol mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        qty = random.randint(100,300) +  mxq
        order = dict(symbol = symbol,
                     side   = side,
                     price  = price,
                     qty    = qty,
                     xref   = 'FC2',
                     )
        if cross:
            order['extra'] = {'crossConsent': 'OkToCross'}

        if with_maq:
            order['maq'] = mxq

        order.update(settings.DARK_ORDER_TYPES['audarkcp'])
        test_order = Order(**order)
        clOrdId,_ = test_order.new()
        print("====== new order =========")
        pprint(test_order)

        child_orders = query_child_orders(test_order)
        ## 
        assert len(child_orders) == 1
        ## child order status in working
        assert child_orders[0]['orderStatusData']['primaryStatus'] == "Working"
        venues = [o['orderInstructionData']['subExecutionPointOverride'] for o in child_orders]
        assert venues == ['ASXC']

        assert child_orders[0]['orderInstructionData']['subExecutionPointOverride'] == 'ASXC'
        assert child_orders[0]['orderInstructionData']['orderType'] == "Pegged"
        assert child_orders[0]['orderInstructionData']['pegType'] == "Mid"
        assert  np.isclose(child_orders[0]['orderInstructionData']['limitPrice'], price)

        ## check child orders rest in ASXC 
        child_order_qtys = [o['orderInstructionData']['quantity'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]
        ## validate child order qty
        assert len(child_order_qtys) == 1
        assert np.sum(child_order_qtys) == qty

        #pytest.set_trace()
        ######################################################
        ## amend price child order price little aggressive.
        price = last
        test_order.amend(price=price,qty=qty + 10)

        child_orders = query_child_orders(test_order)
        ## 
        assert len(child_orders) == 1
        ## child order status in working
        assert child_orders[0]['orderStatusData']['primaryStatus'] == "Working"

        if with_maq:
            assert child_orders[0]['orderInstructionData']['minExecutableQuantity'] == mxq
        else:
            assert 'minExecutableQuantity' not in child_orders[0]['orderInstructionData']

        if cross:
            child_orders[0]['orderInstructionData']['crossConsent'] == "OkToCross"


        assert child_orders[0]['orderInstructionData']['subExecutionPointOverride'] == 'ASXC'
        assert child_orders[0]['orderInstructionData']['orderType'] == "Pegged"
        assert child_orders[0]['orderInstructionData']['pegType'] == "Mid"
        assert np.isclose(child_orders[0]['orderInstructionData']['limitPrice'], price)

        ## check child orders rest in ASXC 
        child_order_qtys = [o['orderInstructionData']['quantity'] for o in child_orders if o['orderStatusData']['primaryStatus'] != "Complete"]
        ## validate child order qty
        assert len(child_order_qtys) == 1
        assert np.sum(child_order_qtys) == qty + 10

        ## viking file the order
        vkOrder = VikingOrder(exch="SYDE")
        vkOrder.new(symbol=symbol,price=price,pegType="Mid",side=opposite_side(side),
                    qty=qty,allOrNone=False,tif="ImmediateOrCancel")
        vkOrder.expect("VikingExecution")

        test_order.expect("AttachExecution")
        ## validation execution at ASXC
        fills = test_order.fills
        assert len(fills) == 1
        assert np.isclose(fills[0].executionData['executionPrice'],price)
        assert fills[0].executionData['subExecutionPoint'] == "ASXC"
        assert fills[0].executionData['execFlowSpecificAustralia']['australiaTradeConditionCode'] == 'CPCXXT'

        test_order.cancel()
        ## parent order completed.
        assert test_order.orderStatus.primaryStatus == "Complete"


class Test_AUDarkExChix:
    """ dark algo exclude CXA."""

    scenarios = []

    sorTypes = (
                'audarkExchix',
               # 'audarkExchixMxq',
                )
    with_maqs = (True,False)
    for crosstype in (True,False):
        for side in settings.TEST_SIDES:
            for sor in sorTypes:
                for with_maq in with_maqs:
                    scenarios.append(
                             {'cross':crosstype,
                              'side': side,
                              'sor': sor,
                              'with_maq': with_maq,
                              }
                              )

    def test_new_amend_fill_cancel_on_OPEN(self,side,cross,sor,with_maq,symbol_depth):
        """ order basic - new/amend/cancel .

        validate:
            - new order qty equally split into working childs.
            - amend order qty up, qty equally split into working childs.
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## default symbol mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',100))
        ## check price not breach priceStep
        price = get_passive_price(side,quote)

        factor = 2
        qty = random.randint(300,500) * factor + mxq
        order = dict(symbol = symbol,
                     side   = side,
                     price  = price,
                     qty    = qty,
                     xref   = 'FC2',
                     )
        if cross:
            order['extra'] = {'crossConsent': 'OkToCross'}
        if with_maq:
            order['maq'] = with_maq

        order.update(settings.DARK_ORDER_TYPES[sor])
        test_order = Order(**order)
        clOrdId,_ = test_order.new()
        print("====== new order =========")
        pprint(test_order)

        ## helper
        val_child_Exchix = partial(validate_child_Exchix,test_order,cross=cross,sor=sor,with_maq=with_maq,price=price)
        ## validate child order 
        val_child_Exchix(price=price,qty=qty)
        #pytest.set_trace()
        ######################################################
        ## amend price child order price little aggressive.
        price = last
        test_order.amend(price=price,qty=qty+100)
        val_child_Exchix(price=price,qty=qty+100)

        ## fill order on ASXC validate rebalance
        ## viking ASXC full fill for cross or partial fill no non-cross
        vkQty = round((qty + 100)/2.0) + 1 if cross else  100
        vkOrder = VikingOrder(exch="SYDE")
        vkOrder.new(symbol=symbol,price=price,pegType="Mid",side=opposite_side(side),
                    qty=vkQty,allOrNone=False,tif="ImmediateOrCancel")
        vkOrder.expect("VikingExecution")

        test_order.expect("AttachExecution")

        fills =test_order.fills
        assert len(fills) == 1
        assert np.isclose(fills[0].executionData['executionPrice'],price)
        assert fills[0].executionData['subExecutionPoint'] == "ASXC"
        assert fills[0].executionData['execFlowSpecificAustralia']['australiaTradeConditionCode'] == 'CPCXXT'
        fillQty = fills[0].executionData['quantity']
        ###################################
        ## validate rebalance after fill
        val_child_Exchix(price=price,qty=qty+100-fillQty)

        test_order.cancel()
        ## parent order completed.
        assert test_order.orderStatus.primaryStatus == "Complete"



