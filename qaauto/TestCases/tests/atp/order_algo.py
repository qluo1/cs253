""" OM2 test cases for order.

test limit order basic i.e. new, amend, cancel
test FAK/FOK order
test market order reject
test SOR order priority
test stale order reject

"""
import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
from datetime import datetime,timedelta
import gevent
import logging
import numpy as np

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
from om2Order import Order
from vikingOrder import VikingOrder

from conf import settings

##################################################
## test symbol can be override within test moduel
## however, to run in xdist, don't specify symbol or
## it will cause clash between differerent process.
##################################################
#symbol = 'MFG.AX'
#symbol = 'CAP.AX'
#symbol = "ANZ.AX"

## required for atp parent order

atp_extra = {
        "interventionConsent": "NoManualIntervention",
        "smartRouteConsent": "OkToSmartRoute",
        "tradeViaInternalAlgorithm": 1,

        "algorithmicIndicator": "Algorithmic",
        "consolidatedRegulatoryCode": "Proprietary",

        "settlementDateCalcMethod": "Regular",
        "shouldIndicateOrder": 1,
        "siEligibility": "NotSiEligible",
    }


common_tags = {
        "start": "startTime=today+'08:59'",
        "end": "endTime=dayCloseTime",
        }

## switch between beta or no beta
BETA= "" # "Beta"

ALGO_ORDERS = {
        ## benchmark  matching.
        'vwap':
        {
            "sor": "HullVWAP" + BETA,
            "sorParam": "volumeLimit=20,volumeLimitType=\"OrderLifespan\",ignoreVolumeOutsideLimit=true,cleanupPrice=0,cleanupVolumeLimit=100,cleanupPercentage=100,printOneLot=false,,maxPercentageDeviation=5,benchmarkVenueType='All',auctionType=1,optFeatures=2",
            ##,CSORLitStrategy=\"SOR_AUBestPriceMinQtyUni\"",

        },

        'twap':
        {
            "sor": "TWAP" + BETA,
            "sorParam": ",volumeLimitType=\"OrderLifespan\",ignoreVolumeOutsideLimit=true,cleanupPrice=0,printOneLot=false,,benchmarkVenueType='All',auctionType=1",
        },
        ## opportunity seeking.
        'peg':
        {
            'sor': "Peg" + BETA,
            "sorParam": "notifyOrderCompletion=true,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow= 20,tradeOpen=0,randomize=true",
        },

        'iceberg':
        {
            'sor': "Iceberg" + BETA,
            "sorParam": "maxExtantPerPrice=10,randomize=true,auctionType=1",
        },

        'participate':
        {
            'sor': "Participate" + BETA,
            'sorParam':"notifyOrderCompletion=true,volumeLimit=30,volumeLimitType=\"OrderLifespan\",ignoreVolumeOutsideLimit=true,cleanupPrice=0,cleanupVolumeLimit=100,cleanupPercentage=100,printOneLot=false,,benchmarkVenueType='All',auctionType=1,",
        },

        'atpplus':
        {
            'sor': "Participate2" + BETA,
            'sorParam': "pRate=10,executionStyle=3,takeOnQueueRisk=true,benchmarkVenueType='All',notifyOrderCompletion=true"

        },
        ## sniper
        'sonar':
        {
            'sor': "Sonar" + BETA,
            'sorParam': "",
        },
        ## get done
        'piccolo':
        {
            'sor': "Piccolo" + BETA,
            'sorParam': "notifyOrderCompletion=true,maxWaitMult=0,auctionType=1",
        },

        '4cast':
        {
            'sor': "Presage" + BETA,
            "sorParam": "riskAvoidance=5,minReqComp=100,cleanupPrice=0,benchmarkVenueType='All',auctionType=1"
        },

        'onOpen':
        {
            'sor':"GSAT_Piccolo" + BETA,
            'sorParam':"startTime=today+'09:59',terminateTriggerExpr=\"period == 2\"",
        },

        'onClose':
        {
            'sor':"GSAT_Piccolo" + BETA,
            'sorParam': "startTime=closeAuctStart+'10s'"
        }
}

for key,algo in ALGO_ORDERS.iteritems():
    algo['exch'] = "SYDE"
    algo["requestResponseCommand"] = True
    algo["extra"] = atp_extra
    if key == "vwap":
        algo["extra"]["crossConsent"] = "OkToCross"

    if key not in ("onOpen","onClose"):
        start_end = "{0[start]},{0[end]}".format(common_tags)
        algo["sorParam"] = ",".join([start_end,algo["sorParam"]])

