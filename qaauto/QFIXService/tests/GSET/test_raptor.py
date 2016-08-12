import random
from datetime import datetime, timedelta, time as dttime, date as dtdate

from tests.fix_order import FIXOrder
import pytest
import gevent

test_session = "RONINDO"

#test_clients = [
#                {'fixId': 'GSETCASH4','starId': '11332394'},
#
#               ]

from tests._utils import active_wait, tickSize, get_passive_price

class Test_DMA:
    """
    test dma order.
    """
#    scenarios = []
#
#    for side in ("Buy"):
#        for test_client in test_clients:
#            client = test_client.copy()
#            client.update({'side': side, 'symbol': '0001.HK'})
#            scenarios.append(client)

    def test_new_amend_cancel(self):
        """ """
        #quote,cha_quote = symbol_depth.get_symbol_quote(symbol)

        #last,bid,ask,close = quote['last'],quote['bid']['bid'],quote['ask']['ask'],quote['close']

        #price = 25.58

        order = {
                'side': 'Buy',
                'symbol': '0001.HK',
                'ordType': "Limit",
                'price': 90,
                'qty': 1000,
                'extra': {
                      #"TargetCompID":"TEST",
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : '0001.HK',
                      #"ExDestination": "SYDE",
                      #"OnBehalfOfCompID": fixId,
                      #"SenderSubID" : "APOLLO",
                      }
                }

        test_order = FIXOrder(test_session,order)
        ## submit new order
        clOrdId, ers = test_order.new()
        assert len(ers) == 1
        assert 'OrderID' in ers[0]
        assert ers[0]['OrdStatus'] == "New"
        assert ers[0]['ExecTransType'] == "New"

        gevent.sleep(1)
        clOrdId, ers = test_order.amend(qty=order['qty'] + 2000,
                                        price=order['price'] + 0.50,
                                        expected_num_msg=1)
        assert len(ers) == 1
        er_replace = ers[0]
        assert er_replace['ExecType'] == "Replace"
        assert er_replace["OrdStatus"] == "Replaced"

        gevent.sleep(1)
        clOrdId, ers = test_order.cancel(expected_num_msg=1)
        assert ers
        assert len(ers) == 1
        assert ers[0]["OrdStatus"] == "Canceled"
        assert ers[0]["ExecType"] == "Canceled"

