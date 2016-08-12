""" test SOR_AUDark mxq.

AUDark is to replace ATP sonarDark algo.

desiged as data driven tests for mxq.

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


TEST_CASES_NEW_AMEND = {
        ## qty > 3 * mxq , cross
        'new_1': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        },
                        'expect': { 'SIX': {'qty': 100}, 'ASXC': {'qty': 100} ,'CXAD': {'qty': 100},},
            },

        ## qty > 3 * qty , not cross
        'new_2': {'data': {
                        'qty': 100,
                        'mxq': 10,
                        'cross': False,
                        },
                        'expect': { 'ASXC': {'qty': 50},'CXAD': {'qty': 50} },
            },

        ## qty == 2 * mxq, resting on preferred venues
        'new_3': {'data': {
                        'qty': 100,
                        'mxq': 50,
                        'cross': True,
                        },
                        'expect': { 'SIX': {'qty': 50}, 'ASXC': {'qty': 50}, },
            },

        ## qty > 2 * mxq and < 3 * mxq, resting on preferred venues
        'new_3_1': {'data': {
                        'qty': 120,
                        'mxq': 50,
                        'cross': True,
                        },
                        'expect': {'SIX': {'qty': 50}, 'ASXC': {'qty': 120 - 50}, },
            },
        ## qty > 2 * mxq and < 3 * mxq, resting on preferred venues
        'new_4': {'data': {
                        'qty': 120,
                        'mxq': 50,
                        'cross': False,
                        },
                        'expect': {'ASXC': {'qty': 60}, 'CXAD': {'qty': 60}, },
            },

        ## qty =< 1 * mxq 
        'new_5': {'data': {
                        'qty': 120,
                        'mxq': 120,
                        'cross': True,
                        },
                        'expect': {'ASXC': {'qty': 120,}, },
            },
        ## qty >= 1*mxq < 2 *mxq  and cross = False
        'new_6': {'data': {
                        'qty': 120,
                        'mxq': 120,
                        'cross': False,
                        },
                        'expect': {'ASXC': {'qty': 120,}, },
            },
        ## qty < 1 * mxq  and cross = True, order rejected
        'new_7': {'data': {
                        'qty': 100,
                        'mxq': 120,
                        'cross': True,
                        },
                        'expect': { 'ASXC':{'qty': 100}} ,
            },
        'new_8': {'data': {
                        'qty': 100,
                        'mxq': 120,
                        'cross': False,
                        },
                        'expect': {'ASXC': {'qty': 100}} ,
            },

        ## qty > 3 * mxq , cross
        'amend_1': {'data': {
                        'qty': (300,600),
                        'mxq': 10,
                        'cross': True,
                        },
                        'expect': { 'SIX': {'qty': 200}, 'ASXC': {'qty': 200} ,'CXAD': {'qty': 200},},
            },
        ## qty > 3 * mxq , cross
        'amend_2': {'data': {
                        'qty': (300,600),
                        'mxq': 10,
                        'cross': False,
                        },
                        'expect': { 'ASXC': {'qty': 300} ,'CXAD': {'qty': 300},},
            },
        ## amend qty down to 2*mxq, cross
        'amend_3': {'data': {
                        'qty': (300,200),
                        'mxq': 100,
                        'cross': True,
                        },
                        'expect': { 'SIX': {'qty': 100}, 'ASXC': {'qty': 100}},
            },
        # amend qty down to < 2 * mxq for no cross
        'amend_4': {'data': {
                        'qty': (300,120),
                        'mxq': 100,
                        'cross': False,
                        },
                        'expect': { 'ASXC': {'qty': 120}},
            },
        ## amend qty down to < 2*mxq and > 1*mxq, cross
        'amend_5': {'data': {
                        'qty': (600,120),
                        'mxq': 100,
                        'cross': True,
                        },
                        'expect': { 'ASXC': {'qty': 120}}, ## TODO: confirm not SIX??
            },
        # amend qty down to < 2 * mxq for no cross
        'amend_6': {'data': {
                        'qty': (300,120),
                        'mxq': 100,
                        'cross': False,
                        },
                        'expect': { 'ASXC': {'qty': 120}},
            },
        ## amend qty down to < 1*mxq, cross
        'amend_7': {'data': {
                        'qty': (600,80),
                        'mxq': 100,
                        'cross': True,
                        },
                        'expect': { 'ASXC': {'qty': 80}},
            },
        # amend qty down to < 1 * mxq for no cross
        'amend_8': {'data': {
                        'qty': (600,80),
                        'mxq': 100,
                        'cross': False,
                        },
                        'expect': { 'ASXC': {'qty': 80}},
            },

}
TEST_CASES_FILL = {

        ## qty > 3 * mxq , cross, full fill trigger rebalance.
        'fill_1': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        'fills': [('ASXC',100)],
                        },
                        'expect': { 'SIX': {'qty': 66}, 'ASXC': {'qty': 68} ,'CXAD': {'qty': 66},},
            },
        ## qty > 3 * mxq , not cross, no rebalanc, partial fill not trigger rebalance for external venue
        'fill_2': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': False,
                        'fills': [('ASXC', 100)],
                        },
                        'expect': { 'ASXC': {'qty': 50} ,'CXAD': {'qty': 150},},
            },

        ## qty > 3 * mxq , cross, partial fill, remaining qty above mxq, no rebalance for external venue.
        'fill_3': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        'fills': [('ASXC', 50)],
                        },
                        'expect': { 'SIX': {'qty': 100}, 'ASXC': {'qty': 50} ,'CXAD': {'qty': 100},},
            },

        ###########################################################################################
        ## qty > 3 * mxq , cross, partial fill, remaining qty below mxq will not trigger rebalance
        ## a known issue : 
        'fill_4': {'data': {
                        'qty': 300,
                        'mxq': 80,
                        'cross': True,
                        'fills': [('ASXC', 80)],
                        },
                        'expect': { 'SIX': {'qty': 100}, 'ASXC': {'qty': 20} ,'CXAD': {'qty': 100},},
            },


        ## qty > 3 * mxq , cross, full fill trigger rebalance.
        'fill_1_cxad': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        'fills': [('CXAD', 100)],
                        },
                        'expect': { 'SIX': {'qty': 66}, 'ASXC': {'qty': 68} ,'CXAD': {'qty': 66},},
            },
        ## qty > 3 * mxq , not cross, no rebalanc, partial fill not trigger rebalance for external venue
        'fill_2_cxad': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': False,
                        'fills': [('CXAD', 100)],
                        },
                        'expect': { 'ASXC': {'qty': 150} ,'CXAD': {'qty': 50},},
            },

        ## qty > 3 * mxq , cross, partial fill, remaining qty above mxq, no rebalance for external venue.
        'fill_3_cxad': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        'fills': [('CXAD', 50)],
                        },
                        'expect': { 'SIX': {'qty': 100}, 'ASXC': {'qty': 100} ,'CXAD': {'qty': 50},},
            },

        ###########################################################################################
        ## qty > 3 * mxq , cross, partial fill, remaining qty below mxq will not trigger rebalance
        ## a known issue : 
        'fill_4_cxad': {'data': {
                        'qty': 300,
                        'mxq': 80,
                        'cross': True,
                        'fills': [('CXAD', 80)],
                        },
                        'expect': { 'SIX': {'qty': 100}, 'ASXC': {'qty': 100} ,'CXAD': {'qty': 20},},
            },
        ## qty > 3 * mxq , cross, full fill trigger rebalance.
        'fill_1_six': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        'fills': [('SIX', 100)],
                        },
                        'expect': { 'SIX': {'qty': 66}, 'ASXC': {'qty': 68} ,'CXAD': {'qty': 66},},
            },
        ## qty > 3 * mxq , cross, partial fill, remaining qty above mxq, no rebalance for external venue.
        'fill_3_six': {'data': {
                        'qty': 300,
                        'mxq': 10,
                        'cross': True,
                        'fills': [('SIX', 50)],
                        },
                        'expect': { 'SIX': {'qty': 50}, 'ASXC': {'qty': 100} ,'CXAD': {'qty': 100},},
            },
        ## for SIX qty below mxq shall be cancelled or rebalanced i.e. cancel CXAD. 
        'fill_4_six': {'data': {
                        'qty': 300,
                        'mxq': 80,
                        'cross': True,
                        'fills': [('SIX', 80)],
                        },
                        'expect': { 'SIX': {'qty': 80}, 'ASXC': {'qty': 140},},
            },

        ##fill multiple venues , partial fill SIX, ASXC, rebalance to ASXC
        'fill_1_asxc_six': {'data': {
                        'qty': 300,
                        'mxq': 80,
                        'cross': True,
                        'fills': [('ASXC', 80),('SIX', 80)],
                        },
                        'expect': { 'ASXC': {'qty': 140},},
            },

        ##multiple fill ASXC, will generate fill below mxq 
        'fill_2_asxc_asxc': {'data': {
                        'qty': 300,
                        'mxq': 80,
                        'cross': True,
                        'fills': [('ASXC', 80),('ASXC', 20)],
                        },
                        'expect': { 'ASXC': {'qty': 120},'SIX':{'qty': 80},},
            },
        ##multiple fill ASXC, will generate fill below mxq 
        'fill_2_cxad_cxad': {'data': {
                        'qty': 300,
                        'mxq': 80,
                        'cross': True,
                        'fills': [('CXAD', 80),('CXAD', 20)],
                        },
                        'expect': { 'ASXC': {'qty': 120},'SIX':{'qty': 80},},
            },

    }

def validate_child_audark(test_order,expect, **kw):
    """ validate child order based on expected:

    - venue child qty match expected.
    - mxq match specified.
    - evently distributed ??

    """

    cross = kw['cross']
    price = kw['price']
    qty   = kw['qty']
    mxq   = float(kw['mxq'])
    sor   = kw.get('sor')

    child_orders = [o for o in test_order.query_child_orders()]
    child_orders_working = [o for o in child_orders if o['orderStatusData']['primaryStatus'] == "Working"]
    child_orders_complete = [o for o in child_orders if o['orderStatusData']['primaryStatus'] == "Complete"]
    ## child order venue
    child_venues = [o['orderInstructionData']['subExecutionPointOverride'] for o in child_orders]
    child_working_venues = [o['orderInstructionData']['subExecutionPointOverride'] for o in child_orders_working]


    ## child order qtys
    child_working_qtys = [o['orderStatusData']['quantityRemaining'] for o in child_orders_working]
    child_complete_resons = {o['orderInstructionData']['subExecutionPointOverride']:
                             o['orderStatusData']['completionReason'] for o in child_orders_complete}


    child_order_mxqs = [o['orderInstructionData']['minExecutableQuantity'] for o in child_orders_working]

    assert set(child_order_mxqs) == set([mxq])

    child_working_prices = [o['orderInstructionData']['limitPrice'] for o in child_orders_working]

    child_venue_qtys = dict(zip(child_working_venues,child_working_qtys))

    assert isinstance(expect,dict)
    for venue,data in expect.iteritems():
        _qty = data['qty']
        assert venue in child_venues
        assert venue in child_working_venues,child_complete_resons
        assert _qty == child_venue_qtys[venue],child_complete_resons
    if len(expect) == 0:
        ##order shall be rejected.
        assert test_order.orderStatus.primaryStatus == "Complete"
        return

    ## qty evenly distributed
    assert np.sum(child_working_qtys) == qty
    #assert np.std(child_working_qtys) < 1
    ## price
    assert np.isclose(np.mean(child_working_prices),price)

### helper for fill on dark venue
def fill_asxc(symbol,side,qty,price,**kw):
    """ viking order IOC fill on ASXC """
    validate = kw.get("validate",True)

    vkOrder = VikingOrder(exch="SYDE")
    vkOrder.new(symbol=symbol,price=price,pegType="Mid",side=side,
                qty=qty,allOrNone=False,tif="ImmediateOrCancel")
    if validate:
        vkOrder.expect("VikingExecution")
    else:
        return vkOrder

def fill_cxad(symbol,side,qty,price,**kw):
    """ viking order IOC/CXAD """

    validate = kw.get("validate",True)

    pegType = "Ask" if side == "Buy" else "Bid"
    vkOrder = VikingOrder(exch="CHIA")
    vkOrder.new(symbol=symbol,price=price,pegType=pegType,side=side,
                qty=qty,allOrNone=False,tif="ImmediateOrCancel")
    if validate:
        vkOrder.expect("VikingExecution")
    else:
        return vkOrder

def fill_six(symbol,side,qty,price,**kw):
    """ fill on SIX. """

    validate = kw.get("validate",True)

    order_t = {'symbol': symbol,
               'side': side,
               'price': price,
               'qty': qty,
               'allOrNone': False,
               'xref': "FA8",
    }
    order_t.update(settings.DARK_ORDER_TYPES['sigmax'])
    order = Order(**order_t)
    order.new()

    if validate:
        order.expect("AttachExecution",timeout=10)

        if order.orderStatus.primaryStatus != "Complete":
            order.cancel()
    else:
        return order

class Test_AUDark_MXQ_NewAmend:

    scenarios = []

    for crosstype in (True,False):
        for side in settings.TEST_SIDES:
            for label in TEST_CASES_NEW_AMEND:
                for xref in ("FC1",
                             "MD1",
                             ):
                    scenarios.append(dict(side=side,xref=xref,label=label))

    def test_new_amend_order(self,side,xref,label,symbol_depth):
            """ order basic - new audark sor .

            validate: based on expected.

            """
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
            bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

            ## check price not breach priceStep
            price = get_passive_price(side,quote)

            test = TEST_CASES_NEW_AMEND[label]
            data = test['data']
            if type(data['qty']) == int:
                qty = data['qty']
                amdQty = None
            else:
                assert isinstance(data['qty'],tuple)
                qty,amdQty =data['qty']

            expect = test['expect']

            order = dict(symbol = symbol,
                         side   = side,
                         price  = price,
                         qty    = qty,
                         xref   = xref,
                         maq    = data['mxq'],
                         )
            if data['cross']:
                order['extra'] = {'crossConsent': 'OkToCross'}

            order.update(settings.DARK_ORDER_TYPES['audark'])

            test_order = Order(**order)
            clOrdId,_ = test_order.new()
            print("====== order =========")
            pprint(test_order)

            try:
                ## amend qty
                if amdQty:
                    test_order.amend(qty=amdQty)
                    qty = amdQty

                ## validate child orders.
                validate_child_audark(test_order,expect,
                                      cross=data['cross'],
                                      price=price,qty=qty,
                                      mxq=min(data['mxq'],qty))

            finally:
                ################################################
                ### cancel order
                print test_order.events()
                test_order.cancel()
                child_orders = test_order.query_child_orders()
                child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
                assert set(child_order_status) == set(["Complete"])
                assert test_order.orderStatus.primaryStatus == "Complete"


class Test_AUDark_MXQ_Fill:

    scenarios = []

    for crosstype in (True,False):
        for side in settings.TEST_SIDES:
            for label in TEST_CASES_FILL:
                for xref in ("FC1",
                             "MD1",
                             ):
                    scenarios.append(dict(side=side,xref=xref,label=label))

    def test_fill_order(self,side,xref,label,symbol_depth):
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
            bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

            ## check price not breach priceStep
            price = get_passive_price(side,quote)

            test = TEST_CASES_FILL[label]
            data = test['data']
            qty  = data['qty']
            fills = data['fills']
            expect = test['expect']

            order = dict(symbol = symbol,
                         side   = side,
                         price  = price,
                         qty    = qty,
                         xref   = xref,
                         maq    = data['mxq'],
                         )
            if data['cross']:
                order['extra'] = {'crossConsent': 'OkToCross'}

            order.update(settings.DARK_ORDER_TYPES['audark'])

            test_order = Order(**order)
            clOrdId,_ = test_order.new()
            print("====== order =========")
            pprint(test_order)

            try:

                ## amend price aggressive.
                price = last
                test_order.amend(price=price,validate=False)
                test_order.expect("AcceptOrderCorrect",timeout=30)

                ## try to fill on dark venue
                fillQty = 0
                fillOrders = []
                assert isinstance(fills,list)
                for _venue,_qty in fills:
                    op_side = opposite_side(side)
                    if _venue == "ASXC":
                        _order = fill_asxc(symbol=symbol,side=op_side,qty=_qty,price=price,validate=False)
                    elif _venue == "CXAD":
                        _order = fill_cxad(symbol=symbol,side=op_side,qty=_qty,price=price,validate=False)
                    elif _venue == "SIX":
                        _order = fill_six(symbol=symbol,side=op_side,qty=_qty,price=price,validate=False)
                    else:
                        assert False, "unknown venue: %s" % _venue

                    fillOrders.append(_order)
                    fillQty += _qty

                ## validate fill orders got fill.
                for _order in fillOrders:
                    if isinstance(_order,VikingOrder):
                        _order.expect("VikingExecution")
                    else:
                        if _order.orderStatus.primary == "Working":
                            _order.cancel()
                        _order.expect("AttachExecution")
                ## validate test order got fill.
                test_order.expect("AttachExecution")

                gevent.sleep(5)
                ## validate child orders.
                validate_child_audark(test_order,expect,
                                      cross=data['cross'],
                                      price=price,qty=qty-fillQty,
                                      mxq=min(data['mxq'],qty-fillQty))
            finally:
                ################################################
                ### cancel order
                #pytest.set_trace()
                print test_order.events()
                test_order.cancel()
                child_orders = test_order.query_child_orders()
                child_order_status = [o['orderStatusData']['primaryStatus'] for o in child_orders]
                assert set(child_order_status) == set(["Complete"])
                assert test_order.orderStatus.primaryStatus == "Complete"