def validate_atp_child(test_order,**kw):
    """ generic validate for atp child order :


    - sum child order qtys == order qty
    - child mxq == order mxq
    - child price "better" than order price

    """
    #cross = kw['cross']
    price = kw['price']
    qty   = kw['qty']
    mxq   = float(kw['mxq'])

    active_wait(lambda: len(test_order._childs) > 0,timeout=20)

    child_orders = [o for o in test_order.query_child_orders()]
    child_orders_working = [o for o in child_orders if o['orderStatusData']['primaryStatus'] == "Working"]
    child_orders_complete = [o for o in child_orders if o['orderStatusData']['primaryStatus'] == "Complete"]
    ## child order venue
    child_venues = [o['orderInstructionData'].get('subExecutionPointOverride') or o['orderInstructionData']['executionPointOverride']
                    for o in child_orders]
    ## child working order venue
    child_working_venues = [o['orderInstructionData'].get('subExecutionPointOverride') or o['orderInstructionData']['executionPointOverride']
                    for o in child_orders_working]


    ## child order qtys
    child_working_qtys = [o['orderStatusData']['quantityRemaining'] for o in child_orders_working]
    child_complete_resons = {o['orderInstructionData'].get('subExecutionPointOverride') or o['orderInstructionData']['executionPointOverride']:
                             o['orderStatusData']['completionReason'] for o in child_orders_complete}

    child_working_mxqs = [o['orderInstructionData'].get('minExecutableQuantity') for o in child_orders_working]

    assert set(child_working_mxqs) == set([mxq])

    child_working_prices = [o['orderInstructionData']['limitPrice'] for o in child_orders_working]

    child_venue_qtys = dict(zip(child_working_venues,child_working_qtys))

    ## not all qty released.
    assert np.sum(child_working_qtys) < qty
    #assert np.std(child_working_qtys) < 1
    ## price
    #assert np.isclose(np.mean(child_working_prices),price)


## additional test parameters.
EXTRA = {"minExecutableQuantity": 30,
         "maxTrancheSize": 100,  ## iceberg order shall be ignored by om2
         }

class Test_ATP_algo:

    """test atp algo spill out child exchange order.  """
    scenarios = []

    atp_algos = (
                 'piccolo',
                 'peg',
                 'iceberg',
                 'sonar',
                 'atpplus',
                 'vwap',
                 'twap',
                 '4cast',
                 )

    for side in settings.TEST_SIDES:
        for sor in atp_algos:
            data = dict(sor=sor,side=side,xref='FA8')
            scenarios.append(data)

    def test_atp_order(self,side,sor,xref,symbol_depth):
        """ atp peg order. """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        print "symbol: ", symbol

        side_pass = opposite_side(side)
        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_aggr_2 = last + tickSize(last,2)
            price_pass = last - tickSize(last,1)
            price_pass_2 = last - tickSize(last,2)
        else:
            price_aggr = last - tickSize(last,1)
            price_aggr_2 = last - tickSize(last,2)
            price_pass = last + tickSize(last,1)
            price_pass_2 = last + tickSize(last,2)


        order = dict(symbol =symbol,
                     side   =side,
                     price  =price_aggr_2,
                     qty    =random.randint(1000,2000),
                     xref   =xref,
                     )

        tags = ALGO_ORDERS[sor]
        order.update(tags)
        if order.get("extra"):
            assert isinstance(order["extra"],dict)
            order["extra"].update(EXTRA)
        else:
            order['extra'] = EXTRA
        ## test order
        test_order = Order(**order)
        ## fac/vk aggressive order to cause market trade
        #pytest.set_trace()
        vkorder = VikingOrder(exch="SYDE")
        try:
            ###########################################
            clOrdId,_ = test_order.new()
            test_order.expect_ok()
            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
            #pytest.set_trace()
            test_order.expect("SetTradingAlgorithmEngine")

            ## wait for atp to createChildOrderCommand
            test_order.expect("UpdateOrderStatus",timeout=300)
            ## validate child orders
            validate_atp_child(test_order,price=price_aggr_2,qty = order['qty'],mxq=EXTRA["minExecutableQuantity"])

            assert test_order._childs
            assert len(test_order._childs) >= 1
            ## query order image
            #child = test_order.requestOrderImage(test_order._childs[0])
            #print "child order inst: ",  child["orderInstructionData"]

            ## aggressive fac order to generate fill
            #fac_order.new()
            #fac_order.expect("AttachExecution",timeout=3)
            assert vkorder.new(symbol=symbol,
                               side=side_pass,
                               price=price_pass_2,
                               qty=order["qty"] + 1000), vkorder._acks

            vkorder.expect("VikingExecution")
            ## atp order fill
            test_order.expect("AttachExecution",timeout=5)
            print "atp fills: ", test_order.fills

        finally:
           ### clean up
           # if test_order.orderStatus.primaryStatus == "Working":
           #     test_order.cancel(validate=False)
           # ## if fac_order submitted
           # if vkorder.acks:
           #     vkorder.cancel()
            ## sleep wait for ATP engine resource available
            gevent.sleep(50)

