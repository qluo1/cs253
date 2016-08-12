""" ATP simulated test cases for parent/child order

copy from order_atp.py, testing atp sor child.

used for simulated ATP /child order testing.

"""
import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
from datetime import datetime,timedelta
from copy import deepcopy

class PriceStyle:

    """ price type. """

    LAST = 0        # last trde
    NEARTOUCH = 1   # best passive
    FARTOUCH  = 2   # best aggressive
    MID = 3         # mid
    NBBO = 4        # mid for ASX/CHIA

def get_price(side,quote,style=PriceStyle.NEARTOUCH):
    """ return price.

    workout passive price based on side, test_instrument.

    """
    bid,ask,last = quote['bid'],quote['ask'],instrument.get("last_adj") or quote['last']

    ## note: adjusted last
    if style == PriceStyle.LAST:
        return last

    ## only for ASX for now
    if style in (PriceStyle.MID,PriceStyle.NBBO):

        if bid and ask:
            return (bid + ask)/2.0
        else:
            return None

    ## check price not breach priceStep
    if side == "Buy":

        if style == PriceStyle.NEARTOUCH:
            if bid > 0:
                return bid
        if style == PriceStyle.FARTOUCH:
            if ask > 0:
                return ask
    else:

        if style == PriceStyle.NEARTOUCH:
            if ask > 0:
                return ask

        if style == PriceStyle.FARTOUCH:
            if bid > 0:
                return bid


    return None


from utils import (
                  tickSize,
                  halfTick,
                  get_passive_price,
                  opposite_side,
                  getPegOrderType,
                  AckFailed,
                  DepthStyle,
                  )
from om2Order import Order
from vikingOrder import VikingOrder

from conf import settings

systemName = "IOSAdapter"
#systemName = "ATP_5MK4UF22"
#systemName = "PlutusChild_DEV"

