""" test cases for SOR.

"""
import random
from pprint import pprint
import pytest
from utils import (
                  valid_rf_ack,
                  tickSize,
                  halfTick,
                  get_passive_price,
                  opposite_side,
                  AckFailed,
                  active_wait,
                  )
from om2Order import Order ,AckFailed
from conf import settings
import gevent
## facil test order
from vikingOrder import VikingOrder

from utils import DepthStyle

class Test_SOR_MXQ:

    """ test sor order with/without mxq.

    - default/explicit mxq
    - sor1/sor4/sor5 should not trade on CHIA
    - other sor should trade on CHIA
    - sor7 trade on CHIA during second phase sweep (bug)

    """

    scenarios = []

    for sor in settings.SOR_NODIRECT_DARK:
        if 'sor4' ==  sor:
        #if 'maq' not in sor:
            for side in settings.TEST_SIDES:
                data = dict(sor=sor,side=side)

                scenarios.append(data)

    def test_new_order_mxq_default(self,side,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,with_mxq=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        assert "MINEXECUTABLEQTY" in attrs
        mxq = int(attrs["MINEXECUTABLEQTY"])
        ## market depth
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        order_t = dict(symbol =symbol,
                        side   =side,
                        price  =last,
                        #qty    =random.randint(1000,2000), #+ mxq,
                        qty = mxq,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )
        ## setup CHIA facil order with qty < minQty
        cha_order = order_t.copy()
        cha_order['side'] = opposite_side(side)
        ## test orde with mxq or 10 -1
        #cha_order['qty'] = (mxq or 10) -1
        cha_order['qty'] = 1#order_t['qty'] -1

        cha_order.update(settings.ORDER_TYPES['chia'])

        test_chaOrder = Order(**cha_order)
        test_chaOrder.new()
        print (" ========== chia order =============")
        print(test_chaOrder)
        test_chaOrder.expect_ok()

        order = order_t.copy()
        order['xref'] = random.choice(settings.HOUSE_XREFS)
        order.update(settings.ORDER_TYPES[sor])

        print ("========== sor order ============")
        ## test sor order
        test_sorOrder = Order(**order)
        ##
        test_sorOrder.new()
        print(test_sorOrder)

        #pytest.set_trace()
        try:
            if sor in( 'sor1','sor6') or (sor in ('sor4','sor5','sor7') and mxq > 0):
                test_sorOrder.expect("AttachExecution",negate=True,wait=1)
                test_chaOrder.expect("AttacheExecution",negate=True,wait=1)
            else:
                test_sorOrder.expect("AttachExecution")
                test_chaOrder.expect("AttachExecution")

            test_sorOrder.cancel(validate=False)
            print test_sorOrder.orderStatus
            print test_sorOrder.fills
            test_sorOrder.orderStatus.primaryStatus == "Complete"
        finally:
            #
            # cleanup test order
            if test_chaOrder.orderStatus.primaryStatus != "Complete":
                test_chaOrder.cancel(validate=False)


    def test_new_order_mxq_explicit_notrade(self,side,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        order_t = dict(symbol =symbol,
                        side   =side,
                        price  =last,
                        qty    = random.randint(1000,2000)+ mxq,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )
        ## setup CHIA facil order with qty < minQty
        cha_order = order_t.copy()
        cha_order['side'] = opposite_side(side)
        ## test orde with mxq or 10 -1
        cha_order['qty'] = (mxq or 10) -1
        cha_order.update(settings.ORDER_TYPES['chia'])

        test_chaOrder = Order(**cha_order)
        test_chaOrder.new()
        print (" ========== chia order =============")
        print(test_chaOrder)
        test_chaOrder.expect_ok()

        order = order_t.copy()
        order['xref'] = random.choice(settings.HOUSE_XREFS)
        order.update(settings.ORDER_TYPES[sor])

        print ("========== sor order ============")
        ## explicit set maq for MinQty SOR
        if sor in ('sor4','sor5','sor7') and mxq > 0:
            order['maq'] = mxq

        ## test sor order
        test_sorOrder = Order(**order)
        ##
        test_sorOrder.new()
        print(test_sorOrder)

        try:
            if sor in( 'sor1','sor6') or (sor in ('sor4','sor5','sor7') and mxq > 0):
                test_chaOrder.expect("AttacheExecution",negate=True,wait=1)
                test_sorOrder.expect("AttachExecution",negate=True,wait=1)
            else:
                test_sorOrder.expect("AttachExecution")
                test_chaOrder.expect("AttachExecution")

            test_sorOrder.cancel()
            print test_sorOrder.orderStatus
            print test_sorOrder.fills
            test_sorOrder.orderStatus.primaryStatus == "Complete"
        finally:
            #
            # cleanup test order
            if test_chaOrder.orderStatus.primaryStatus != "Complete":
                test_chaOrder.cancel()


class Test_SOR_BestPrice_New:

    """ test sor BestPrice new order.

    - build depth in ASX/CHIA for NBBO
    - BestPrice new order hit CHIA, test CHIA Lit/Dark

    """

    scenarios = []

    depthStyles = (
              DepthStyle.ASXCHIA,
              DepthStyle.ASXONLY,
            )

    ## test order resting on CHIA i.e. lit/dark/ASXCP
    ## chia_bid/buy, chia_ask/sell will not aggressive enough for being traded.
    testStyles = ('asxc',
                  'chia',
                  'chia_mid',
                  )

    for sor in settings.SOR_NODIRECT_DARK:
        for style in depthStyles:
            for testStyle in testStyles:
                data = dict(sor=sor,style=style,testStyle=testStyle)

                scenarios.append(data)

    def test_new_order_sor(self,sor,style,testStyle,symbol_depth):
        """ sor order best price lit sweep."""
        if testStyle == 'asxc':
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,style=style)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        side = random.choice(settings.TEST_SIDES)
        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))
        side_pass = opposite_side(side)

        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_pass = last - tickSize(last,1)
        else:
            price_aggr = last - tickSize(last,1)
            price_pass = last + tickSize(last,1)

        ## order template
        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_pass
        t_chia.update(settings.ORDER_TYPES[testStyle])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA/ASXC order =========")
        print order_cxa

        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_aggr
        t_sor['qty'] = 2 * t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        order_sor.new()
        print ("======== sor order ============")
        print order_sor

        try:
            ## asxonly not traded for CHIA
            if sor == 'sor1' and testStyle != 'asxc':
                order_cxa.expect("AttachExecution",negate=True)
                order_sor.expect("AttachExecution",negate=True)
                order_cxa.cancel()
                order_sor.cancel()
            ## BestPriceMinQtyNoLit not traded for CHIA ,BPMQNotLitUni not trade on CHIA for new order
            elif sor in ('sor6','sor6_maq','sor7','sor7_maq') and testStyle == 'chia' :
                order_cxa.expect("AttachExecution",negate=True)
                order_sor.expect("AttachExecution",negate=True)
                order_cxa.cancel()
                order_sor.cancel()
            ## everything else should sweep/traded on CHIA dark and ASXCP
            else:
                order_sor.expect("AttachExecution")
                order_cxa.expect("AttachExecution")
                pprint(order_sor.fills)
        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)

