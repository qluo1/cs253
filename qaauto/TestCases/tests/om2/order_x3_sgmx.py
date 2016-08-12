""" test cases for X3 matching engine.

test cases for X3/Plutus matching behaviour.

manual intraday switch by update RDS -- one symbol per day only.

"""
from datetime import datetime
import time
import copy
import random
from pprint import pprint
import pytest

from utils import (
              valid_rf_ack,
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              active_wait,
              AckFailed,
              DepthStyle,
              SeqNumber,
              )
from om2Order import Order
from conf import settings
import gevent

#symbol = 'NAB.AX'
#symbol = 'ANZ.AX'
#symbol = 'FXL.AX'
symbol = 'CAB.AX'
#symbol = 'MGR.AX'

X3_STAR_IDS = [
               "1000015",
               "1072",
               "1079",
               "1098",
               "11224768",
               "11204109"
               ]


ETFS = ['IKO.AX',]
class Test_Amend_Count:
    """
    test multiple amend for
    - Limit/Market 
    - market state in OPEN/PRE_OPEN/PRE_CSPA
    """
    scenarios = []

    for orderType in (
            "Limit",
            "Market",):
        for marketState in (
                        'OPEN',
                        'PRE_OPEN',
                        'PRE_CSPA',):
            scenarios.append(dict(orderType=orderType,marketState=marketState))

    def test_amend_count(self,orderType, marketState,symbol_depth):
        try:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(state=marketState,top200=True,blacklist=ETFS)
            bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
            mxq = int(attrs.get("MINEXECUTABLEQTY",100))
            pprint(quote)
        except Exception,e:
            if e.msg.startswith("no test symbols available"):
                pytest.skip(e)

        order_t = dict(symbol  = symbol,
                        side   = "Buy",
                        price  = last,
                        qty    = 1,
                        orderType = orderType,
                        xref = "FC2",
                        extra= {
                                'businessUnit': 'DMA',
                                'clientStarId': random.choice(X3_STAR_IDS),
                                },
                        )

        if orderType == "Market":
            order_t['price'] = 0
        psgmxBuyTemplate = order_t.copy()
        psgmxBuyTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
        psgmxBuyOrder = Order(**psgmxBuyTemplate)
        psgmxBuyOrder.new()
        print (" ========== PLUTUSSGMX buy order =============")
        print(psgmxBuyOrder)
        psgmxBuyOrder.expect_ok()

        # Perform 100 amends, then check the external references
        for new_qty in range(2,12):
            psgmxBuyOrder.amend(qty = new_qty)

        childId = psgmxBuyOrder._childs[0]
        childOrder = psgmxBuyOrder.requestOrderImage(childId)
        print (" ========== PLUTUSSGMX child order =============")
        pprint(childOrder)
        latestColtVersionTag = childOrder['orderStatusData']['externalReferences'][-1]['tag']

        psgmxBuyOrder.cancel()

def _setup_darkpool(symbol,darkPool):
    """ """
    print "symbol: %s, pool: %s" %(symbol,darkPool)
    ## update RDS  setup symbol for X3 or Plutus
    rds_cmd = {
        'cmd': 'updateSharedMemoryFeederRecord',
        'handle': 'updateSharedMemoryFeederRecord',
        'argumentVector': [
            {'arg': 'Insert df OmPreferenceInfo [ name String "%s.AU..Routing" ] [ value String "%s" ]' % (symbol,darkPool) },
        ]
    }
    #print rds_cmd
    ack = Order.sendRdsHermes(rds_cmd)
    assert "Success" == ack['status']
    gevent.sleep(40)

