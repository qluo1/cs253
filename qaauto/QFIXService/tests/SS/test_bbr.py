import random
from datetime import datetime, timedelta, time as dttime, date as dtdate

from tests.fix_order import FIXOrder
import pytest
import gevent

test_session = "BBRTEST"

"""
Lee, Keith [Tech] 10:45 AM
onshore migrated: PVM.SYD
offshore migrated: ABERDEENAM/WADDELLCRD
offshore non-migrated: ICAIXA
"""
## HK, need manual accept/ack order from dart.
test_clients = [
            ## onshore migrated -- ppe_XTDd
            {'fixId': 'PVM.SYD','starId': '11332394'},
            ## offshore migrated -- ppe_XTDd
            {'fixId': 'ABERDEENAM','starId': '11332394'},
            ## onshore not migrated -- qa_XTDb
            {'fixId': 'VFMC','starId': '11332394'},
            ## offshore not migrated -- ppe_XTDd
            {'fixId': 'ICAIXA','starId': '11332394'},
]

from tests._utils import active_wait, tickSize, get_passive_price

class Test_SS_HT:
    """
    test SS high touch  order, not all order need manual accept/ack at dart.
    """
    scenarios = []

    for side in ("Buy","Sell","Sell Short"):
        for test_client in test_clients:
            client = test_client.copy()
            client.update({'side': side, 'symbol': 'NAB.AX'})
            scenarios.append(client)

    def test_new_amend_cancel(self,side,symbol,fixId,starId,fetch_market_data):
        """ """
        price_data = fetch_market_data(symbol)
        price = float(price_data['HST_CLOSE2'])

        order = {
                'side': side,
                'symbol': symbol,
                'ordType': "Limit",
                'price': price,
                'qty': random.randint(20,50),
                'extra': {
                      "HandlInst"   : "manual",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : symbol,
                      "ExDestination": "SYDE",
                      "OnBehalfOfCompID": fixId,
                      "SendingTime" : datetime.utcnow(),
                      }
                }

        test_order = FIXOrder(test_session,order)

        status = test_order.session_status
        assert status['loggedon'] and status['enabled']
        ## submit new order
        clOrdId, ers = test_order.new()
        assert len(ers) == 1
        assert 'OrderID' in ers[0]
        assert ers[0]['OrdStatus'] == "New"
        assert ers[0]['ExecTransType'] == "New"

        gevent.sleep(10)
        clOrdId, ers = test_order.amend(qty=order['qty'] + 2000,
                                        price=order['price'] + 0.50,
                                        expected_num_msg=2)
        assert len(ers) == 2
        er_pending_replace = ers[0]
        er_replace = ers[1]
        assert er_pending_replace['ExecType'] == "Pending Replace"
        assert er_pending_replace["OrdStatus"] == "Pending Replace"
        assert er_replace['ExecType'] == "Replace"
        assert er_replace["OrdStatus"] == "Replaced"

        gevent.sleep(10)
        clOrdId, ers = test_order.cancel(expected_num_msg=2)
        assert ers
        assert len(ers) == 1
        assert ers[0]["OrdStatus"] == "Canceled"
        assert ers[0]["ExecType"] == "Canceled"

