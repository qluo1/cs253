""" symbol_depth service.

depend on market data service and om2 viking for clear/build depth.

"""
import sys
import os
import logging
import logging.config
import collections
import random
import signal
from datetime import datetime,timedelta
## setup local path
import cfg

import zerorpc
import gevent

from conf import settings
logging.config.dictConfig(settings.LOGGING)

log = logging.getLogger(__name__)
SIZE_LIMIT = 5000000
## last price > 5c
MIN_LAST_LIMIT = 0.05

class TestClient(object):
    """ map one to one for a test client session.

    track: current_symbol,
           client pid
           how long it has lived

    """

    ## db service
    dbservice_ = zerorpc.Client(heartbeat=settings.HEARTBEAT_TIMEOUT)
    dbservice_.connect(settings.OM2DBSERVICE_RPC_ENDPOINT)

    def __init__(self,pid,snapshot):
        """ """
        self.pid_ = pid
        ## reference of market snapshot 
        self.snapshot_ = snapshot
        ##  client creation datetime
        self.timestamp = datetime.now()
        ## track currently being tested symbol
        self.current_test_symbol_ = None

    def get_test_symbols(self,**kw):
        """ """
        state = kw.get("state","OPEN")
        assert state in ("OPEN","PRE_OPEN","PRE_CSPA","PRE_NR")
        with_last = kw.get("with_last",False)
        with_depth = kw.get("with_depth",False)
        without_depth = kw.get("without_depth",False)
        min_last_limit = kw.get("min_last",MIN_LAST_LIMIT)
        black_list = kw.get("blaklist",[])
        ## symbol must with mxq
        with_mxq = kw.get("with_mxq",False)
        top_100 = kw.get("top100",False)
        top_200 = kw.get("top200",False)
        top_300 = kw.get("top300",False)

        ## all open asx symbols for specified state
        asx_symbols = [s for s in self.snapshot_ \
                        if s.endswith("AX") and \
                            self.snapshot_[s][0]['state'] == state and \
                            s.split(".")[0] + ".CHA" in self.snapshot_ and \
                            self.snapshot_[s][0]['bid'] and self.snapshot_[s][0]['ask'] and \
                            self.snapshot_[s.split(".")[0] + ".CHA"][0]['state'] == "" and \
                            (self.snapshot_[s][0]['bid']['undisclose'] == 0 or self.snapshot_[s][0]['ask']['undisclose'] == 0) and \
                            (self.snapshot_[s][0]['bid']['bidSize'] < SIZE_LIMIT  or self.snapshot_[s][0]['ask']['askSize'] < SIZE_LIMIT)
                      ]


        gevent.sleep(0)
        if black_list:
            asx_symbols = [s for s in asx_symbols if s not in black_list]

        if with_depth:
            asx_symbols = [s for s in asx_symbols if (self.snapshot_[s][0]['bid']['numBids'] > 0 or self.snapshot_[s][0]['ask']['numAsks'] > 0)]

        if without_depth:
            asx_symbols = [s for s in asx_symbols if (self.snapshot_[s][0]['bid']['numBids'] == 0 and self.snapshot_[s][0]['ask']['numAsks'] == 0)]

        if with_last:
            asx_symbols = [s for s in asx_symbols if self.snapshot_[s][0]['last'] > min_last_limit]

        gevent.sleep(0)
        ## filter symbol with mxq
        def filter_mxq(symbol):
            gevent.sleep(0)
            attrs = self.dbservice_.query_symbol_attrs(s)
            if  'MINEXECUTABLEQTY' in attrs:
                return True
            return False
        if with_mxq:
            gevent.sleep(0)
            total = len(asx_symbols)
            asx_symbols = [s for s in asx_symbols if filter_mxq(s)]
            log.info("snapshot: %d, total selected: %d, filtered with_mxq: %d" % (len(self.snapshot_.keys()),total, len(asx_symbols)))

        ## filter top 200
        if top_100:
            top_100_symbols = self.dbservice_.list_top_100()
            gevent.sleep(0)
            asx_symbols = [s for s in asx_symbols if s in top_100_symbols]

        ## filter top 200
        if top_200:
            top_200_symbols = self.dbservice_.list_top_200()
            gevent.sleep(0)
            asx_symbols = [s for s in asx_symbols if s in top_200_symbols]

        ## filter top 300
        if top_300:
            top_300_symbols = self.dbservice_.list_top_300()
            gevent.sleep(0)
            asx_symbols = [s for s in asx_symbols if s in top_300_symbols]

        return asx_symbols

    @property
    def current_symbol(self):
        return self.current_test_symbol_

    @current_symbol.setter
    def current_symbol(self,symbol):
        self.current_test_symbol_ = symbol

    @property
    def pid(self):
        return self.pid_

    @pid.setter
    def pid(self,pid):
        self.pid_ = pid

