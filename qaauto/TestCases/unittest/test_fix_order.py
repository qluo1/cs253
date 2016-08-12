from datetime import datetime
from apollo import pyfix42
from apollo.qfix_client import QFIX_ClientSession


def test_new_order_single():
    """ """

    session =QFIX_ClientSession("APOLLO.TEST")

    status = session.check_session()

    assert isinstance(status,dict)
    assert status['loggedon'] == True

    clOrdId = session.nextClOrdID

    msg = {'MsgType'    : 'NewOrderSingle',
           'OrdType'    : 'Limit',
           'TimeInForce': 'Day',
           'Side'       : 'Buy',
           'Symbol'     : 'ANZ.AX',
           'Price'      : '24.10',
           'SecurityID' : 'ANZ.AX',
           'IDSource'   : 'RIC code',
           'ClOrdID'    :  clOrdId,
           'OrderQty'   : 109,
           'TransactTime': datetime.utcnow(),
           'OnBehalfOfCompID': 'GSETCASH2',
           #"Text"       : "PPEXDMa",
           #"11007"      : "0",
           "Algorithm"  : "VWAP",
           "HandlInst"  : "auto-private",
           "ExDestination": "SYDE",
           "Rule80A"       : "A",
           }
    ## validate test order
    fix_msg = pyfix42.construct(msg)
    ack = session.send_apollo_order(msg)
    assert ack
    print ack

    res = session.get_results(clOrdId)
    assert isinstance(res,list)
    assert len(res) == 1
    print res

    ## validation

    ack = res[0]
    assert ack['MsgType'] == "ExecutionReport"
    assert ack['OrdStatus'] == "New"
    assert ack['ClOrdID'] == clOrdId
    assert ack['ExecType'] == "New"