class AmendStyle:

    """ amend style. """

    PRICEONLY = 0
    QTYONLY   = 1
    PRICEQTY  = 2

class Test_SOR_BestPrice_Amend:

    """ test sor order BestPrice.

    - build depth in ASX/CHIA for NBBO
    - BestPrice new order hit CHIA, test CHIA Lit/Dark
    - Note: issue 445, amend aggressive for order already cross spread, it will not re-sweep ASXC.

    """

    scenarios = []

    styles = (
              DepthStyle.ASXCHIA,
              DepthStyle.ASXONLY,
            )

    ## test order i.e. CHIA lit/dark/ASXCP
    ## chia_bid/buy, chia_ask/sell will not aggressive enough for being traded.
    testStyles = ('asxc',
                  'chia',
                  'chia_mid',
                  )

    amendStyles = (AmendStyle.PRICEONLY,
                   AmendStyle.PRICEQTY,
                   )

    for sor in settings.SOR_NODIRECT_DARK:
        #if sor not in ('sor4','sor4_maq','sor6','sor6_maq','sor7','sor7_maq'): continue
        for side in settings.TEST_SIDES:
            for style in styles:
                for testStyle in testStyles:
                    for amendStyle in amendStyles:
                        data = dict(sor=sor,side=side,style=style,testStyle=testStyle,amendStyle=amendStyle)

                    scenarios.append(data)

    #@pytest.mark.skipif("True")
    def test_amend_order_aggry(self,side,sor,style,testStyle,amendStyle,symbol_depth):
        """ sor order best price lit sweep."""
        if testStyle == 'asxc':
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs  = symbol_depth.get_tradable_symbol(build=True,style=style)
            #depth.clear_depth(symbol=symbol,last=last,build=True,style=style)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))
        side_pass = opposite_side(side)

        print  " === asx depth === "
        pprint(quote)
        print " === cxa depth === "
        pprint(cha_quote)

        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_pass = last - tickSize(last,1)
            price_pass_2 = last - tickSize(last,2)
        else:
            price_aggr = last - tickSize(last,1)
            price_pass = last + tickSize(last,1)
            price_pass_2 = last + tickSize(last,2)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_pass
        t_chia.update(settings.ORDER_TYPES[testStyle])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA/ASXC order =========")
        print order_cxa
        gevent.sleep(1)
        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_pass_2
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        order_sor.new()
        ## no trade
        order_sor.expect("AttachExecution",negate=True)
        ## amend aggr
        gevent.sleep(1) ## workaround OM2 issue 445
        if amendStyle ==  AmendStyle.PRICEQTY:
            order_sor.amend(price=price_aggr,qty=2 * t_sor['qty'])
        else:
            order_sor.amend(price=price_aggr)

        print ("======== sor order(amend) ============")
        print order_sor

        try:
            ## asxonly not traded for CHIA
            if sor == 'sor1' and testStyle != 'asxc':
                order_cxa.expect("AttachExecution",negate=True)
                order_sor.expect("AttachExecution",negate=True)
                order_cxa.cancel()
                order_sor.cancel()
            ## BestPriceMinqtyNoLit not traded for CHIA, BPMQNoLitUni not traded for CHIA 
            elif sor in ('sor6','sor6_maq','sor7','sor7_maq') and testStyle == 'chia' :
                order_cxa.expect("AttachExecution",negate=True)
                order_sor.expect("AttachExecution",negate=True)
                order_cxa.cancel()
                order_sor.cancel()
            ## everything else should sweep/traded on CHIA dark and ASXCP
            else:
                order_sor.expect("AttachExecution")
                order_cxa.expect("AttachExecution")
                pprint(order_sor.fills)
        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)


