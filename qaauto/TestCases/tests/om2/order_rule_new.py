"""test cases for business rules.

1. sizeLimit
2. priceStep OPEN
3. %last in AUCTION
4. priceStep AUCTION i.e. WOW.AX
5. tickSize
6. block security, i.e. AAC.AX liquidity size = 0.01

"""
import time
import random
from pprint import pprint
from datetime import datetime
import math
import pytest
import gevent

from utils import (
              valid_rf_ack,
              tickSize,
              halfTick,
              get_passive_price,
              round_price,
              opposite_side,
              active_wait,
              )
from om2Order import Order
from vikingOrder import VikingOrder
from conf import settings


from TestMarketSymbol import  RandomSymbol
from FindPriceStep import find_rules ,find_sizeLimit

test_inst = RandomSymbol()
sample_size = 1

def get_symbols(state="OPEN"):
    """ helper get auction symbols."""
    test_symbols = None
    if state == "OPEN":
        test_symbols =[o for o in test_inst._gen_open_symbol_with_depth()]
    elif state == "PRE_CSPA":
        test_symbols = [o for o in test_inst._gen_auction_close_symbols()]
    else:
        test_symbols =[o for o in test_inst._gen_auction_open_symbols()]

    random.shuffle(test_symbols)
    return test_symbols


