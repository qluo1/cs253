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



class AmendStyle:
    """ amend style. """

    PRICEONLY = 0
    PRICEQTY  = 1
    QTYUP     = 2
    QTYDOWN   = 3

class Test_SOR_Auction_Amend:

    """ test sor order amend during auction phase.

    - amend price only or amend price/qty
    - check child order after new and after amend.
    - extract exchange orderId
    - check if exchange orderId has changed?!

    current: exchange orderId will be changed
    new: exchange orderId will not changed i.e. native amend.

    """

    scenarios = []
    amendStyles = (AmendStyle.PRICEONLY,
                   AmendStyle.PRICEQTY,
                   AmendStyle.QTYUP,
                   AmendStyle.QTYDOWN,
                   )

    auctionStyles = [
                    'PRE_CSPA',
                    'PRE_OPEN']

    for sor in settings.SOR_NODIRECT:
        for side in settings.TEST_SIDES:
            for amendStyle in amendStyles:
                for auctionStyle in auctionStyles:
                    data = dict(sor=sor,side=side,amendStyle=amendStyle,auctionStyle=auctionStyle)
                    scenarios.append(data)

    def test_new_amend_sor_order_at_auction(self,side,sor,amendStyle,auctionStyle,symbol_depth):
        """ order basic - new/amend for all order types . """

        try:
            if auctionStyle == "PRE_OPEN":
                symbol, quote, cha_quote, attrs = symbol_depth.get_pre_open_symbol()
            else:
                symbol, quote, cha_quote, attrs = symbol_depth.get_pre_cspa_symbol()
        except Exception,e:
            if e.name == "ValueError" and 'no test symbols available' in e.traceback:
                pytest.skip(e)

        bid,ask,last,close = quote['bid']['bid'], quote['ask']['ask'], quote['last'],quote['close']

        last = last or close or float(attrs.get('CLOSEPRICE',0.10))
        ## workaround 
        if last <= 0.001: last = 0.003

        if side == 'Buy':
            price_aggr = last + tickSize(last,1)
            price_pass = last - tickSize(last,1)
            price_pass_2 = last - tickSize(last,2)
        else:
            price_aggr = last - tickSize(last,1)
            price_pass = last + tickSize(last,1)
            price_pass_2 = last + tickSize(last,2)

        order_t = dict(symbol =symbol,
                        side   =side,
                        price  =last,
                        qty    =random.randint(100,200), #+ mxq,
                        xref   = random.choice(settings.CLIENT_XREFS),
                        )

        order = order_t.copy()
        order.update(settings.ORDER_TYPES[sor])
        print ("========== sor order ============")
        ## test sor order
        test_sorOrder = Order(**order)
        ##
        test_sorOrder.new()
        print(test_sorOrder)

        try:
            #pytest.set_trace()
            childs = test_sorOrder.query_child_orders()
            assert len(childs) > 0
            ## child is live 
            child_order_status = [o['orderStatusData']['primaryStatus'] for o in childs]

            assert len([s for s in child_order_status if s == "Working"]) > 0, child_order_status
            extRefs = [o['orderStatusData']['externalReferences'] for o in childs]
            exch_order_ids_new = []
            for extRef in extRefs:
                exch_order_ids_new += [o['tag'] for o in extRef if o['externalObjectIdType'] == "ExchangeId"]

            assert len(exch_order_ids_new) > 0

            if amendStyle ==  AmendStyle.PRICEQTY:
                test_sorOrder.amend(price=price_aggr,qty=order['qty']-5)
            elif amendStyle == AmendStyle.PRICEONLY:
                test_sorOrder.amend(price=price_aggr)
            elif amendStyle == AmendStyle.QTYDOWN:
                test_sorOrder.amend(qty=order['qty'] - 5)
            elif amendStyle == AmendStyle.QTYUP:
                test_sorOrder.amend(qty=order['qty'] + 10)
            else:
                assert False, "unknown amend style: %s" % amendStyle

            childs_amend = test_sorOrder.query_child_orders()

            assert len(childs_amend) > 0
            ## child is live 
            child_order_status = [o['orderStatusData']['primaryStatus'] for o in childs_amend]
            if len([s for s in child_order_status if s == "Working"]) == 0:
                ## child order either rejected or traded
                pytest.skip("child order either rejected or filled: %s" % childs_amend)

            extRefs = [o['orderStatusData']['externalReferences'] for o in childs_amend if o['orderStatusData']['primaryStatus'] == "Working"]

            exch_order_ids_amend = []
            for extRef in extRefs:
                exch_order_ids_amend += [o['tag'] for o in extRef if o['externalObjectIdType'] == "ExchangeId"]

            assert len(exch_order_ids_amend) > 0

            if amendStyle == AmendStyle.QTYDOWN:
                assert sorted(exch_order_ids_amend) == sorted(exch_order_ids_new)
            else:
                assert sorted(exch_order_ids_amend) == sorted(exch_order_ids_new)

        finally:
            test_sorOrder.cancel(validate=False)