class Test_SOR_Unireflect:

    """ test sor order unireflect hit CHIA.

    - build depth in ASX/CHIA for NBBO
    - unireflect new order hit CHIA
    -

    """

    scenarios = []

    styles = (
              DepthStyle.ASXCHIA,
              DepthStyle.CHIAASX,
              DepthStyle.ASXONLY,
              )

    for sor in settings.SOR_NODIRECT_DARK:
        if sor.endswith("maq_0"): continue
        for side in settings.TEST_SIDES:
            for style in styles:
                data = dict(sor=sor,side=side,style=style)

                scenarios.append(data)

    def test_new_order(self,side,sor,style,symbol_depth):
        """ sor-un order after resting hit CHIA ."""
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,style=style)
        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))
        # using ticker
        bid,ask,last = quote['bid'],quote['ask'],quote['last']

        side_pass = opposite_side(side)

        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_pass = last - tickSize(last,1)
        else:
            price_aggr = last - tickSize(last,1)
            price_pass = last + tickSize(last,1)


        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )

        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_aggr
        t_sor['qty'] = 2 * t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        order_sor.new()
        print ("======== resting sor order ============")
        print order_sor

        ##
        gevent.sleep(2)
        ### facil order CHIA
        vkOrder = VikingOrder(exch="CHIA")
        assert vkOrder.new(symbol=symbol,side=side_pass,price=price_pass,qty=order_t['qty'])
        print ("======== CHIA order =========")
        print vkOrder,vkOrder.acks

        try:
            ## asxonly not traded for CHIA
            if sor in ('sor1','sor2','sor4','sor4_maq','sor6','sor6_maq'):
                assert vkOrder.filledQty == 0
                order_sor.expect("AttachExecution",negate=True)
                assert vkOrder.cancel()
                order_sor.cancel()
            ## everything else should sweep/traded on CHIA dark and ASXCP
            else:
                order_sor.expect("AttachExecution")
                active_wait(lambda: vkOrder.filledQty > 0)
                assert vkOrder.filledQty == vkOrder._data['quantity'], vkOrder.acks
                pprint(order_sor.fills)
        finally:

            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel()
            ## clean up
            if 'VikingAcceptCancelRequest' not in vkOrder.acks and vkOrder.filledQty != vkOrder._data['quantity']:
                assert vkOrder.cancel()

class Test_SOR_SI_ASXOnly:

    """ test sor order for client SI ASXONLY.

    - test order behave as if ASXONLY being applied.
    - i.e. no CHIA sweep.

    """

    scenarios = []

    for sor in settings.SOR_NODIRECT_DARK:
        for side in settings.TEST_SIDES:
            data = dict(sor=sor,side=side)

            scenarios.append(data)

    def test_new_order_si(self,side,sor,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))
        bid,ask,last = quote['bid'],quote['ask'],quote['last']

        order_t = dict(symbol  = symbol,
                        side   = side,
                        price  = last,
                        qty    = mxq + random.randint(1000,2000),
                        xref   = random.choice(settings.HOUSE_XREFS),
                        )
        ## setup CHIA facil order with qty < minQty
        cha_order = order_t.copy()
        cha_order['side'] = opposite_side(side)
        ## test orde with mxq or 10 -1
        cha_order['qty'] = 1
        cha_order.update(settings.ORDER_TYPES['chia'])

        test_chaOrder = Order(**cha_order)
        test_chaOrder.new()
        print (" ========== chia order =============")
        print(test_chaOrder)
        test_chaOrder.expect_ok()

        order = order_t.copy()
        order['xref'] = random.choice(settings.CLIENT_SI_XREFS)
        order.update(settings.ORDER_TYPES[sor])

        print ("========== sor order ============")
        ## test sor order
        test_sorOrder = Order(**order)
        ##
        test_sorOrder.new()
        print(test_sorOrder)

        try:
            test_sorOrder.expect("AttachExecution",negate=True,wait=1)
            test_chaOrder.expect("AttacheExecution",negate=True,wait=1)

            test_sorOrder.cancel()
            print test_sorOrder.orderStatus
            print test_sorOrder.fills
            assert test_sorOrder.orderStatus.primaryStatus == "Complete"
        finally:
            #
            # cleanup test order
            if test_chaOrder.orderStatus.primaryStatus != "Complete":
                test_chaOrder.cancel()