class Test_ATP_Order_basic:
    """
    orderCapacity must be specified.

    """
    scenarios = []

    serviceOffers = (None,"GSST")

    test_xrefs = {
                  'HL5': "Agency",
                  'FC8':"Principal",
                  }
    ##################################
    ## default SGMX, override to SOR
    extra = {'tradingAlgorithm': "SOR_ALGO",
                'tradingAlgorithmParameters': "okToPostDark=false,okToPostExchange=true,okToPostLit=false,okToSweepAltHidden=true,okToSweepDark=false,okToSweepExchange=true,okToSweepLit=true",
                'destinationId':"SOR",
                }

    for side in settings.TEST_SIDES:
        for pegType in [None,
                        # 'MarketOrder', 'Mid', 'Ask', 'Bid', 'Last'
                        ]:
            for serviceOffer in serviceOffers:
                for xref in test_xrefs:
                    data = dict(side = side, pegType = pegType,serviceOffer=serviceOffer,xref=xref,capacity=test_xrefs[xref])
                    scenarios.append(data)

    def test_new_cancel(self,side,pegType,serviceOffer,xref,capacity,symbol_depth):
        """ order basic - new/cancel . """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True,style=DepthStyle.MIRROR)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        opp_side = opposite_side(side)

        print "symbol: ",symbol
        mxq = attrs.get("MINEXECUTABLEQTY")
        price = last

        now = datetime.utcnow()

        start = now - timedelta(hours=5)
        end = now + timedelta(hours=2)
        param = "startTime=%s,endTime=%s,notifyOrderCompletion=false,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow=20,tradeOpen=0,randomize=0" % \
                (start.strftime("%Y/%m/%d %H:%M:%S GMT"),end.strftime("%Y/%m/%d %H:%M:%S GMT"))
        parentOrder = dict(symbol = symbol,
                     side     = side,
                     price    = price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     capacity = capacity,
                     system = systemName,
                     )

        parentOrder['orderType'] = 'Limit'
        parent = Order(**parentOrder)

        clordId, er= parent.new(validate=False)
        parent.expect("OrderEntry")
        ################################
        ## setup CHIA test order
        cxa_order = VikingOrder(exch="CHIA")
        cxa_order.new(symbol=symbol,side=opp_side,price=price,qty=27)

        ###############################
        ## child sor order
        extra = deepcopy(self.extra)
        if serviceOffer:
            extra["serviceOffering"] = serviceOffer

        child = dict(parentOrderId=parent.orderId,
                     xref=xref,
                     price=price,
                     qty=200,
                     maq = 10,
                     sor=None,
                     exch="SYDE",
                     symbol=None,
                     side=side,
                     capacity=capacity,
                     system=systemName,
                     commandRequest=True,
                     crossConsent="OkToCross",
                     extra=extra,
                     )

        if pegType == 'MarketOrder':
            child['price'] = 0
            child['orderType'] = 'Market'
        elif pegType == None:
            child['orderType'] = 'Limit'
        elif pegType != None:
            child['orderType'] = 'Pegged'
            child['pegType'] = pegType

        child = Order(**child)
        print child
        #send new child order
        clOrdId,er = child.new(timeout=50)

        ## validate child order serviceOffer
        ## JIRA http://eq-trading.jira.services.gs.com/jira/browse/ANZIN-661
        if serviceOffer:
            assert child.orderInst.serviceOffering == serviceOffer
        else:
            ## servcie offer must match parent order
            assert parent.orderInst.serviceOffering == child.orderInst.serviceOffering

        ## check child fill
        try:
            if xref != "HL5":
                cxa_order.expect("VikingExecution")
                child.expect("AttachExecution")
            else:
                assert "VikingExecution" not in cxa_order.acks
                cxa_order.cancel()

        finally:
            #cancel order itself by default should validate AcceptOrderCancel
            child.cancel()
            ## ATP not actually cancel the order 
            #parent.cancel()
            print child.events()
            cxa_order.cancel()


    def test_new_amend_cancel(self,side,pegType,serviceOffer,xref,capacity,symbol_depth):
        """ order basic - new/amend/cancel . """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        print "symbol: ",symbol
        # using ticker
        #mxq = inst['attrs'].get("MINEXECUTABLEQTY")
        ## check price not breach priceStep
        price = get_passive_price(side,quote)
        ## lookup reg data
        now = datetime.utcnow()

        start = now - timedelta(hours=5)
        end = now + timedelta(hours=2)
        param = "startTime=%s,endTime=%s,notifyOrderCompletion=false,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow=20,tradeOpen=0,randomize=0" % \
                (start.strftime("%Y/%m/%d %H:%M:%S GMT"),end.strftime("%Y/%m/%d %H:%M:%S GMT"))

        parentOrder = dict(symbol = symbol,
                     side     = side,
                     price    = price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     capacity = capacity,
                     system = systemName,
                     )


        parentOrder['orderType'] = 'Limit'
        parent = Order(**parentOrder)

        clordId, er= parent.new(validate=False)
        parent.expect("OrderEntry")

        extra = deepcopy(self.extra)

        if serviceOffer:
            extra['serviceOffering'] = serviceOffer

        child = dict(parentOrderId=parent.orderId,
                     xref=xref,
                     price=price,
                     qty=200,
                     maq = 10,
                     sor=None,
                     exch="SYDE",
                     symbol=None,
                     side=side,
                     capacity = capacity,
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     extra=extra
                     )

        if pegType == 'MarketOrder':
            child['price'] = 0
            child['orderType'] = 'Market'
        elif pegType == None:
            child['orderType'] = 'Limit'
        elif pegType != None:
            child['orderType'] = 'Pegged'
            child['pegType'] = pegType

        child = Order(**child)
        pprint(child)

        #send new child order
        clOrdId,er = child.new(timeout=60)
        #amend qty down: 200 -> 100
        child.amend(qty = 100)
        child.hist()[-1].order.quantity = 100

        #amend qty up: 100 -> 250
        child.amend(qty = 250)
        child.hist()[-1].order.quantity = 250

        if pegType != 'MarketOrder':
            #amend price up
            child.amend(price = last + tickSize(last,2) )
            child.hist()[-1].order.limitPrice - (last + tickSize(last,2)) < 0.00001

        if pegType != 'MarketOrder':
            #amend price down
            child.amend(price = last - tickSize(last,2) )
            child.hist()[-1].order.limitPrice - (last - tickSize(last,2)) < 0.00001

        #amend min exec qty down: 10 -> 2
        child.amend(maq = 2 )
        child.hist()[-1].order.minExecutableQuantity == 2

        #amend min exec qty up: 2 -> 5
        child.amend(maq = 5)
        child.hist()[-1].order.minExecutableQuantity == 2

        if pegType != 'MarketOrder':
            #amend price and qty
            child.amend(price= last + tickSize(last, 10), qty = 500)
            child.hist()[-1].order.limitPrice - (last + tickSize(last, 10)) < 0.00001
            child.hist()[-1].order.quantity == 500

        if pegType != 'MarketOrder':
            #amend price and maq 
            child.amend(price= last+ tickSize(last,5), maq = 50)
            child.hist()[-1].order.limitPrice - (last + tickSize(last,5)) < 0.00001
            child.hist()[-1].order.minExecutableQuantity == 50

        if pegType != 'MarketOrder':
            #amend price, qty and maq 
            child.amend(price= last - tickSize(last,5), maq = 88, qty = 88)
            child.hist()[-1].order.minExecutableQuantity == 88
            child.hist()[-1].order.limitPrice - (last - tickSize(last,5)) < 0.00001
        #cancel order
        child.cancel()
        print child.events()

