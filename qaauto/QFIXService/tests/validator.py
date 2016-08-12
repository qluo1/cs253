import logging

log = logging.getLogger(__name__)

def Generic_Validator(er):
    """ generic FIX/ER validation. """

    assert isinstance(er,dict)
    assert er["MsgType"] in ("ExecutionReport", "OrderCancelReject")

    ## tag 11
    assert "ClOrdID" in er
    ## tag 37
    assert "OrderID" in er
    ## tag 39
    assert "OrdStatus" in er

    if er["MsgType"] == "ExecutionReport":
        ## tag 17
        assert "ExecID" in er
        ## 150
        assert "ExecType" in er

        ## security/symbol
        assert  "Symbol" in er
        assert "SecurityID" in er
        assert "IDSource" in er

        ## side 54
        assert "Side" in er
        ## 14
        assert "CumQty" in er
        ## 151
        assert "LeavesQty" in er

    else:
        assert "CxlRejResponseTo" in er