class Test_SOR_Amend_FilledOrder:

    """ test sor order amend filled order will be rejected. """

    scenarios = []

    ## test order i.e. CHIA lit/dark/ASXCP
    testStyles = ('chia',)

    for sor in ('sor4','sor4_maq'):
        #if sor in ('sor2',):
        for side in settings.TEST_SIDES:
            for testStyle in testStyles:
                data = dict(sor=sor,side=side,testStyle=testStyle)

                scenarios.append(data)

    def test_new_order_sor(self,side,sor,testStyle,symbol_depth):
        """ sor order best price lit sweep."""
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))
        bid,ask,last = quote['bid'],quote['ask'],quote['last']

        side_pass = opposite_side(side)

        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_pass = last - tickSize(last,1)
        else:
            price_aggr = last - tickSize(last,1)
            price_pass = last + tickSize(last,1)

        ## setup depth, 2 tickSize
        if testStyle == 'asxc':
            depth.clear_depth(symbol=symbol,last=last,build=True)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_pass
        t_chia.update(settings.ORDER_TYPES[testStyle])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA/ASXC order =========")
        print order_cxa

        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_aggr
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        order_sor.new()
        print ("======== sor order ============")
        print order_sor

        try:
            order_sor.expect("AttachExecution")
            order_cxa.expect("AttachExecution")
            pprint(order_sor.fills)
            ## amend filled sor order qty up
            try:

                order_sor.amend(qty=order_t['qty'] + 200)
                assert False, "order should be rejected by OM2 for amend filled sor order %s!" % order_sor
            except AckFailed,ex:
                e = ex.message
                #     AckFailed: {u'orderId': u'QAEAUCEA520150601O', u'rejectReasons': [{u'rejectReasonText': u'Validation failed: Order already completed', u'rejectingSystem': 2, u'rejectReasonType': 17}], u'eventIdWrapper': [{u'eventNumber': 26, u'eventSystemName': u'QAEAUCEA', u'eventId': u'QAEAUCEA2620150601V', u'eventDate': u'20150601'}], u'wasCommandSuccessful': False, u'posDupId': u'FC1/rO'}
                assert 'rejectReasons' in e and 'rejectReasonText' in e['rejectReasons'][0], e
                assert e['rejectReasons'][0]['rejectReasonText'] == u'Validation failed: Order already completed', e
            except ValueError,ex:
                order_sor.expect("RequestOrderCorrectFailure")
                events = order_sor.hist()[-1].eventData.events
                assert events[0]['rejectReasons'][0]['rejectReasonText'] == 'Validation failed: Order already completed', events

            print order_sor.orderStatus

        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel()
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel()


class Test_SOR_AmendUp_for_ImmediateFill:

    """ test sor order amend filled order will be rejected.

    only validate successful fill, then amend. skip any reject.

    """

    scenarios = []

    ## test order i.e. asx lit
    testStyles = ('asx',)

    for sor in settings.SOR_NODIRECT_DARK: #('sor4','sor4_maq')
        #if sor in ('sor2',):
        for side in settings.TEST_SIDES:
            for testStyle in testStyles:
                data = dict(sor=sor,side=side,testStyle=testStyle)

                scenarios.append(data)

    def test_new_order_sor(self,side,sor,testStyle,symbol_depth):
        """ sor order best price lit sweep."""

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        ## default symbol  mxq
        mxq = int(attrs.get('MINEXECUTABLEQTY',0))
        bid,ask,last = quote['bid'],quote['ask'],quote['last']

        side_pass = opposite_side(side)

        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_pass = last - tickSize(last,1)
        else:
            price_aggr = last - tickSize(last,1)
            price_pass = last + tickSize(last,1)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )

        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_aggr
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        order_sor.new()
        print ("======== sor order ============")
        print order_sor

        ## facil order should hit SOR order
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_pass
        t_chia.update(settings.ORDER_TYPES[testStyle])

        order_cxa = Order(**t_chia)
        order_cxa.new(validate=False)
        print ("======== ASX order =========")
        print order_cxa

        try:
            qty = random.randint(10,200)
            ### amend sor order for both price/qty
            try:
                order_sor.amend(qty=t_sor['qty'] + qty,price=price_pass)
                active_wait(lambda : len(order_sor.fills) > 0)
                if len(order_sor.fills) == 0:
                    pytest.skip("too faster to amend")

            except AckFailed,e:
                print e
                pytest.skip("too slow to amend")
            except ValueError,ex:
                order_sor.expect("RequestOrderCorrectFailure")
                events = order_sor.hist()[-1].eventData.events
                assert events[0]['rejectReasons'][0]['rejectReasonText'] == 'Validation failed: Order already completed', events

            order_sor.expect("AttachExecution")
            order_cxa.expect("AttachExecution")
            pprint(order_sor.fills)
            pprint(order_sor.orderStatus)
            assert order_sor.orderStatus.quantityRemaining == order_sor.orderStatus.childQuantityOpen == qty
            assert order_sor.orderStatus.splitQuantityRemaining == qty
            #assert order_sor.orderStatus.splitQuantity in ( qty, qty + t_sor['qty'])
            assert order_sor.orderStatus.splitQuantityExecuted == t_sor['qty']

        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)