from vikingDepthService import VkDepth

class SymbolManager():
    """ """

    def __init__(self):
        """ """
        self.subscriber_ = zerorpc.Subscriber(methods={'on_market_data':self.on_market_quote})
        self.api_ = zerorpc.Client(heartbeat=settings.HEARTBEAT_TIMEOUT)
        ## quote api server
        self.api_.connect(settings.QUOTE_RPC_ENDPOINT)

        self.clients_ = {}
        ## market quote snapshot
        self.snapshot_ = {}

        ## viking depth service
        self.depthService_ = VkDepth(self.snapshot_)
        ## blacklist symbol
        self.blacklist_ = []

        self.timestamp_ = datetime.now()

    def start(self):
        """ """
        ## setup black list from config
        for symbol in settings.SYMBOL_BLACK_LIST:
            symbol = symbol.upper()
            if not symbol.endswith("AX"):
                symbol = symbol + ".AX"
            self.blacklist_.append(symbol)

        ## extract current market snapshot
        log.info("start symbol manager: query market snapshot image.")
        for quote in self.api_.get_snapshot():
            symbol = quote['symbol']
            self.snapshot_[symbol] = collections.deque([quote],maxlen=1)
        log.info("updated %d symbols. " % len(self.snapshot_.keys()))
        ## start live quote listener
        self.subscriber_.connect(settings.QUOTE_PUB_ENDPOINT)
        ## kick off subscriber  in greenlet
        self.worker_ = gevent.spawn(self.subscriber_.run)
        log.info("subscribed live quote at: %s" % settings.QUOTE_PUB_ENDPOINT)

    def on_market_quote(self,quote):
        """ callback on new market quote, from subscriber."""
        try:
            symbol = quote['symbol']
            log.debug("quote update: %s" % quote)
            ## save quote snapshot
            if symbol not in self.snapshot_:
                self.snapshot_[symbol] = collections.deque([quote],maxlen=1)
            else:
                self.snapshot_[symbol].append(quote)

        except Exception,e:
            log.exception(e)

    def _select_tradable_symbol(self,client,test_symbols,**kw):
        """ try to test if symbol is tradable."""

        ## client has specified a desired symbol
        specified_symbol = kw.get("symbol")
        ## randomize test symbols
        random.shuffle(test_symbols)
        ## set client specified symbol as preferred.
        if specified_symbol:
            client.current_symbol = specified_symbol
        try:
            symbol = client.current_symbol
            if symbol:
                kw['symbol'] = symbol
                if self.depthService_.clear_depth(client.pid,**kw):
                    return symbol
            else:
                raise ValueError("initial run")
        except ValueError,e:

            log.warn("current symbol failed: %s, %s" % (symbol,e))
            ## try to find a symbol can be traded.
            for symbol in test_symbols:
                log.info("test symbol: %s" % symbol)
                gevent.sleep(0)
                #import pdb;pdb.set_trace()
                try:
                    kw['symbol'] = symbol
                    if self.depthService_.clear_depth(client.pid,**kw):
                        return symbol
                except ValueError,e:
                    log.warn("fail to clear depth for %s, %s" % (symbol,e))
                    continue

    def get_test_symbol(self,pid,**kw):
        """ request a testable symbol for the test process. """

        if pid not in self.clients_:
            self.clients_[pid] = TestClient(pid,self.snapshot_)

        client = self.clients_[pid]
        test_symbols = client.get_test_symbols(**kw)
        ## filter blacklist
        test_symbols = [s for s in test_symbols if s not in self.blacklist_]

        if len(test_symbols)  == 0:
            raise ValueError("no test symbols available: %s" % kw)

        ## return current_symbol if still valid
        if client.current_symbol and client.current_symbol in test_symbols:
            return self.get_symbol_quote(client.current_symbol)

        symbol = random.choice(test_symbols)
        client.current_symbol= symbol

        return self.get_symbol_quote(symbol)

    def get_symbol_quote(self,symbol):
        """ return symbol quote snapshot."""
        assert symbol.endswith(".AX")

        ticker,exch = symbol.split(".")
        asx_symbol = ticker + ".AX"
        cha_symbol = ticker + ".CHA"

        asx_quote,cha_quote = self.snapshot_[asx_symbol][0], self.snapshot_[cha_symbol][0]

        return (asx_quote,cha_quote)

    def get_tradable_symbol(self,pid,**kw):
        """ """
        if pid not in self.clients_:
            self.clients_[pid] = TestClient(pid,self.snapshot_)

        if  'state' in kw:
            assert kw['state'] == "OPEN"
        else:
            kw['state'] = "OPEN"
        ## 
        if 'with_last' not in kw :
            kw['with_last'] = True

        client_blacklist= kw.get("blacklist",[])

        ## current test symbol exclude current client
        client_current_test_symbols = [v.current_symbol for k,v in self.clients_.iteritems() if k != pid]

        client = self.clients_[pid]

        test_symbols = client.get_test_symbols(**kw)
        ## filter out blacklist and current testing symbols
        test_symbols = [s for s in test_symbols if s not in self.blacklist_ + client_blacklist + client_current_test_symbols]
        ## try to find a tradable symbol for the client
        symbol = self._select_tradable_symbol(client,test_symbols,**kw)
        #import pdb;pdb.set_trace()
        ## refresh quote  for the symbol
        quotes = self.get_symbol_quote(symbol)
        ## set the tradable symbol for the client.

        client.current_symbol = symbol

        return (symbol,quotes[0], quotes[1])

    def cleanup(self):
        """ """
        ## cleanup old test client older than 1 day
        now = datetime.now()
        for pid,client in self.clients_.items():
            if now - client.timestamp_  > timedelta(days=1):
                self.clients_.pop(pid)

def run_as_service():
    """ """
    ## single instance.
    from singleton import SingleInstance
    me = SingleInstance(__name__)
    ## 
    manager = SymbolManager()
    manager.start()
    server = zerorpc.Server(methods={
        'get_test_symbol': manager.get_test_symbol,
        'get_symbol_quote': manager.get_symbol_quote,
        'get_tradable_symbol': manager.get_tradable_symbol,
        },heartbeat=settings.HEARTBEAT_TIMEOUT)

    def trigger_shutdown():
        """ shutdown event loop."""
        log.info("signal INT received, stop event loop.")
        server.stop()

    log.info("binding endpoing: %s" % settings.SYMBOL_MANAGER_API_ENDPOINT)
    server.bind(settings.SYMBOL_MANAGER_API_ENDPOINT)
    log.info("setup signal for INT/QUIT")
    ## register signal INT/QUIT for proper shutdown
    gevent.signal(signal.SIGINT,trigger_shutdown)
    gevent.signal(signal.SIGTERM,trigger_shutdown)

    server.run()
    print "exited"

if __name__ == "__main__":
    "" ""
    run_as_service()
