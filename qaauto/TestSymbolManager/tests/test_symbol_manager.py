import os
import json
import sys
from datetime import datetime
from pprint import pprint
import symbolManager
from symbolManager import SymbolManager
import gevent


class Test_SymbolManager:

    manager = SymbolManager()

    def setup_class(cls):
        cls.manager.start()

    def test_manager_snapshot(self):
        """ """
        assert len(self.manager.snapshot_.keys()) > 100

        quote = self.manager.snapshot_[self.manager.snapshot_.keys()[0]][0]

        assert 'last' in quote
        assert 'bid' in quote
        assert 'ask' in quote
        assert 'bidSize' in quote['bid']
        assert len(self.manager.snapshot_.keys()) > 1
        assert 'askSize' in quote['ask']
        assert 'numAsks' in quote['ask']
        assert 'timestamp' in quote
        assert 'state' in quote
        assert quote['status'] == 'STATE_OK'

    def test_get_symbols(self):
        """ """
        pid = os.getpid()

        symbols = self.manager.get_test_symbol(pid)
        assert symbols
        assert len(symbols) > 0
        print symbols

    def test_get_open_symbols(self):
        """ """
        pid = os.getpid()
        symbols = self.manager.get_test_symbol(pid,state="OPEN")
        assert symbols
        assert len(symbols) > 0
        #print symbols
        print len(symbols)
    def test_get_pre_open_symbols(self):
        """ """
        pid = os.getpid()
        symbols = self.manager.get_test_symbol(pid,state="PRE_OPEN")
        assert symbols
        assert len(symbols) > 0
        print symbols
        print len(symbols)

    def test_get_pre_close_symbols(self):
        """ """
        pid = os.getpid()
        symbols = self.manager.get_test_symbol(pid,state="PRE_CSPA")
        if len(symbols):
            print symbols
            print len(symbols)


    def test_get_open_symbos_withdepth(self):
        """ """
        pid = os.getpid()
        symbols = self.manager.get_test_symbol(pid,state="OPEN",with_depth=True)
        assert symbols
        assert len(symbols) > 0
        print symbols
        print len(symbols)

    def test_get_open_symbos_withoutdepth(self):
        """ """
        pid = os.getpid()
        symbols = self.manager.get_test_symbol(pid,state="OPEN",without_depth=True)
        assert symbols
        assert len(symbols) > 0
        print symbols
        print len(symbols)

    def test_get_open_symbos_withlast(self):
        """ """
        pid = os.getpid()
        symbols = self.manager.get_test_symbol(pid,state="OPEN",with_last=True)
        assert symbols
        assert len(symbols) > 0
        print symbols
        print len(symbols)

    def test_tradable_symbol(self):
        """ """
        pid = os.getpid()
        rets = self.manager.get_tradable_symbol(pid,state="OPEN")
        pprint (rets)
        symbol,quote_asx,quote_cha = rets
        assert isinstance(quote_asx,dict)
        assert isinstance(quote_cha,dict)
        pprint(symbol)
        pprint(quote_asx)
        pprint(quote_cha)

    def test_tradable_symbol_with_mxq(self):
        """ """
        pid = os.getpid()
        rets = self.manager.get_tradable_symbol(pid,with_mxq=True)
        pprint (rets)
        symbol,quote_asx,quote_cha = rets
        assert isinstance(quote_asx,dict)
        assert isinstance(quote_cha,dict)
        pprint(symbol)
        pprint(quote_asx)
        pprint(quote_cha)


    def test_load_run_tradable_symbol(self):
        """ """
        pid = os.getpid()

        start = datetime.now()
        for x in range(100):
            inst = self.manager.get_tradable_symbol(pid,state="OPEN")
            assert 'symbol' in inst
            assert 'asx' in inst
            assert 'cha' in inst
            print inst['symbol']
            pprint(inst['asx'])
        end = datetime.now()

        print (end-start).total_seconds()/100.0




ENDPOINT = "tcp://localhost:20193"
import zerorpc
class MySymbolManager(zerorpc.Subscriber):

    def __init__(self):
        """ """
        super(MySymbolManager,self).__init__()

    def start(self):
        """ """
        self.connect(ENDPOINT)
        ## kick off subscriber 
        self.worker_ = gevent.spawn(self.run)
        ## client 

    def on_market_quote(self,data):
        """ callback on new market quote, from subscriber."""
        try:
            quote = json.loads(data)
            symbol = quote['symbol']
            ## save quote snapshot
            print symbol, quote

        except Exception,e:
            print("unexpected: %s" % e)

class MySymbolManagerTWO():
    def __init__(self):
        """ """

        self.subscriber_ = zerorpc.Subscriber(methods={'on_market_quote':self.on_market_quote})

    def start(self):
        """ """
        self.subscriber_.connect(ENDPOINT)
        ## kick off subscriber 
        self.worker_ = gevent.spawn(self.subscriber_.run)
        ## client 

    def on_market_quote(self,data):
        """ callback on new market quote, from subscriber."""
        try:
            quote = json.loads(data)
            symbol = quote['symbol']
            ## save quote snapshot
            print symbol, quote

        except Exception,e:
            print("unexpected: %s" % e)

def _test_POC():
    #m = MySymbolManager()
    m = MySymbolManagerTWO()

    m.start()
    gevent.sleep(100)

