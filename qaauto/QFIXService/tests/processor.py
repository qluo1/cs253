import logging
from conf import settings

log = logging.getLogger(__name__)

def Base_Processor(request):
    """ convert low case mandatory field into FIX tag."""

    if 'ordType' in  request:
        request['OrdType'] = request.pop("ordType")
    if 'msgType' in request:
        request['MsgType'] = request.pop("msgType")
    if 'qty' in request:
        request['OrderQty'] = request.pop("qty")
    if 'clOrdId' in request:
        request['ClOrdID'] = request.pop("clOrdId")
    if 'side' in request:
        request['Side'] = request.pop("side")
    if 'price' in request:
        request['Price'] = request.pop("price")
    if 'transTime' in request:
        request['TransactTime'] = request.pop("transTime")
    if 'symbol' in request:
        request['Symbol'] = request.pop("symbol")
    if 'tif' in request:
        request['TimeInForce'] = request.pop("tif")

    if 'Currency' not in request:
        request['Currency'] = settings.DEFAULT_CURRENCY

def NewOrderSingle(request):
    """ handle new order single specific tags."""

    assert isinstance(request,dict)
    if request['MsgType'] == "NewOrderSingle":
        ## process new order 
        if request['Side'] in ('Short','ShortExempt'):
           request['LocateReqd'] ='Y'

def OrderCancelReplaceRequest(request):
    """ handle order amend specific tags."""

    assert isinstance(request,dict)
    if request['MsgType'] == "OrderCancelReplaceRequest":
        if 'origClOrdId' in request:
            request['OrigClOrdID'] = request.pop("origClOrdId")

        ## for algo order tag 8031/8032 is invalid in amend. however, apollo need algorithm for routing purpose.
        #if 'Algorithm' in request:
        #    request.pop('Algorithm')
        #if '8032' in request:
        #    request.pop('8032')



def OrderCancelRequest(request):
    """ handle order cancel specific tags."""

    assert isinstance(request,dict)
    if request['MsgType'] == "OrderCancelRequest":

        if 'origClOrdId' in request:
            request['OrigClOrdID'] = request.pop("origClOrdId")

        ## for algo order tag 8031/8032 is invalid in amend.
        if 'Algorithm' in request:
            request.pop('Algorithm')
        if '8032' in request:
            request.pop('8032')

### BBR, currency = USD
def BBRTEST_currency(request):
    """ handle new order single specific tags."""

    assert isinstance(request,dict)
    if 'Currency' in request:
        request["Currency"] = "USD"