class Test_X3_Cross:
    """
    validate X3 crossing behaviour.

    1) new buy, sell limit/market within MID, cross

    2) multiple buy orders, one sell limit/mrket within MID, cross multiple

    3) new buy order with maq, sell limit/market below maq, amend qty above maq cross

    4) new buy_1, buy_2,  sell qty below buy_1 qty cross with buy_1, keep/queue priority

    5) new buy_1 with maq, buy_2 without maq, sell qty below maq cross with buy_2, bypass/queue priority

    6) new buy_1 with maq, buy_2 without maq, sell qty above maq below buy_q qty cross with buy_1, keep/queue priority

    7) new buy 30, sell 100/maq 40 limit/market amend maq down 30, expect fill


    """
    scenarios = []

    for orderType in (
            "Limit",
            "Market",):
        for side in settings.TEST_SIDES:
                scenarios.append(dict(orderType=orderType,side=side))

    def setup_class(cls):
        """ """
        from conftest import SymbolDepthManager
        symbol_depth=SymbolDepthManager(symbol=symbol)
        t_symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,top200=True)
        ## ensure symbol match specified
        assert t_symbol == symbol

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        pprint(quote)
        cls.data_ = {'symbol': t_symbol,
                      'asx': quote,
                      'cxa': cha_quote,
                      'attrs': attrs,
                      'bid': bid,
                      'ask': ask,
                      'last': last,
                      }

        cls.order_t = dict(symbol  = t_symbol,
                            side   = "Buy",
                            price  = last,
                            qty    = random.choice(range(1000,3000)),
                            xref   = 'FC2',
                            system = "IOSAdapter",
                            extra = {'businessUnit': 'SS',
                                     'clientStarId': random.choice(X3_STAR_IDS),
                                     "serviceOffering":"GSAT"},)
        ## sigmaX order
        cls.order_t.update(settings.DARK_ORDER_TYPES['sigmax'])
        ## hard coded value
        _setup_darkpool(symbol,"SGMX")
        #### X3 no need xref
        cls.system_ = "AUMEA"
        cls.order_t.pop("xref")
        #_setup_darkpool(symbol,"PLUTUS")
        #cls.system_ = "PlutusSGMX"

    def _check_system(self,order):
        """ """
        childs = order.query_child_orders()
        assert len(childs) == 1
        print (" ========== child order =============")
        pprint(childs)
        systemName = childs[0]['orderStatusData']['externalReferences'][-1]['systemName']
        assert systemName == self.system_
        return systemName

    def test_new_order_cross(self,orderType,side):

        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        ## 
        if orderType == "Market":
            order["price"] = 0
        test_one = Order(**order)
        test_one.new()
        print (" ==========  buy order =============")
        print(test_one)
        ## reverse
        order['side'] = opposite_side(order['side'])
        test_two = Order(**order)
        test_two.new()
        print (" ==========  sell order =============")
        print(test_two)

        try:
            test_one.expect("AttachExecution")
            test_two.expect("AttachExecution")
            ## check system name
            self._check_system(test_one)

        finally:
            for order in (test_one,test_two):
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()
    def test_new_order_mxq_cross(self,orderType,side):

        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        ## 
        if orderType == "Market":
            order["price"] = 0

        orderQty = order['qty']
        order['maq'] = 100
        test_one = Order(**order)
        test_one.new()
        print (" ==========  buy order =============")
        print(test_one)

        ###############
        ## reverse
        order['side'] = opposite_side(order['side'])
        order['qty'] = 99
        ## X3 not support mxq above qty.
        order.pop('maq')
        test_two = Order(**order)
        test_two.new()
        print (" ==========  sell order =============")
        print(test_two)

        try:
            ## no order should be traded.
            test_one.expect("AttachExecution",negate=True)
            test_two.expect("AttachExecution",negate=True)
            ## amend qty up
            test_two.amend(qty=orderQty)

            test_one.expect("AttachExecution")
            test_two.expect("AttachExecution")
            ## check system name
        finally:
            for order in (test_one,test_two):
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()

    def test_multiple_new_orders_cross(self,orderType,side):

        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        orderQty = self.order_t['qty']
        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        if orderType == "Market":
            order['price'] = 0

        test_orders = []
        for qty in (5,10,20,30,35,orderQty-100):
            order['qty'] = qty
            test= Order(**order)
            test.new()
            print (" ==========  buy order =============")
            print(test)
            test_orders.append(test)

        ## reverse
        order['side'] = opposite_side(order['side'])
        order['qty'] = orderQty
        test_two = Order(**order)
        test_two.new()
        print (" ==========  sell order =============")
        print(test_two)
        test_orders.append(test_two)

        try:
            for order in test_orders:
                order.expect("AttachExecution")
            ## check system name

        finally:
            for order in test_orders:
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()

    def test_new_orders_cross_keep_priority(self,orderType,side):
        """ new order fill, keep/queue priority """

        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        ## 
        if orderType == "Market":
            order["price"] = 0
        test_orders = []

        order['qty'] = 100
        test_one = Order(**order)
        test_one.new()
        test_orders.append(test_one)
        print (" ==========  buy order =============")
        print(test_one)


        order['qty']=100
        test_two = Order(**order)
        test_two.new()
        test_orders.append(test_two)
        print (" ==========  buy order =============")
        print(test_two)

        ## reverse
        order['side'] = opposite_side(order['side'])
        test_three = Order(**order)
        test_three.new()
        test_orders.append(test_three)
        print (" ==========  sell order =============")
        print(test_three)

        try:
            test_one.expect("AttachExecution")
            test_two.expect("AttachExecution",negate=True)
            test_three.expect("AttachExecution")
            test_two.cancel()
            ## check system name
            self._check_system(test_one)
        finally:
            ## in case exception, cleanup
            for order in test_orders:
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()

    def test_new_orders_cross_bypass_priority(self,orderType,side):
        """ bypass priority on maq constrain.

        """
        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        ## 
        if orderType == "Market":
            order["price"] = 0
        test_orders = []

        order['qty'] = 100
        order['maq'] = 50
        test_one = Order(**order)
        test_one.new()
        test_orders.append(test_one)
        print (" ==========  buy order =============")
        print(test_one)

        order['qty']=100
        order.pop("maq")
        test_two = Order(**order)
        test_two.new()
        test_orders.append(test_two)
        print (" ==========  buy order =============")
        print(test_two)

        ## reverse
        order['side'] = opposite_side(order['side'])
        order['qty'] = 40
        test_three = Order(**order)
        test_three.new()
        test_orders.append(test_three)
        print (" ==========  sell order =============")
        print(test_three)

        try:
            test_one.expect("AttachExecution",negate=True)
            test_two.expect("AttachExecution")
            test_three.expect("AttachExecution")
            test_one.cancel()
            ##
            self._check_system(test_one)

        finally:
            for order in test_orders:
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()

    def test_new_orders_cross_maq_keep_priority(self,orderType,side):
        """ keep priority with maq constrain.

        """
        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        ## 
        if orderType == "Market":
            order["price"] = 0
        test_orders = []

        order['qty'] = 100
        order['maq'] = 50
        test_one = Order(**order)
        test_one.new()
        test_orders.append(test_one)
        print (" ==========  buy order =============")
        print(test_one)

        order['qty']=100
        order.pop("maq")
        test_two = Order(**order)
        test_two.new()
        test_orders.append(test_two)
        print (" ==========  buy order =============")
        print(test_two)

        ## reverse
        order['side'] = opposite_side(order['side'])
        order['qty'] = 80
        test_three = Order(**order)
        test_three.new()
        test_orders.append(test_three)
        print (" ==========  sell order =============")
        print(test_three)

        try:
            ##Plutus bit slow
            gevent.sleep(2)
            test_one.expect("AttachExecution")
            test_two.expect("AttachExecution",negate=True)
            test_three.expect("AttachExecution")
            test_two.cancel()
            # validate
            self._check_system(test_one)
        finally:
            for order in test_orders:
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()

    def test_new_order_amend_mxq_cross(self,orderType,side):

        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType
        ## 
        if orderType == "Market":
            order["price"] = 0

        orderQty = order['qty']
        order['qty'] = 30
        test_one = Order(**order)
        test_one.new()
        print (" ==========  buy order =============")
        print(test_one)

        ###############
        ## reverse
        order['side'] = opposite_side(order['side'])
        order['qty'] = 100
        ## X3 not support mxq above qty.
        order['maq'] = 40
        test_two = Order(**order)
        test_two.new()
        print (" ==========  sell order =============")
        print(test_two)

        try:
            ## no order should be traded.
            test_one.expect("AttachExecution",negate=True)
            test_two.expect("AttachExecution",negate=True)
            ## amend qty up
            test_two.amend(qty=orderQty,maq=30)

            test_one.expect("AttachExecution")
            test_two.expect("AttachExecution")
            ## check system name
        finally:
            for order in (test_one,test_two):
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()

    def test_amend_order_amend_mxq_cross(self,orderType,side):
        """ amend price from passive to mid. """

        if orderType == "Market":
            pytest.skip("skip market order for price amend")

        symbol,bid,ask,last = self.data_['symbol'],self.data_['bid'],self.data_['ask'],self.data_['last']

        delta = -3 if opposite_side(side) == "Buy" else 3

        order = copy.deepcopy(self.order_t)
        order['side'] = side
        order['orderType'] = orderType

        orderQty = order['qty']
        orderPrice = order['price']
        test_one = Order(**order)
        test_one.new()
        print (" ==========  buy order =============")
        print(test_one)

        ###############
        ## reverse
        order['side'] = opposite_side(order['side'])
        order['qty'] = 100
        order['price'] = orderPrice + tickSize(orderPrice,delta)
        ## X3 not support mxq above qty.
        test_two = Order(**order)
        test_two.new()
        print (" ==========  sell order =============")
        print(test_two)

        try:
            ## no order should be traded.
            test_one.expect("AttachExecution",negate=True)
            test_two.expect("AttachExecution",negate=True)
            ## amend qty/price up
            test_two.amend(qty=orderQty,price=orderPrice)

            test_one.expect("AttachExecution")
            test_two.expect("AttachExecution")
            ## check system name
        finally:
            for order in (test_one,test_two):
                if order.orderStatus.primaryStatus != "Complete":
                    order.cancel()