class Test_ATP_Auction:

    """ test onOpen, onClose alto. """
    scenarios = []

    for sor in ("onOpen","onClose"):
        data = dict(sor=sor,side="Buy",xref='FA8')
        scenarios.append(data)

    #@pytest.mark.skipif("True")
    def test_order(self,side,sor,xref,symbol_depth):
        """ atp auction order. """
        quote, cha_quote, attrs = symbol_depth.get_pre_open_symbol()

        symbol = quote['symbol']
        last = quote['last']
        print "symbol: ", symbol
        #pytest.set_trace()
        order = dict(symbol =symbol,
                     side   =side,
                     price  =last,
                     qty    =random.randint(1000,2000),
                     xref   =xref,
                     )

        tags = ALGO_ORDERS[sor]
        order.update(tags)
        ##
        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)
        #pytest.set_trace()
        test_order.expect("SetTradingAlgorithmEngine")
        ## wait for atp to createChildOrderCommand
        test_order.expect("UpdateOrderStatus",timeout=120)
        assert test_order._childs
        assert len(test_order._childs) >= 1
        ## query order image
        child = test_order.requestOrderImage(test_order._childs[0])
        print "child order inst: ",  child["orderInstructionData"]

class Test_ATP_VWAP_SIGA:
    """ setup resting order 1) ATP VWAP, 2) SIGMAX

    expect: order cross within sigma dark pool.
    """
    scenarios = []

    data = dict(sor='vwap',side="Buy",xref='FC8')
    scenarios.append(data)

    def test_order(self,sor,side,xref,symbol_depth):
        """
        """
        for i  in range(10):
            if i != 0: gevent.sleep(50) ## ATP no engine capacity for load
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,pid=i)
            print "symbol: ",symbol
            last = quote['last']
            #pytest.set_trace()
            side_pass = opposite_side(side)
            if side == 'Buy':
                price_aggr = last + tickSize(last,1)
                price_aggr_2 = last + tickSize(last,2)
                price_pass = last - tickSize(last,1)
                price_pass_2 = last - tickSize(last,2)
            else:
                price_aggr = last - tickSize(last,1)
                price_aggr_2 = last - tickSize(last,2)
                price_pass = last + tickSize(last,1)
                price_pass_2 = last + tickSize(last,2)

            order = dict(symbol =symbol,
                         side   =side,
                         price  =last,
                         qty    =random.randint(10000,20000),
                         xref   =xref,
                         )

            tags = ALGO_ORDERS[sor]
            order.update(tags)

            #pytest.set_trace()
            ##
            if order.get("extra"):
                assert isinstance(order["extra"],dict)
                order["extra"].update(EXTRA)
            else:
                order['extra'] = EXTRA
               ##
            test_order = Order(**order)
            ###########################################
            clOrdId,_ = test_order.new()
            test_order.expect_ok()
            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)

            ## sigma-X Sor order
            dark = order.copy()
            dark["side"] = side_pass
            dark["xref"] = "FC2"
            dark["price"] = price_pass_2
            dark["qty"] = 2000
            dark.pop("sorParam")
            dark.pop("extra")
            dark.update(settings.DARK_ORDER_TYPES["sigmax"])

            dark_order = Order(**dark)
            clOrdId,_ = dark_order.new()
            acks =  dark_order.events(clOrdId)
            print "dark orderId,%s, %s" % (dark_order.orderId,acks)

class Test_ALGO_TAG:

    """
    test atp tags for various order option.

    """
    scenarios = []

    for sor in ALGO_ORDERS:
        if sor != "atpplus": continue
        data = dict(sor=sor,side="Buy",xref='FA8')
        scenarios.append(data)

    @pytest.mark.skipif("True")
    def test_order(self,side,sor,xref,symbol_depth):
        """ atp peg order. """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        print "symbol: ",symbol
        #pytest.set_trace()
        order = dict(symbol =symbol,
                     side   =side,
                     price  =last,
                     qty    =random.randint(1000,2000),
                     xref   =xref,
                     )

        tags = ALGO_ORDERS[sor]
        order.update(tags)

        test_order = Order(**order)
        ###########################################
        clOrdId,_ = test_order.new()
        test_order.expect_ok()
        acks =  test_order.events()
        print "orderId,%s, %s" % (test_order.orderId,acks)
        import pdb;pdb.set_trace()

