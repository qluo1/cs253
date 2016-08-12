from tests.fix_order import FIXOrder

def test_new_amend_cancel_order():
    """ AU unittest case for GSET Algo/Plutus."""

    session = "APOLLO.TEST"

    msg = {
           'ordType'    : 'Limit',
           'side'       : 'Buy',
           'symbol'     : 'NAB.AX',
           'price'      : '27.10',
           'qty'        : 109,
           'extra': {
                    # "OnBehalfOfCompID": "GSETCASH4",
                     #"Text": "PPEXDMa",
                     "TargetCompID":"TEST",
                     "HandlInst": "auto-private",
                     "IDSource": "RIC code",
                     "SecurityID": "NAB.AX",
                     "Algorithm": "VWAP",
                     "ExDestination": "SYDE",
                     "OnBehalfOfCompID": "GS_ARN_D",
                     "SenderSubID": "JONEIA",
                     "8032": "endTime=dayCloseTime+5h",
                     }
          }


    test_order = FIXOrder(session,msg)

    clOrdId, ers =  test_order.new()
    assert ers
    print clOrdId, ers
    assert len(ers) == 1
    assert 'OrderID' in ers[0]
    assert ers[0]['OrdStatus'] == "New"
    assert ers[0]['ExecTransType'] == "New"

    clOrdId, ers = test_order.amend(qty=2000,price=28.10,expected_num_msg=2)
    assert ers
    print clOrdId, ers
    assert len(ers) == 2

    er_pending = ers[0]
    er_replace = ers[1]
    assert er_pending['ExecType'] == "Pending Replace"
    assert er_pending["OrdStatus"] == "Pending Replace"

    assert er_replace['ExecType'] == "Replace"
    assert er_replace["OrdStatus"] == "Replaced"


    clOrdId, ers = test_order.cancel(expected_num_msg=2)
    assert ers
    print clOrdId, ers
    assert len(ers) == 2
    assert ers[0]["OrdStatus"] == "Pending Cancel"
    assert ers[0]["ExecType"] == "Pending Cancel"
    assert ers[1]["OrdStatus"] == "Canceled"
    assert ers[1]["ExecType"] == "Canceled"