class Test_BusinessRules_OPEN(object):
    """ """
    scenarios = []
    ## expensive to call,return symobl with depth and last exclude blacklist symbols
    open_symbols = [o for o in test_inst._gen_open_symbol_with_depth_and_last() if o[0].symbol not in settings.BLACKLIST_SYMBOLS]
    ## generate random list of symbols with fixed sequence
    random.shuffle(open_symbols, lambda: 0.5)
    ## limit up to 10
    if len(open_symbols) > 10:
        open_symbols = open_symbols[:10]

    for sor in settings.ORDER_TYPES:
        for quote,cha_quote,attrs in open_symbols:
            data = dict(sor=sor,symbol=quote.symbol)
            scenarios.append(data)

    def test_size_limit_open(self,sor,symbol):
        """ test size limit for all orders."""

        side = random.choice(["Buy","Sell","Short"])
        businessUnit = random.choice(["PT","SS","DEFAULT","ALGO_DEFAULT","DMA"])

        ## refresh quote
        quote,cha_quote = test_inst._get_quote(symbol)
        bid = quote.bid[0]
        ask = quote.ask[0]
        last = quote.last

        if bid ==0 or ask == 0:
            pytest.skip("missing bid/ask: %s" % str(quote))

        if quote.state != "OPEN":
            pytest.skip("symbol not in open: %s" % str(quote))

        pprint(quote)
        price = bid or last
        orderType = "limit"
        if sor in ("asx_bid","asx_ask","asx_mid","chia_mid","chia_ask","chia_bid"):
            orderType == "pegged"

        rule = find_rules(quote,price,orderType=orderType,businessUnit=businessUnit)

        sizeLimit = rule['sizeLimit']
        qty_breach = math.ceil((sizeLimit+1)/max(last,price))
        qty_pass = math.floor(sizeLimit/max(last,price))

        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     qty    =qty_breach,
                     xref   =random.choice(settings.CLIENT_XREFS),
                     extra = {'businessUnit': businessUnit},
                     )
        tags = settings.ORDER_TYPES[sor]
        order.update(tags)
        print("====== order =========")
        pprint(order)
        ###########################################
        ## order breach sizeLimit
        print "breach sizeLimit", max(last,price) * qty_breach
        test_order = Order(**order)
        clOrdId,_ = test_order.new(validate=False)

        if sor in settings.SOR_NODIRECT or len(test_order._childs) > 0 :
            test_order.expect('ForceCancel',clOrdId=clOrdId)
        else:
            test_order.expect('OrderReject',clOrdId=clOrdId)
        ## u'SOR: {UtilityAlgo: Unexpected error; SYDE:EqControl: Order[$1,564,656] exceeds [$1,500,000]}
        assert test_order.orderStatus.rejectReasonText != u""

        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)
        assert test_order.orderStatus.primaryStatus == "Complete"
        print test_order.orderStatus

    def test_price_step_open(self,sor,symbol):
        """ """
        if sor in ("chia_mid","chia_bid","chia_ask"):
            pytest.skip("skip chia peg order type: %s" % sor)

        side = random.choice(["Buy","Sell","Short"])
        businessUnit = random.choice(["PT","SS","DEFAULT","ALGO_DEFAULT","DMA"])
        ## refresh quote
        quote,cha_quote = test_inst._get_quote(symbol)
        bid = quote.bid[0]
        ask = quote.ask[0]
        last = quote.last
        ## should never happen
        if bid ==0 and ask == 0 and last == 0 :
            pytest.skip("missing bid/ask/last: %s" % str(quote))
        if quote.state != "OPEN":
            pytest.skip("symbol not in open: %s" % str(quote))

        price = bid or last
        orderType = "limit"
        if sor in ("asx_bid","asx_ask","asx_mid","chia_mid","chia_ask","chia_bid"):
            orderType == "pegged"

        ## chia direct order using asx quote lookup
        rule = find_rules(quote,price,orderType=orderType,businessUnit=businessUnit)
        print("======== quote ========")
        pprint(quote)
        print("======== rule ========")
        pprint(rule)

        max_buy,min_sell = rule['max'], rule['min']
        ## check price not breach priceStep
        if side == 'Buy':
            max_price = max_buy
            delta = +1
        else:
            max_price = min_sell
            delta = -1

        if max_price < 0:
            pytest.skip("max price is in negative")

        ##round price conservatively, max_price will be pass price
        pass_price= round_price(max_price,side=side)
        ## round_price aggressively + 1 tick
        price_breach = round_price(max_price,side=opposite_side(side)) + tickSize(max_price,delta)

        assert delta > 0 and price_breach > max_price or delta < 0 and price_breach < max_price

        order = dict(symbol =symbol,
                     side   =side,
                     price  =price_breach,
                     qty    =random.randint(1,10),
                     xref   =random.choice(settings.CLIENT_XREFS),
                     extra = {'businessUnit': businessUnit},
                     )
        tags = settings.ORDER_TYPES[sor]
        order.update(tags)
        print("====== order =========")
        pprint(order)

        ###########################################
        ## order breach price
        print "breach price", price_breach
        test_order = Order(**order)
        clOrdId,_ = test_order.new(validate=False)
        if sor in settings.SOR_NODIRECT:
            ## order might be traded at price less than breach price for SOR
            try:
                test_order.expect('ForceCancel')
            except ValueError,e:
                ## if sor sweep and traded, make sure execution price is ok
                if 'AttachExecution' in test_order.events():
                    if delta > 0 : # buy order
                        for fill in test_order.fills:
                            assert fill.executionPrice <  order['price']
                    else:
                        for fill in test_order.fills:
                            assert fill.executionPrice > order['price']
                else:
                    raise(e)

        else:
            ## direct order reject by viking.
            test_order.expect('OrderReject',clOrdId=clOrdId)
        ## reject with following error msg
        ## u'SOR: {UtilityAlgo: Unexpected error; SYDE:EqControl: Order[$1,564,656] exceeds [$1,500,000]}
        assert test_order.orderStatus.rejectReasonText != u""

        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)
        assert test_order.orderStatus.primaryStatus == "Complete"
        print test_order.orderStatus

        ###########################################
        ## order not breach price
        print "pass price", pass_price
        order['price'] = pass_price
        test_order = Order(**order)
        try:
            clOrdId,_ = test_order.new()

            if sor in settings.SOR_NODIRECT or len(test_order._childs) > 0:
                try:
                    test_order.expect('ForceCancel',clOrdId=clOrdId,negate=True,wait=0.3)
                except ValueError,e:
                ## if sor sweep and traded, make sure execution price is ok
                    if 'AttachExecution' in test_order.events():
                        if delta > 0 : # buy order
                            for fill in test_order.fills:
                                assert fill.executionPrice <  order['price']
                        else:
                            for fill in test_order.fills:
                                assert fill.executionPrice > order['price']
                    else:
                        raise(e)
        except ValueError,e:
            ## order has passed rule and released to exchange!
            if test_order.orderStatus.rejectingSystem == "Exchange" or \
               test_order.orderStatus.rejectReasons[0]['rejectReasonType'] == "ExchangeReject":
                ##u'SOR: {UtilityAlgo: Unexpected error; SYDE:The premium is outside the allowed price limits for this instrument.}'
                #import re
                #p = re.compile("The premium is outside the allowed price limits for this instrument")
                #if not p.search(test_order.orderStatus.rejectReasonText):
                #    raise(e)
                #print 'workaround issue ANZIN-436, will be removed once fixed'
                ## test stop here, got exchange reject, order passed business rule.
                return
            else:
                raise(e)

        acks =  test_order.events(clOrdId)
        print "orderId,%s, %s" % (test_order.orderId,acks)
        ## order might be traded for aggressive price
        active_wait(lambda: test_order.orderStatus.primaryStatus == "Complete")
        if test_order.orderStatus.primaryStatus != "Complete":
            test_order.cancel()
            test_order.expect("AcceptOrderCancel")
        assert test_order.orderStatus.primaryStatus == "Complete"
        print test_order.orderStatus

