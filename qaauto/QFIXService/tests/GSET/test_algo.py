import random
from datetime import datetime, timedelta, time as dttime, date as dtdate

from tests.fix_order import FIXOrder
import pytest
import gevent

def _after_hour(implicit = False):
    now = datetime.now()
    if now.time() > dttime(16,15,0):
        #gmt_time = (datetime.utcnow() + timedelta(hours=5)).strftime("%Y%m%d-%H:%M:%S")
        return ",endTime=dayCloseTime+'5h'"
    if implicit:
        return ",endTime=dayCloseTime"
    return ""

test_session = "APOLLO.TEST"
test_clients = [
                {'fixId': 'GS_ARN_D','starId': '11332394'},
               ]

from tests._utils import active_wait, tickSize

class Test_EDGEAlgo_Plutus:
    """
    test algo order to AU EDGEAlgo/Plutus.

    """
    scenarios = []

    for side in ("Buy","Sell","Sell Short"):
        for algo,params in (("VWAP",""),
                           ("GSAT_Participate","limitOTMImpact=false,6064=ASXDirect")):
            for test_client in test_clients:
                client = test_client.copy()
                client.update({'side': side, 'algo': algo, 'algoParam': params})
                scenarios.append(client)

    def test_new_amend_cancel(self,side,algo,algoParam,fixId,starId,symbol_depth,position):
        """ """
        quote,cha_quote = symbol_depth.get_test_symbol()

        starPos = position.get_position(starId)
        assert starPos
        print starPos
        symbol = quote['symbol']
        last,bid,ask,close = quote['last'],quote['bid']['bid'],quote['ask']['ask'],quote['close']

        price = last or  close or bid or ask
        if price == 0:
            price = 0.10

        order = {
                'side': side,
                'symbol': symbol,
                'ordType': "Limit",
                'price': price,
                'qty': random.randint(2000,5000),
                'extra': {
                      "TargetCompID":"TEST",
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : symbol,
                      "Algorithm"   : algo,
                      "ExDestination": "SYDE",
                      "OnBehalfOfCompID": fixId,
                      "SenderSubID" : "JONEIA",
                      "Rule80A"     : "P",
                      "8032"        : algoParam + _after_hour(),
                      }
                }

        test_order = FIXOrder(test_session,order)
        ## submit new order
        clOrdId, ers = test_order.new()
        assert len(ers) == 1
        assert 'OrderID' in ers[0]
        assert ers[0]['OrdStatus'] == "New"
        assert ers[0]['ExecTransType'] == "New"

        gevent.sleep(10)
        newPos = position.get_position(starId)
        assert newPos
        print newPos

        clOrdId, ers = test_order.amend(qty=order['qty'] + 2000,
                                        price=order['price'] + 0.50,
                                        expected_num_msg=2)
        assert len(ers) == 2

        er_pending = ers[0]
        er_replace = ers[1]
        assert er_pending['ExecType'] == "Pending Replace"
        assert er_pending["OrdStatus"] == "Pending Replace"

        assert er_replace['ExecType'] == "Replace"
        assert er_replace["OrdStatus"] == "Replaced"

        gevent.sleep(10)
        amdPos = position.get_position(starId)
        assert amdPos
        print amdPos

        clOrdId, ers = test_order.cancel(expected_num_msg=2)
        assert ers
        assert len(ers) == 2
        assert ers[0]["OrdStatus"] == "Pending Cancel"
        assert ers[0]["ExecType"] == "Pending Cancel"
        assert ers[1]["OrdStatus"] == "Canceled"
        assert ers[1]["ExecType"] == "Canceled"


class Test_EDGEAlgo_Trade:
    """ test algo fill.

    """
    scenarios = []

    for side in ("Buy","Sell","Sell Short"):
        for algo,params in (
                            ("GSAT_Iceberg",""),
                            ("GSAT_Iceberg","minTOSize=10"),

                            ):
            for test_client in test_clients:
                client = test_client.copy()
                client.update({'side': side, 'algo': algo, 'algoParam': params})
                scenarios.append(client)

    def test_new_trade(self,side,algo,algoParam,fixId,starId,symbol_depth):
        """
        """
        symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)

        last,bid,ask,close = quote['last'],quote['bid']['bid'],quote['ask']['ask'],quote['close']

        price = last + tickSize(3,last) if side == "Buy" else last - tickSize(3,last)

        order = {
                'side': side,
                'symbol': symbol,
                'ordType': "Limit",
                'price': price,
                'qty': random.randint(2000,5000),
                'extra': {
                      "TargetCompID":"TEST",
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : symbol,
                      "Algorithm"   : algo,
                      "ExDestination": "SYDE",
                      "OnBehalfOfCompID": fixId,
                      "SenderSubID" : "JONEIA",
                      "8032"        : algoParam + _after_hour(),
                      }
                }


        test_order = FIXOrder(test_session,order)
        ## submit new order
        clOrdId, ers = test_order.new()
        assert len(ers) == 1
        assert 'OrderID' in ers[0]
        assert ers[0]['OrdStatus'] == "New"
        assert ers[0]['ExecTransType'] == "New"

        active_wait(lambda: len(ers) > 1,timeout=90)
        pytest.set_trace()
        if len(ers) == 1:
            ## force clear depth again
            symbol_depth.get_tradable_symbol()
        active_wait(lambda: len(ers) > 1,timeout=60)

        assert len(ers) > 1
        assert ers[-1]['OrdStatus'] == "Partially filled"
        assert ers[-1]['LastMkt'] == 'AX'
        assert ers[-1]['LastPx'] > 0
        assert ers[-1]['LastPx'] > 0
        assert ers[-1]['LastShares'] > 0


        test_order.cancel(expected_num_msg=2)
        print test_order