class Test_ASXSweep:
    """ test asx sweep i.e. ASXS order type.

    0) build depth with bid/ask in 1 tick size. note: bid = last, ask = last + one tick
    1) asxweep order at mid tick, and new order hit ASXC at mid
    2) remaining qty/asxweep resting on bid or ask as limit order
    3) other side aggrssive order should be test order at bid or ask. note: this is a better price than mid
    """

    scenarios = []

    sor_types = ('asxsweep','asxs')
    for side in settings.TEST_SIDES:
        for sor in sor_types:
            data = dict(side=side,sor=sor)
            scenarios.append(data)

    def test_asxweep_new_order_aggressive(self,side,sor,symbol_depth):
        """
        1) new order aggressive at mid price, expect hit ASXC at mid
        2) other side aggressive order should hit test order at bid or ask.
           note: this should be a better price than mid.
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,tick=0.5)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        side_pass = opposite_side(side)

        order_t = {
                'symbol' : symbol,
                'price' : last + halfTick(last),
                'qty' : random.randint(100,300),
                'side': side_pass,
                'xref': 'FC1',
        }
        asxc_order_t = order_t.copy()
        asxc_order_t.update(settings.ORDER_TYPES['asxc'])

        ## submit asxc order
        asxc_order = Order(**asxc_order_t)
        asxc_order.new()
        asxc_order.expect_ok()
        ## prepare test order
        order_t.update(settings.ORDER_TYPES[sor])
        order_t['side'] = side
        order_t['xref'] = 'FC5'
        order_t['qty'] = order_t['qty'] + 300
        test_order = Order(**order_t)

        test_order.new()
        test_order.expect_ok()
        gevent.sleep(2)

        assert test_order.fills
        assert len(test_order.fills) >= 1
        #pytest.set_trace()
        assert asxc_order.fills

        asxc_exec = test_order.fills[0].executionData
        assert asxc_exec['executionLastMarket'] == 'ASXC'
        assert asxc_exec['executionPrice'] - (last + halfTick(last)) < 0.00001

        ## other side aggressive order hit asxsweep order at bid/ask i.e. better than mid
        aggr_order_t = order_t.copy()
        aggr_order_t.update(settings.ORDER_TYPES['asx'])
        aggr_order_t['xref'] = 'FC2'
        aggr_order_t['qty'] = 900 + order_t['qty']
        if side == "Buy":
            #test_order.amend(price=last +  tickSize(last,1))
            aggr_order_t['side'] = "Sell"
            aggr_order_t['price'] = last
        else:
            #test_order.amend(price=last)
            aggr_order_t["side"] = "Buy"
            aggr_order_t['price'] = last + tickSize(last,1)

        aggr_order = Order(**aggr_order_t)
        aggr_order.new()
        aggr_order.expect_ok()

        gevent.sleep(1)
        assert aggr_order.fills
        assert len(test_order.fills) > 1

        ## validate fill on ASXT
        asxt_exec = test_order.fills[-1].executionData
        assert asxt_exec['executionLastMarket'] == 'ASXT'
        if side == "Buy":
            assert asxt_exec['executionPrice'] - last  < 0.00001
            ## asxt price should better than asxc
            assert asxc_exec['executionPrice'] > asxt_exec['executionPrice']
        else:
            assert asxt_exec['executionPrice'] - (last + tickSize(last,1)) < 0.00001
            ## asxt price should better than asxc
            assert asxc_exec['executionPrice'] < asxt_exec['executionPrice']

        aggr_order.cancel(validate=False)
        asxc_order.cancel(validate=False)

    @pytest.mark.skipif("True")
    def test_asxweep_amend_order_aggressive_halfTick(self,side,sor,symbol_depth):
        """
        1) new order passive at bid/ask
        2) amend order aggressive halfTick, hit ASXC
        3) other side aggressive order, hit test order at bid or ask.
        note: price 3) should be a better price that price 2)

        half tick amend will not supported by Viking, must be full tick.
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,tick=0.5)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        side_pass = opposite_side(side)

        passive_price = last if side == 'Buy' else last + tickSize(last,1)

        order_t = {
                'symbol' : symbol,
                'price' : last + halfTick(last),
                'qty' : random.randint(100,300),
                'side': side_pass,
                'xref': 'FC1',
        }
        asxc_order_t = order_t.copy()
        asxc_order_t.update(settings.ORDER_TYPES['asxc'])

        ## submit asxc order
        asxc_order = Order(**asxc_order_t)
        asxc_order.new()
        asxc_order.expect_ok()
        ## prepare passive test order
        order_t.update(settings.ORDER_TYPES[sor])
        order_t['side'] = side
        order_t['xref'] = 'FC5'
        order_t['price'] = passive_price
        order_t['qty'] = order_t['qty'] + 300
        test_order = Order(**order_t)
        test_order.new()
        test_order.expect_ok()

        ## order no fill
        gevent.sleep(2)
        assert len(test_order.fills) == 0

        test_order.amend(price=last + halfTick(last))
        ## active wait for execution.
        assert active_wait(lambda: len(test_order.fills) >=1 )
        assert test_order.fills
        assert len(test_order.fills) >= 1

        assert asxc_order.fills
        assert len(asxc_order.fills) == 1

        asxc_exec = test_order.fills[0].executionData
        assert asxc_exec['executionLastMarket'] == 'ASXC'
        assert asxc_exec['executionPrice'] - (last + halfTick(last)) < 0.00001

        ## other side aggressive order hit asxsweep order at bid/ask i.e. better than mid
        aggr_order_t = order_t.copy()
        aggr_order_t.update(settings.ORDER_TYPES['asx'])
        aggr_order_t['xref'] = 'FC2'
        aggr_order_t['qty'] = 900 + order_t['qty']
        if side == "Buy":
            #test_order.amend(price=last +  tickSize(last,1))
            aggr_order_t['side'] = "Sell"
            aggr_order_t['price'] = last
        else:
            #test_order.amend(price=last)
            aggr_order_t["side"] = "Buy"
            aggr_order_t['price'] = last + tickSize(last,1)

        aggr_order = Order(**aggr_order_t)
        aggr_order.new()
        aggr_order.expect_ok()

        active_wait(lambda: len(test_order.fills) > 1)
        assert aggr_order.fills
        assert len(test_order.fills) > 1

        ## validate fill on ASXT
        asxt_exec = test_order.fills[1].executionData
        assert asxt_exec['executionLastMarket'] == 'ASXT'
        if side == "Buy":
            assert asxt_exec['executionPrice'] - last  < 0.00001
            ## asxt price should better than asxc
            assert asxc_exec['executionPrice'] < asxt_exec['executionPrice']
        else:
            assert asxt_exec['executionPrice'] - (last + tickSize(last,1)) < 0.00001
            ## asxt price should better than asxc
            assert asxc_exec['executionPrice'] > asxt_exec['executionPrice']
        ## clean up
        aggr_order.cancel(validate=False)
        asxc_order.cancel(validate=False)

    def test_asxweep_amend_order_aggressive_oneTick(self,side,sor,symbol_depth):
        """ 
        1) new order passive at bid/ask
        2) amend order aggressive one tick, hit ASXC
        3) other side aggressive order, hit test order at bid or ask.
        note: price 3) should equal  price 2)

        amend in one tick.
        """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,tick=1)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

        side_pass = opposite_side(side)

        aggr_price = - tickSize(last,1) if side == 'Buy' else tickSize(last,1)
        order_t = {
                'symbol' : symbol,
                'price' : last,
                'qty' : random.randint(100,300),
                'side': side_pass,
                'xref': 'FC1',
        }
        asxc_order_t = order_t.copy()
        asxc_order_t.update(settings.ORDER_TYPES['asxc'])

        ## submit asxc order
        asxc_order = Order(**asxc_order_t)
        asxc_order.new()
        asxc_order.expect_ok()
        ## prepare passive test order
        order_t.update(settings.ORDER_TYPES[sor])
        order_t['side'] = side
        order_t['xref'] = 'FC5'
        order_t['price'] = last + aggr_price
        order_t['qty'] = order_t['qty'] + 300
        test_order = Order(**order_t)
        test_order.new()
        test_order.expect_ok()
        gevent.sleep(2)
        assert len(test_order.fills) == 0

        test_order.amend(price=last)
        ##  expect fill
        active_wait(lambda: len(test_order.fills) > 1)
        assert test_order.fills
        assert len(test_order.fills) >= 1

        assert asxc_order.fills
        assert len(asxc_order.fills) == 1

        asxc_exec = test_order.fills[0].executionData
        assert asxc_exec['executionLastMarket'] == 'ASXC'
        assert asxc_exec['executionPrice'] - (last + halfTick(last)) < 0.00001

        ## other side aggressive order hit asxsweep order at bid/ask i.e. better than mid
        aggr_order_t = order_t.copy()
        aggr_order_t.update(settings.ORDER_TYPES['asx'])
        aggr_order_t['xref'] = 'FC2'
        aggr_order_t['qty'] = 900 + order_t['qty']
        aggr_order_t['price'] = last  + aggr_price

        if side == "Buy":
            #test_order.amend(price=last +  tickSize(last,1))
            aggr_order_t['side'] = "Sell"
        else:
            #test_order.amend(price=last)
            aggr_order_t["side"] = "Buy"

        aggr_order = Order(**aggr_order_t)
        aggr_order.new()
        aggr_order.expect_ok()

        active_wait(lambda: len(aggr_order.fills) > 0)
        assert aggr_order.fills
        assert len(test_order.fills) > 1

        ## validate fill on ASXT
        asxt_exec = test_order.fills[1].executionData
        assert asxt_exec['executionLastMarket'] == 'ASXT'
        if side == "Buy":
            assert asxt_exec['executionPrice'] - last  < 0.00001
            ## asxt price should better than asxc
            assert asxc_exec['executionPrice'] == asxt_exec['executionPrice']
        else:
            assert asxt_exec['executionPrice'] - (last + tickSize(last,1)) < 0.00001
            ## asxt price should better than asxc
            assert asxc_exec['executionPrice'] == asxt_exec['executionPrice']

        ## clean up
        asxc_order.cancel(validate=False)
        aggr_order.cancel(validate=False)