class Test_BusinessRules_MKTOrder_OPEN(object):
    """ test direct market order type

    most market order type will be rejected, except asx direct marekt/marketToLimit.

    market will be convert to marketToLimit at Viking.
    """
    scenarios = []
    ## expensive to call,return symobl with depth and last exclude blacklist symbols
    open_symbols = [o for o in test_inst._gen_open_symbol_with_last_without_depth() if o[0].symbol not in settings.BLACKLIST_SYMBOLS]
    ## generate random list of symbols with fixed sequence
    random.shuffle(open_symbols, lambda: 0.5)
    ## limit up to 10
    if len(open_symbols) > 10:
        open_symbols = open_symbols[:10]

    for sor in ('asxmklt','asxmkt'):
        for quote,cha_quote,attrs in open_symbols:
            data = dict(sor=sor,symbol=quote.symbol)
            scenarios.append(data)

    def test_size_limit_open(self,sor,symbol):
        """ test size limit for all orders."""

        side = random.choice(["Buy","Sell","Short"])
        businessUnit = random.choice(["PT","SS","DEFAULT","ALGO_DEFAULT","DMA"])

        ## refresh quote
        quote,cha_quote = test_inst._get_quote(symbol)
        bid = quote.bid[0]
        ask = quote.ask[0]
        last = quote.last

        assert bid == ask == 0

        if quote.state != "OPEN":
            pytest.skip("symbol not in open: %s" % str(quote))

        pprint(quote)
        ##TODO: orderType = "market"
        orderType = "limit"
        rule = find_rules(quote,last,orderType=orderType,businessUnit=businessUnit)

        sizeLimit = rule['sizeLimit']
        qty_breach = math.ceil((sizeLimit+1)/last)
        qty_pass = math.floor(sizeLimit/last)

        try:
            vk_order = VikingOrder(exch="SYDE")
            vk_order.new(symbol=symbol,side=opposite_side(side),price=last,qty=100)
            print vk_order._acks

            order = dict(symbol =symbol,
                         side   =side,
                         price  =0,
                         qty    =qty_breach,
                         xref   =random.choice(settings.CLIENT_XREFS),
                         extra = {'businessUnit': businessUnit},
                         )
            tags = settings.MKT_ORDERS[sor]
            order.update(tags)
            print("====== order =========")
            pprint(order)
            ###########################################
            ## order breach sizeLimit
            print "breach sizeLimit", last * qty_breach
            test_order = Order(**order)
            clOrdId,_ = test_order.new(validate=False)
            test_order.expect('OrderReject',clOrdId=clOrdId)
            ## u'SOR: {UtilityAlgo: Unexpected error; SYDE:EqControl: Order[$1,564,656] exceeds [$1,500,000]}
            assert test_order.orderStatus.rejectReasonText != u""

            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
            assert test_order.orderStatus.primaryStatus == "Complete"
            print test_order.orderStatus
        finally:
            ## clean up 
            vk_order.cancel()
    ### skip this test case as price step rule not implemented.
    @pytest.mark.skipif("True")
    def test_price_step_open(self,sor,symbol):
        """ """
        side = random.choice(["Buy","Sell","Short"])
        businessUnit = random.choice(["PT","SS","DEFAULT","ALGO_DEFAULT","DMA"])
        ## refresh quote
        quote,cha_quote = test_inst._get_quote(symbol)
        bid = quote.bid[0]
        ask = quote.ask[0]
        last = quote.last
        if quote.state != "OPEN":
            pytest.skip("symbol not in open: %s" % str(quote))

        assert bid==ask==0
        orderType = "limit"
        ## chia direct order using asx quote lookup
        rule = find_rules(quote,last,orderType=orderType,businessUnit=businessUnit)
        print("======== quote ========")
        pprint(quote)
        print("======== rule ========")
        pprint(rule)

        max_buy,min_sell = rule['max'], rule['min']
        ## check price not breach priceStep
        if side == 'Buy':
            max_price = max_buy
            delta = +1
        else:
            max_price = min_sell
            delta = -1

        if max_price < 0:
            pytest.skip("max price is in negative")

        ##round price conservatively, max_price will be pass price
        pass_price= round_price(max_price,side=side)
        ## round_price aggressively + 1 tick
        price_breach = round_price(max_price,side=side) + tickSize(max_price,delta)
        ## set to smallest 
        if price_breach == 0: pytest.skip("price breach is 0: %s" % last)

        assert delta > 0 and price_breach > max_price or delta < 0 and price_breach < max_price

        ## setup breach price in viking
        vk_order = VikingOrder(exch="SYDE")
        vk_order.new(symbol=symbol,side=opposite_side(side),price=price_breach,qty=100)
        assert "VikingOrderAccept" in vk_order.acks
        print vk_order._acks

        ## prepare test market order
        order = dict(symbol =symbol,
                     side   =side,
                     price  =0,
                     qty    =random.randint(10,20),
                     xref   =random.choice(settings.CLIENT_XREFS),
                     extra = {'businessUnit': businessUnit},
                     )
        tags = settings.MKT_ORDERS[sor]
        order.update(tags)
        print("====== order =========")
        pprint(order)

        try:
            ###########################################
            ## order breach price
            print "breach price", price_breach
            test_order = Order(**order)
            clOrdId,_ = test_order.new(validate=False)
            ## direct order reject.
            test_order.expect('OrderReject',clOrdId=clOrdId)
            ## reject with following error msg
            ## u'SOR: {UtilityAlgo: Unexpected error; SYDE:EqControl: Order[$1,564,656] exceeds [$1,500,000]}
            assert test_order.orderStatus.rejectReasonText != u""

            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
            assert test_order.orderStatus.primaryStatus == "Complete"
            print test_order.orderStatus

        finally:
            print vk_order.acks
            vk_order.cancel()

