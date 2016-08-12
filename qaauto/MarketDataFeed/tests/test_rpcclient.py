import zerorpc
import gevent
from pprint import pprint
import pytest
import os,sys


MONGO="/gns/mw/lang/python/modules/2.7.2/pymongo-2.9/lib/python2.7/site-packages"
if MONGO not in sys.path:
    sys.path.append(MONGO)
from bson import json_util
##0RPC data server
RPC_ENDPOINT = "tcp://localhost:30192"
SUB_ENDPOINT = "tcp://localhost:30193"

### test remote
#RPC_ENDPOINT = "tcp://d48965-004.dc.gs.com:20192"
#SUB_ENDPOINT = "tcp://d48965-004.gd.gs.com:20193"
#
client = zerorpc.Client(heartbeat=30)
client.connect(RPC_ENDPOINT)

def test_get_quote():

    print client.get_quote("CSL.AX")

    print client.get_quote("ADD")

def test_list_symbols():
    symbols = client.list_symbols(exchange="AX")
    cha_symbols = client.list_symbols(exchange="CHA")
    all_symbols = client.list_symbols()


    #print symbols
    print len(symbols)
    print len(cha_symbols)
    print len(all_symbols)

    print cha_symbols
    no_stocks = [i for i in symbols if i[1] not in ( 'OPEN',None)]
    print no_stocks

def test_list_synmbols_no_quote():

    all_symbols_no_quote = client.list_symbols(with_quote=False)
    print all_symbols_no_quote
    print  len(all_symbols_no_quote)
    assert 'RFP.CHA' not in all_symbols_no_quote

@pytest.mark.skipif("True")
def test_subscribe_symbol():

    symbols = ['AGLIYF.AX','ANZHA.AX','NABHA.AX']
    client.subscribe_symbols('DF_ASX_QA',symbols)

    gevent.sleep(2)
    all_symbols_no_quote = client.list_symbols(with_quote=False)
    for symbol in symbols:
        assert symbol not in all_symbols_no_quote

def test_on_market_quote():
    """
    """
    endpoint = SUB_ENDPOINT
    trigger = gevent.event.Event()
    class Subscriber(zerorpc.Subscriber):
        count = 0
        def on_market_data(self,quote):
            print quote
            #quote = json.loads(quote)
            #print quote
            self.count +=1
            if self.count > 10:
                trigger.set()

    client = Subscriber()
    client.connect(endpoint)
    gevent.spawn(client.run)
    trigger.wait()


def test_get_depth():
    quote = client.get_quote("BHP.AX")
    assert quote
    print "BHP.AX quote" 
    print quote

    quote = client.get_depth("BHP.AX")
    assert quote
    print "BHP.AX depth" 
    print quote

    quote = client.get_quote("BHP.CHA")
    assert quote
    print "BHP.CHA quote"
    print quote

    quote = client.get_depth("BHP.CHA")
    assert quote
    print "BHP.CHA depth"
    print quote

    quote = client.get_quote("BHP")
    assert quote
    print "BHP quote"
    print quote

    quote = client.get_depth("BHP")
    assert quote
    print "BHP depth"
    print quote

def test_testdepth_remove():
    symbol = "CCL"

    quote = client.get_quote(symbol)
    print "%s quote" % symbol
    pprint(quote)
    depth = client.get_depth(symbol)
    assert depth
    print "%s depth" % symbol
    pprint(depth)

