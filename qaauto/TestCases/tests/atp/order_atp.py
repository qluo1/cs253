""" ATP simulated test cases for parent/child order

ATP Algo parent order is a simulated order, ATP will ignore this order, therefore, no ack or OrderAccept.
Algo child order is generated to simulate ATP createChildOrderCommand, and
Child order shall be accepted and processed by PlutusOM2Adapter/OM2OrderReceiver.

"""
import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
from datetime import datetime,timedelta

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
                  )
from om2Order import Order

from conf import settings

systemName = "IOSAdapter"
#systemName = "ATP_5MK4UF22"
#systemName = "PlutusChild_DEV"


class Test_ATP_Order_basic:
    """
    """

    scenarios = []

    serviceOffers = (None,"GSST")

    test_xrefs = [
                  'HL5',
                  'FC8',
                  ]
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
                    data = dict(side = side, pegType = pegType,serviceOffer=serviceOffer,xref=xref)
                    scenarios.append(data)

    def test_new_cancel(self,side,pegType,serviceOffer,xref,symbol_depth):
        """ order basic - new/cancel . """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        print "symbol: ",symbol
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
                     capacity = "Agency",
                     system = systemName,
                     )

        parentOrder['orderType'] = 'Limit'
        parent = Order(**parentOrder)

        clordId, er= parent.new(validate=False)
        parent.expect("OrderEntry")
        ###############################
        ## child sor order

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
                     capacity = "Agency",
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     extra=self.extra
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

        #cancel order itself by default should validate AcceptOrderCancel
        child.cancel()
        ## ATP not actually cancel the order 
        #parent.cancel()
        print child.events()

    @pytest.mark.basic
    def test_new_amend_cancel(self,side,pegType,serviceOffer,xref,symbol_depth):
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
                     capacity = "Principal",
                     system = systemName,
                     )


        parentOrder['orderType'] = 'Limit'
        parent = Order(**parentOrder)

        clordId, er= parent.new(validate=False)
        parent.expect("OrderEntry")

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
                     capacity = "Principal",
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     extra=self.extra
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

    def _val_fill(self,order,last):
        """ helper for validate execution. """
        assert len(order.fills) > 0
        for fill in order.fills:
            assert fill.executionData["subExecutionPoint"] == "SIGA"
            assert fill.executionData["executionLastMarket"] == "SIGA"
            assert fill.executionData["executionPrice"] - last < 0.0001
            ## validate versus account for cross
            ## {u'accountAliases': [{u'accountSynonym': u'043947290', u'accountSynonymType': u'AmAccountNumber'}],        
            versus = [i for i in fill.executionData["accounts"] if i["accountRole"] == "Versus"]
            assert len(versus) == 1
            assert versus[0]["accountAliases"][0]["accountSynonym"] == u'043947290' ,"incorrect cross trade versus account"

        print "validated fill: %d" % len(order.fills)

    def test_new_fill_amend_cancel(self,side,pegType,serviceOffer,xref,symbol_depth):
        """ order basic - new/fill/amend/cancel . """

        o_side = opposite_side(side)

        inst = test_instrument.get()
        symbol = inst['symbol']
        print "symbol: ", symbol

        # using ticker
        quote = inst['quote']
        last = inst.get('last_adj') or quote['last']
        #mxq = inst['attrs'].get("MINEXECUTABLEQTY")
        depth.clear_depth(symbol=symbol,last=last,build=True)
        ## get updated depth info
        inst = test_instrument.get()
        ## check price not breach priceStep
        price = get_price(side,inst,PriceStyle.LAST)
        agg_price = get_price(o_side,inst,PriceStyle.FARTOUCH)
        #print agg_price
        ## lookup reg data
        now = datetime.utcnow()

        start = now - timedelta(hours=5)
        end = now + timedelta(hours=2)
        param = "startTime=%s,endTime=%s,notifyOrderCompletion=false,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow=20,tradeOpen=0,randomize=0" % \
                (start.strftime("%Y/%m/%d %H:%M:%S GMT"),end.strftime("%Y/%m/%d %H:%M:%S GMT"))

        order1 = dict(symbol   = symbol,
                     side     = side,
                     price    = price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     serviceOffering = "Programtrading",
                     system = systemName
                     )

        parent1 = Order(**order1)

        # send parent order
        clordId1, er= parent1.new(validate=False)
        parent1.expect("OrderEntry")

        extra = {}
        if serviceOffer:
            extra['serviceOffering'] = serviceOffer


        child1 = dict(parentOrderId=parent1.orderId,
                     xref=xref,
                     price=price,
                     qty=200,
                     sor=None,
                     exch="SYDE",
                     symbol=None,
                     side=side,
                     #capacity = "Principal",
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     extra=extra
                     )

        if pegType == 'MarketOrder':
            child1['price'] = 0
            child1['orderType'] = 'Market'
        elif pegType == None:
            child1['orderType'] = 'Limit'
        elif pegType != None:
            child1['orderType'] = 'Pegged'
            child1['pegType'] = pegType

        print child1 
        child1 = Order(**child1)

        #send new child order
        clOrdId1,er1 = child1.new()

        #amend child 1 qty to 300 and set maq = 200 
        child1.amend(qty=300, maq = 200)

        xref = "FC2"
        #opposing order
        order2 = dict(symbol   = symbol,
                     side     = o_side,
                     price    = agg_price,
                     qty      = random.randint(100,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     serviceOffering = "GSST",
                     system = systemName,
                     )

        parent2 = Order(**order2)

        # send parent order 2
        clordId2, er = parent2.new(validate=False)
        parent2.expect("OrderEntry")

        extra = {'serviceOffering' : 'GSST'}

        child2 = dict(parentOrderId=parent2.orderId, xref=xref, price=agg_price, qty=103, sor=None,
                      exch="SYDE", symbol=None,maq = 15, side=o_side,system = systemName, extra = extra)
        child2 = Order(**child2)

        # send child order 2
        clOrdId2,er = child2.new()
        time.sleep(5)

        assert child1.orderStatus.primaryStatus == 'Working'
        assert child2.orderStatus.primaryStatus == 'Working'
        #import pdb;pdb.set_trace()

        # No trade yet because child 1 has a maq of 200
        child1.amend(maq = 100)
        #Expect the both child orders have a trade 
        ## plutus took long time to complete
        child1.expect("AttachExecution",timeout=120)
        assert child1.orderStatus.primaryStatus == 'Working'
        self._val_fill(child1,last)
        #assert len(child1.fills) > 0
        #assert child1.fills[0].executionData["subExecutionPoint"] == "SIGA"
        #assert child1.fills[0].executionData["executionLastMarket"] == "SIGA"
        print "child1", child1.events()

        child2.expect("AttachExecution")
        assert child2.orderStatus.primaryStatus == 'Complete'
        self._val_fill(child2,last)
        #assert len(child2.fills) > 0
        #assert child2.fills[0].executionData["subExecutionPoint"] == "SIGA"
        #assert child2.fills[0].executionData["executionLastMarket"] == "SIGA"
        #assert child2.fills[0].executionData["executionPrice"] - last < 0.0001
        ### validate versus account for cross
        ### {u'accountAliases': [{u'accountSynonym': u'043947290', u'accountSynonymType': u'AmAccountNumber'}],        
        #assert child2.fills[0].executionData["accountAliases"]["accountSynonym"] == u'043947290' ,"incorrect cross trade versus account"

        print "child2", child2.events()

        # try to modify child 1 when order is partially filled

        #amend quantity up // amend qty down is rejected by Om2 for partially filled orders
        child1.amend(qty = 300)

        #amend quantity down
        child1.amend(qty = 250)

        if pegType != 'MarketOrder':
            #amend price
            child1.amend(price = last + tickSize(last,2) )

        #amend min exec qty
        child1.amend(maq = 2 )

        if pegType != 'MarketOrder':
            #amend price and qty
            child1.amend(price= last + tickSize(last, 10), qty = 400)

        if pegType != 'MarketOrder':
            #amend price and maq 
            child1.amend(price= last+ tickSize(last,5), maq = 50)

        if pegType != 'MarketOrder':
            #amend price, qty and maq 
            child1.amend(price= last - tickSize(last,5), maq = 22, qty = 350)

        #cancel child 1
        child1.cancel()
        assert child1.orderStatus.primaryStatus == 'Complete'


    def test_new_fill2_amend_cancel(self,side,pegType,serviceOffer,xref,symbol_depth):
        """ order basic - new/fill/amend/cancel . """


        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        print "symbol: ",symbol

        o_side = opposite_side(side)
        ## check price not breach priceStep
        price = get_price(side,quote,PriceStyle.LAST)
        agg_price = get_price(o_side,quote,PriceStyle.FARTOUCH)
        pass_price = get_price(o_side,quote,PriceStyle.NEARTOUCH)
        #print agg_price
        ## lookup reg data
        now = datetime.utcnow()

        start = now - timedelta(hours=5)
        end = now + timedelta(hours=2)
        param = "startTime=%s,endTime=%s,notifyOrderCompletion=false,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow=20,tradeOpen=0,randomize=0" % \
                (start.strftime("%Y/%m/%d %H:%M:%S GMT"),end.strftime("%Y/%m/%d %H:%M:%S GMT"))
        xref = "FC1"
        order1 = dict(symbol   = symbol,
                     side     = side,
                     price    = price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     serviceOffering = "ProgramTrading",
                     system = systemName
                     )

        parent1 = Order(**order1)

        # send parent order
        clordId1, er= parent1.new(validate=False)
        parent1.expect("OrderEntry")

        extra = {}
        if serviceOffer:
            extra['serviceOffering'] = serviceOffer


        child1 = dict(parentOrderId=parent1.orderId,
                     xref=xref,
                     price=price,
                     qty=200,
                     sor=None,
                     exch="SYDE",
                     symbol=None,
                     side=side,
                     capacity = "Principal",
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     extra=extra
                     )

        if pegType == 'MarketOrder':
            child1['price'] = 0
            child1['orderType'] = 'Market'
        elif pegType == None:
            child1['orderType'] = 'Limit'
        elif pegType != None:
            child1['orderType'] = 'Pegged'
            child1['pegType'] = pegType

        # send child order 1
        child1 = Order(**child1)
        clOrdId1,er1 = child1.new()

        #amend child 1 qty to 300 
        child1.amend(qty=300)

        ## FC8 should be NXXT, FC2/FC1 should be BPXT
        xref = random.choice(["FC8","FC2"])
        ##opposing order
        order2 = dict(symbol   = symbol,
                     side     = o_side,
                     price    = agg_price,
                     qty      = random.randint(300,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     serviceOffering = serviceOffer,
                     system = systemName,
                     )

        parent2 = Order(**order2)

        # send parent order 2
        clordId2, er = parent2.new(validate=False)
        parent2.expect("OrderEntry")

        extra = {}
        if serviceOffer:
            extra["serviceOffering"] = serviceOffer


        child2 = dict(parentOrderId=parent2.orderId,
                     xref=xref,
                     price=agg_price,
                     qty=200,
                     sor=None,
                     exch="SYDE",
                     symbol=None,
                     side=o_side,
                     capacity = "Principal",
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     extra=extra
                     )

        child2['price'] = 0
        child2['orderType'] = 'Market'
        child2 = Order(**child2)

        # send child order 2
        clOrdId2,er = child2.new()

        #Expect the both child orders have a trade 
        child1.expect("AttachExecution",timeout=120)
        assert child1.orderStatus.primaryStatus == 'Working'
        self._val_fill(child1,last)

        child2.expect("AttachExecution")
        assert child2.orderStatus.primaryStatus == 'Complete'
        self._val_fill(child2,last)

        #cancel child 1
        child1.cancel()
        assert child1.orderStatus.primaryStatus == 'Complete'


    def test_new_multi_fill_amend_cancel(self,side,pegType,serviceOffer,xref,symbol_depth):
        """ order basic - new/fill/amend/cancel .

        should generate BPXT trade report due to FC1/FC2 in same group.

        """

        o_side = opposite_side(side)

        inst = test_instrument.get()
        symbol = inst['symbol']
        # using ticker
        quote = inst['quote']
        last = inst.get('last_adj') or quote['last']
        #mxq = inst['attrs'].get("MINEXECUTABLEQTY")
        depth.clear_depth(symbol=symbol,last=last,build=True)

        inst = test_instrument.get()
        ## check price not breach priceStep
        price = get_price(side,inst,PriceStyle.LAST)
        agg_price = get_price(o_side,inst,PriceStyle.FARTOUCH)
        #print agg_price
        ## lookup reg data
        now = datetime.utcnow()

        start = now - timedelta(hours=5)
        end = now + timedelta(hours=2)
        param = "startTime=%s,endTime=%s,notifyOrderCompletion=false,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow=20,tradeOpen=0,randomize=0" % \
                (start.strftime("%Y/%m/%d %H:%M:%S GMT"),end.strftime("%Y/%m/%d %H:%M:%S GMT"))
        xref = "FC1"
        order1 = dict(symbol   = symbol,
                     side     = side,
                     price    = price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     serviceOffering = "Programtrading",
                     system = systemName
                     )

        parent1 = Order(**order1)

        # send parent order
        clordId1, er= parent1.new(validate=False)
        parent1.expect("OrderEntry")

        extra = {}
        if serviceOffer:
            extra['serviceOffering'] = serviceOffer


        child1 = dict(parentOrderId=parent1.orderId, xref=xref, price=price, qty=204, sor=None, exch="SYDE",
                      symbol=None, side=side, maq = 5, system = systemName, extra = extra)

        # send child order 1
        child1 = Order(**child1)
        clOrdId1,er1 = child1.new()

        #amend child 1 qty to 300 
        child1.amend(qty=300, maq = 200)

        xref = "FC2"
        #opposing order
        order2 = dict(symbol   = symbol,
                     side     = o_side,
                     price    = agg_price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     serviceOffering = "GSST",
                     system = systemName,
                     )

        parent2 = Order(**order2)

        # send parent order 2
        clordId2, er = parent2.new(validate=False)
        parent2.expect("OrderEntry")

        child2 = dict(parentOrderId=parent2.orderId, xref=xref, price=agg_price, qty=5, sor=None,
                      exch="SYDE", symbol=None, side=o_side,system = systemName, extra = extra)
        child2 = Order(**child2)
        # send child order 2
        clOrdId2,er = child2.new()

        child3 = dict(parentOrderId=parent2.orderId, xref=xref, price=agg_price, qty=10, sor=None,
                      exch="SYDE", symbol=None, side=o_side,system = systemName, extra = extra)
        child3 = Order(**child3)
        # send child order 3
        clOrdId2,er = child3.new()

        child4 = dict(parentOrderId=parent2.orderId, xref=xref, price=agg_price, qty=15, sor=None,
                      exch="SYDE", symbol=None, side=o_side,system = systemName, extra = extra)
        child4 = Order(**child4)
        # send child order 4
        clOrdId2,er = child4.new()

        child5 = dict(parentOrderId=parent2.orderId, xref=xref, price=agg_price, qty=150, sor=None,
                      exch="SYDE", symbol=None, side=o_side,system = systemName, extra = extra)
        child5 = Order(**child5)
        # send child order 5
        clOrdId2,er = child5.new()

        time.sleep(5)

        assert child1.orderStatus.primaryStatus == 'Working'
        assert child2.orderStatus.primaryStatus == 'Working'
        assert child3.orderStatus.primaryStatus == 'Working'
        assert child4.orderStatus.primaryStatus == 'Working'
        assert child5.orderStatus.primaryStatus == 'Working'

        # No trade yet because child 1 has a maq of 200
        child1.amend(maq = 2)


        #Expect the both child orders have a trade 
        ## plutus took long time  up to 60 seconds to ack
        child1.expect("AttachExecution",timeout=80)
        assert child1.orderStatus.primaryStatus == 'Working'
        self._val_fill(child1,last)

        child2.expect("AttachExecution")
        assert child2.orderStatus.primaryStatus == 'Complete'
        self._val_fill(child2,last)

        child3.expect("AttachExecution")
        assert child3.orderStatus.primaryStatus == 'Complete'
        self._val_fill(child3,last)

        child4.expect("AttachExecution")
        assert child4.orderStatus.primaryStatus == 'Complete'
        self._val_fill(child4,last)

        child5.expect("AttachExecution")
        assert child5.orderStatus.primaryStatus == 'Complete'
        self._val_fill(child5,last)

        # try to modify child 1 when order is partially filled

        #amend quantity up // amend qty down is rejected by Om2 for partially filled orders
        child1.amend(qty = 300)

        #amend quantity down
        child1.amend(qty = 250)

        if pegType != 'MarketOrder':
            #amend price
            child1.amend(price = last + tickSize(last,2) )

        #amend min exec qty
        child1.amend(maq = 2 )

        if pegType != 'MarketOrder':
            #amend price and qty
            child1.amend(price= last + tickSize(last, 10), qty = 400)

        if pegType != 'MarketOrder':
            #amend price and maq 
            child1.amend(price= last+ tickSize(last,5), maq = 50)

        if pegType != 'MarketOrder':
            #amend price, qty and maq 
            child1.amend(price= last - tickSize(last,5), maq = 22, qty = 350)

        #cancel child 1
        child1.cancel()
        assert child1.orderStatus.primaryStatus == 'Complete'

    def test_new_ioc_reject(self,side,pegType,serviceOffer,xref,symbol_depth):
        """ ioc child order reject . """

        inst = test_instrument.get()
        symbol = inst['symbol']
        print "symbol: ",symbol
        # using ticker
        quote = inst['quote']
        last = inst.get('last_adj') or quote['last']
        #mxq = inst['attrs'].get("MINEXECUTABLEQTY")
        ## check price not breach priceStep
        price = get_passive_price(side,inst)
        ## lookup reg data
        now = datetime.utcnow()

        start = now - timedelta(hours=5)
        end = now + timedelta(hours=2)
        param = "startTime=%s,endTime=%s,notifyOrderCompletion=false,pegStyle=\"Neutral\",maxShowType=\"porder\",maxShow=20,tradeOpen=0,randomize=0" % \
                (start.strftime("%Y/%m/%d %H:%M:%S GMT"),end.strftime("%Y/%m/%d %H:%M:%S GMT"))
        xref = "FC8"
        parentOrder = dict(symbol = symbol,
                     side     = side,
                     price    = price,
                     qty      = random.randint(1000,2000),
                     xref     = xref,
                     sor      = "PegTest",
                     sorParam = param,
                     atp      = True,
                     exch     = "SYDE",
                     capacity = "Principal",
                     system = systemName,
                     )

        parentOrder['orderType'] = 'Limit'
        parent = Order(**parentOrder)

        clordId, er= parent.new(validate=False)
        parent.expect("OrderEntry")

        extra = {}
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
                     capacity = "Principal",
                     system=systemName,
                     commandRequest = True,
                     crossConsent = "OkToCross",
                     ## ioc order
                     tif="ImmediateOrCancel",
                     allOrNone=random.choice([False,True]),
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
        print child
        #send new child order
        clOrdId,er = child.new(validate=False)
        child.expect("OrderReject")
        assert child.orderStatus.rejectReasonType == "InternalError"
        assert child.orderStatus.rejectReasonText == 'The time in force field does not contain a valid value'
        print child.events()