class Test_BusinessRules_AUCTION(object):
    """ """
    scenarios = []
    auction_types  = ('PRE_OPEN','PRE_CSPA')
    for sor in settings.ORDER_TYPES:
        ## skip asxc, chia
        if sor in ("asxc","asxcb","chia","chia_bid","chia_ask","chia_mid","asx_mid","asx_bid","asx_ask"): continue
        for auction_type in auction_types:
            data = dict(sor=sor,auctionType=auction_type)
            scenarios.append(data)

    #@pytest.mark.skip
    def test_size_auction(self,sor,auctionType):
        """ """
        side = random.choice(["Buy","Sell","Short"])
        businessUnit = random.choice(["PT","SS","DEFAULT","ALGO_DEFAULT","DMA"])
        auction_symbols = get_symbols(auctionType)
        if len(auction_symbols)==0:
            pytest.skip("no symbol in open auction")

        if len(auction_symbols) >  sample_size:

            test_symbols = auction_symbols[:sample_size]
        else:
            test_symbols = auction_symbols

        for quote,cha_quote,attrs in test_symbols:

            symbol = quote.symbol
            ## refresh quote
            quote,cha_quote = test_inst._get_quote(symbol)
            bid = quote.bid[0]
            ask = quote.ask[0]
            last = quote.last
            close = float(attrs['CLOSEPRICE'])

            ## skip if test if symbol not meed requirerment.
            if auctionType == "PRE_OPEN" and quote.state not in ("PRE_OPEN",):
                pytest.skip("symbol not in PRE_OPEN: %s" % str(quote))
            if auctionType == "PRE_CSPA" and quote.state not in ("PRE_CSPA","PRE_NR"):
                pytest.skip("symbol not in PRE_CSPA: %s" % str(quote))
            if last == 0 and close == 0:
                pytest.skip("missing bid/ask: %s" % str(quote))

            pprint(quote)
            price = last or close
            orderType = "limit"
            if sor in ("asx_bid","asx_ask","asx_mid","chia_mid","chia_ask","chia_bid"):
                orderType == "pegged"

            rule = find_rules(quote,price,orderType=orderType,businessUnit=businessUnit)
            sizeLimit = rule['sizeLimit']
            qty_breach = math.ceil((sizeLimit+1)/max(last,price))
            qty_pass = math.floor(sizeLimit/max(last,price))

            order = dict(symbol =symbol,
                         side   =side,
                         price  =price,
                         qty    =qty_breach,
                         xref   =random.choice(settings.CLIENT_XREFS),
                         extra = {'businessUnit': businessUnit},
                         )
            tags = settings.ORDER_TYPES[sor]
            order.update(tags)
            print("====== order =========")
            pprint(order)
            ###########################################
            ## order breach sizeLimit
            print "breach sizeLimit", max(last,price) * qty_breach
            test_order = Order(**order)
            clOrdId,_ = test_order.new(validate=False)

            ## new way to detect whether is SOR
            #active_wait(lambda: len(test_order._childs) > 0,timeout=1)
            #if test_order._childs > 0:
            #    test_order.expect('ForceCancel',clOrdId=clOrdId)
            #else:
            #    test_order.expect('OrderReject',clOrdId=clOrdId)

            if sor in settings.SOR_NODIRECT or len(test_order._childs) > 0:
                test_order.expect('ForceCancel',clOrdId=clOrdId)
            else:
                test_order.expect('OrderReject',clOrdId=clOrdId)

            # u'SOR: {UtilityAlgo: Unexpected error; SYDE:EqControl: Order[$1,564,656] exceeds [$1,500,000]}
            assert test_order.orderStatus.rejectReasonText != u""

            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
            assert test_order.orderStatus.primaryStatus == "Complete"
            print test_order.orderStatus

    def test_price_step_auction(self,sor,auctionType):
        """ """
        side = random.choice(["Buy","Sell","Short"])
        businessUnit = random.choice(["PT","SS","DEFAULT","ALGO_DEFAULT","DMA"])
        auction_symbols = get_symbols(auctionType)

        if len(auction_symbols)==0:
            pytest.skip("no symbol in auction :%s" % auctionType)

        if len(auction_symbols) > sample_size:
            test_symbols = auction_symbols[:sample_size]
        else:
            test_symbols = auction_symbols

        for quote, cha_quote, attrs in test_symbols:

            symbol = quote.symbol
            ## refresh quote
            quote,cha_quote = test_inst._get_quote(symbol)
            bid = quote.bid[0]
            ask = quote.ask[0]
            last = quote.last
            ## market close or darpan close
            close = quote.close or float(attrs['CLOSEPRICE'])
            match = quote.match

            if last ==0 and close == 0:
                pytest.skip("missing last and close: %s, %s" % (str(quote),attrs))
            ## 
            if last == 0: last = close
            ## price = last = close
            price = last
            orderType = "limit"

            rule = find_rules(quote,price,orderType=orderType,businessUnit=businessUnit)

            max_buy, min_sell = rule['max'], rule['min']
            ## check price not breach priceStep
            if side == 'Buy':
                max_price = max_buy
                delta = +2
            else:
                max_price = min_sell
                delta = -2
            print("======== quote ========")
            pprint(quote)
            print("======== rule ========")
            pprint(rule)


            if max_price < 0:
                pytest.skip("max price is in negative")

            max_price = round_price(max_price,side=side)
            price_breach = max_price + tickSize(max_price,delta)

            order = dict(symbol =symbol,
                         side   =side,
                         price  =price_breach,
                         qty    =random.randint(200,300),
                         xref   =random.choice(settings.CLIENT_XREFS),
                         extra = {'businessUnit': businessUnit} ,
                         )
            tags = settings.ORDER_TYPES[sor]
            order.update(tags)
            print("====== order =========")
            pprint(order)

            ###########################################
            ## order breach sizeLimit
            print "breach price", price_breach
            test_order = Order(**order)
            clOrdId,_ = test_order.new(validate=False)

            if sor in settings.SOR_NODIRECT:
                test_order.expect('ForceCancel',clOrdId=clOrdId)
            else:
                test_order.expect('OrderReject',clOrdId=clOrdId)
            ## u'SOR: {UtilityAlgo: Unexpected error; SYDE:EqControl: Order[$1,564,656] exceeds [$1,500,000]}
            assert test_order.orderStatus.rejectReasonText != u""
            assert test_order.orderStatus.rejectReasonType == 'LimitPriceTooAggressive'

            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
            assert test_order.orderStatus.primaryStatus == "Complete"
            print test_order.orderStatus

            ###########################################
            ## order not breach limit
            price_pass = max_price - tickSize(max_price,delta)

            print "pass price", price_pass
            order['price'] = price_pass
            test_order = Order(**order)
            clOrdId,_ = test_order.new()
            if sor in settings.SOR_NODIRECT:
                test_order.expect('ForceCancel',clOrdId=clOrdId,negate=True,wait=0.3)

            ## chia and asxc shall be rejected by exchange.
            if sor != ('chia','chia_bid','chia_ask','asxc','asx_mid'):
                acks =  test_order.events(clOrdId)
                print "orderId,%s, %s" % (test_order.orderId,acks)
                ## order might be traded for aggressive price
                gevent.sleep(1)
                if test_order.orderStatus.primaryStatus != "Complete":
                    test_order.cancel()
                    test_order.expect("AcceptOrderCancel")
            assert test_order.orderStatus.primaryStatus == "Complete"
            print test_order.orderStatus