class Test_SOR_ASXPreference:
    """
    IS:6010-1595671,Yoffe, Igal,SOR AU: Chi-X re-preferencing

    if ASX,CHIA got same price, ASX will be preferred.
    old way is always sweep CHIA first.



    1) new order depth with asx,chia at same price point, hit asx
    2) amend order agr, depth asx,chia at same price point, hit asx.
    3) new order depth with chia at better price point, hit chia.
    4) amend order depth with chia at better price point, hit chia.

    """
    scenarios = []

    styles = (
              DepthStyle.ASXCHIA,
              DepthStyle.ASXONLY,
            )

    amendStyles = (AmendStyle.PRICEONLY,
                   AmendStyle.PRICEQTY,
                   )

    for sor in settings.SOR_NODIRECT_DARK:
        ## skip asxonly 
        if sor in ('sor1','xasx'): continue
        for side in settings.TEST_SIDES:
            for style in styles:
                data = dict(sor=sor,side=side,style=style)
                scenarios.append(data)

    #@pytest.mark.skipif("True")
    def test_new_order_aggr(self,side,sor,style,symbol_depth):
        """ sor order best price lit sweep."""
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,style=style)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

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

        #depth.clear_depth(symbol=symbol,last=last,build=True,style=style)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_aggr
        t_chia.update(settings.ORDER_TYPES["chia"])
        ## facil order ASX direct with same price at CHIA
        t_asx = order_t.copy()
        t_asx['side'] = side_pass
        t_asx['price'] = price_aggr
        t_asx.update(settings.ORDER_TYPES["asx"])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA order =========")
        print order_cxa

        order_asx = Order(**t_asx)
        order_asx.new()
        print ("======== ASX order =========")
        print order_asx

        gevent.sleep(1)
        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_aggr
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        try:
            order_sor.new()
            ## no trade
            order_sor.expect("AttachExecution")
            print order_sor.fills
            order_cxa.expect("AttachExecution",negate=True)
            order_asx.expect("AttachExecution")
            print order_asx.fills
            order_cxa.cancel()
        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)
            if order_asx.orderStatus.primaryStatus != "Complete":
                order_asx.cancel(validate=False)
    def test_amend_order_aggr(self,side,sor,style,symbol_depth):
        """ sor order amend aggr, best price with asx preference."""
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,style=style)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

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

        #depth.clear_depth(symbol=symbol,last=last,build=True,style=style)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_aggr
        t_chia.update(settings.ORDER_TYPES["chia"])
        ## facil order ASX direct with same price at CHIA
        t_asx = order_t.copy()
        t_asx['side'] = side_pass
        t_asx['price'] = price_aggr
        t_asx.update(settings.ORDER_TYPES["asx"])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA order =========")
        print order_cxa

        order_asx = Order(**t_asx)
        order_asx.new()
        print ("======== ASX order =========")
        print order_asx

        gevent.sleep(1)
        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_pass
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)

        try:
            order_sor.new()
            ## no trade
            order_sor.expect("AttachExecution",negate=True)
            ## amend aggr
            order_sor.amend(qty=t_sor['qty']-10,price=price_aggr)
            order_sor.expect("AttachExecution")
            print "sor order fill", order_sor.fills

            order_cxa.expect("AttachExecution",negate=True)
            order_asx.expect("AttachExecution")
            print "asx order fill", order_asx.fills
            order_cxa.cancel()
        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)
            if order_asx.orderStatus.primaryStatus != "Complete":
                order_asx.cancel(validate=False)
    def test_new_order_aggr_chia(self,side,sor,style,symbol_depth):
        """ sor order best price lit sweep."""
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,style=style)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

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

        #depth.clear_depth(symbol=symbol,last=last,build=True,style=style)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_aggr
        t_chia.update(settings.ORDER_TYPES["chia"])
        ## facil order ASX direct with inferior price than CHIA
        t_asx = order_t.copy()
        t_asx['side'] = side_pass
        t_asx['price'] = price_aggr_2
        t_asx.update(settings.ORDER_TYPES["asx"])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA order =========")
        print order_cxa

        order_asx = Order(**t_asx)
        order_asx.new()
        print ("======== ASX order =========")
        print order_asx

        gevent.sleep(1)
        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_aggr_2
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)
        try:
            order_sor.new()
            ## no trade
            order_sor.expect("AttachExecution")
            print order_sor.fills
            ## NoLit new order not sweep CHIA
            if sor not in ("sor6","sor7","sor6_maq","sor7_maq"):
                order_asx.expect("AttachExecution",negate=True)
                order_cxa.expect("AttachExecution")
                print order_cxa.fills
            else:
                ## sor6, 'BestPriceMinQtyNoLit' not sweep chia on new order
                order_cxa.expect("AttachExecution",negate=True)
                ## asx fill will hit vking depth setup order
                #order_asx.expect("AttachExecution")
                #print order_asx.fills
        finally:

            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)
            if order_asx.orderStatus.primaryStatus != "Complete":
                order_asx.cancel(validate=False)
    def test_amend_order_aggr_chia(self,side,sor,style,symbol_depth):
        """ sor order amend aggr, best price with asx preference."""

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,style=style)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = int(attrs.get('MINEXECUTABLEQTY',0))

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

        #depth.clear_depth(symbol=symbol,last=last,build=True,style=style)

        order_t = dict(symbol = symbol,
                        side  = side,
                        price = last,
                        qty   = mxq + random.randint(100,200),
                        xref  = random.choice(settings.CLIENT_XREFS),
                        )
        ## facil order CHIA with better pricce
        t_chia = order_t.copy()
        t_chia['side'] = side_pass
        t_chia['price'] = price_aggr
        t_chia.update(settings.ORDER_TYPES["chia"])
        ## facil order ASX direct with inferior price at CHIA
        t_asx = order_t.copy()
        t_asx['side'] = side_pass
        t_asx['price'] = price_aggr_2
        t_asx.update(settings.ORDER_TYPES["asx"])

        order_cxa = Order(**t_chia)
        order_cxa.new()
        print ("======== CHIA order =========")
        print order_cxa

        order_asx = Order(**t_asx)
        order_asx.new()
        print ("======== ASX order =========")
        print order_asx

        gevent.sleep(1)
        ## test SOR order
        t_sor = order_t.copy()
        t_sor['price'] = price_pass
        t_sor['qty'] = t_sor['qty']
        t_sor['xref'] = random.choice(settings.HOUSE_XREFS)
        t_sor.update(settings.ORDER_TYPES[sor])
        order_sor = Order(**t_sor)

        try:
            order_sor.new()
            ## no trade
            order_sor.expect("AttachExecution",negate=True)
            ## amend aggr
            order_sor.amend(qty=t_sor['qty']-10,price=price_aggr_2)
            order_sor.expect("AttachExecution")
            print "sor order fill", order_sor.fills
            ## sor6 not hit CXA
            if sor not in ('sor6','sor6_maq','sor7','sor7_maq'):
                order_asx.expect("AttachExecution",negate=True)
                order_cxa.expect("AttachExecution")
                print "cxa order fill", order_cxa.fills
            else:
                order_cxa.expect("AttachExecution",negate=True)

        finally:
            ##clean up
            if order_cxa.orderStatus.primaryStatus != "Complete":
                order_cxa.cancel(validate=False)
            if order_sor.orderStatus.primaryStatus != "Complete":
                order_sor.cancel(validate=False)
            if order_asx.orderStatus.primaryStatus != "Complete":
                order_asx.cancel(validate=False)


