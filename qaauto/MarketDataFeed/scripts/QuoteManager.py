#! /bin/env python
""" quote manager -- listening and publishing live market quote.

subscribe GS MarketDataToolkit and publish live quote data.

also expose API for query,subscribe current market data via zerorpc.
"""
import sys
import random
import Queue
import time
import traceback
import logging
import logging.config
from threading import Thread
## app specific config
from cfg import MyMDTListener, StringVector, setuplog, json
from cfg import settings
import zmq
from concurrent.futures import Future
import signal

log = logging.getLogger(__file__)
## config python logging
logging.config.dictConfig(settings.LOGGING)

## helper
from Quote import Quote
## ignore following fields
filters = ()

class QuoteManager(object):

    """ main class manage MDT live quote.

    - init MDT envrionment
    - subscribe symbol for live qutoes
    - unscribe symbol

    """
    quoteData_      = Queue.Queue()
    subscribeQueue_ = Queue.Queue()
    requestQueue_   = Queue.Queue()
    quotes_         = {}
    stop_flag_      = False
    ## zmq
    ## replay
    repSock_        = None
    ## pub
    pubock_         = None
    ## poller
    poller_         = None

    def onQuoteData(self,data):
        """ callback function, from MyMDTListener.

        quote data is a pydict.
        """
        try:
            log.info("onQuoteData called:%s" % data)
            ret = {}
            for k,v in data.items():
                if k in filters:
                    continue
                else:
                    ret[k] = v
            self.quoteData_.put(ret)
        except Exception,e:
            log.error("unexpected error on process incoming MDT quote data: %s" % e)

    def onStatusUpdate(self,data):
        """ callback function, from MyMDTListener on status.

        remove any invalid symbol. based on status code.
        {'desc': 'F10: Not In Cache', 'code': 'CODE_INFO', 'class': 'CLASS_ITEM','entity': 'ORSN.CHA'}
        """

        try:
            log.info("onStatus called: %s" %  data)
            code = data['code']
            entity = data['entity']
            class_item = data['class']
            desc = data['desc']
            ## remove junk symbol
            if desc == 'F10: Not In Cache' and code == 'CODE_INFO':
                if entity in self.quotes_:
                    self.quotes_.pop(entity)
        except Exception,e:
            log.error("unexpected error on processing onStatusUpdate: %s" % e)

    def init(self):
        """ kick off listener and processing thread. """

        ## setup gslogging
        if not setuplog(settings.LOGCFG,"QuoteManager",settings.LOG_DIR):
            log.error("setup gs logging failed")
            return False
        services = StringVector()
        for service in settings.SERVICES:
            services.append(service)

        log.info("env: %s, user: %s, service: %s" % (settings.ENV,settings.USER,services))
        self.listener_ = MyMDTListener(settings.ENV,settings.USER,services)
        ## register callback
        self.listener_.setupOnDataCB("onQuoteData",self)
        self.listener_.setupOnStatusCB("onStatusUpdate",self)

        self.runner_ = Thread(target=self.run)
        self.runner_.setDaemon(True)

        self.runner_.start()
        log.info("initialized and run")

        return self.runner_.isAlive()

    def run(self):
        """ processing incoming request and quote.  """
        ## zerorpc publisher
        publisher_ = zerorpc.Publisher()
        publisher_.bind(settings.RPC_PUB_ENDPOINT)
        ## setup zmq publisher
        context = zmq.Context()
        self.pubSock_ = context.socket(zmq.PUB)
        self.pubSock_.bind(settings.PUB_QUOTE_ENDPOINT)
        self.poller_ = zmq.Poller()
        self.poller_.register(self.repSock_,zmq.POLLIN)

        while not self.stop_flag_:
            """
                1. check quote queue
                2. publish quote to ZMQ
            """
            try:

                try:
                    req = self.subscribeQueue_.get_nowait()
                    log.info("subscribe quote for :%s" % req)
                    assert type(req) == list
                    ## req should be already validated as a list of dict
                    ss_asx = StringVector()
                    ss_cxa = StringVector()

                    for s in req:
                        symbol = s['symbol']
                        if symbol not in self.quotes_:
                            self.quotes_[symbol] = Quote(**s)
                            if symbol.endswith(".AX"):
                                ss_asx.append(symbol)
                            elif symbol.endswith(".CHA"):
                                ss_cxa.append(symbol)
                            else:
                                #log.error("unknown symbol being specified: %s, symbol should end with either .AX or .CHA" % s)
                                log.warn("subscribe symbol: %s to asx" % symbol)
                                ss_asx.append(symbol)
                    ## ASX
                    if len(ss_asx) > 0:
                        if not self.listener_.subscribe(settings.SERVICES[0], ss_asx):
                            log.error("subsribe ASX failed for : %s" % ss_asx)
                    ## CHIA
                    if len(ss_cxa) > 0:
                        if not self.listener_.subscribe(settings.SERVICES[1],ss_cxa):
                            log.error("subscribe CHIA failed for : %s" % ss_cxa)
                except Queue.Empty:
                    pass

                try:
                    ## process incoming quote data
                    quote = self.quoteData_.get(timeout=0.01)
                    symbol = quote['SYMBOL']
                    log.info("prossing mdt quote data:%s, size:%d" % (symbol,self.quoteData_.qsize()))
                    ## quote object must already exist
                    self.quotes_[symbol].parse(quote)
                    log.info("quote updated: %s" % self.quotes_[symbol])
                    ## publish to ZMQ here
                    snapshot = self.quotes_[symbol].toJson()
                    self.pubSock_.send_multipart([symbol,snapshot])
                    ## publish to zerorpc
                    publisher_.on_market_quote(self.quotes_[symbol].toJson())
                except Queue.Empty:
                    pass

            except Exception,e:
                publisher_.stop()
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.info("failed for runner exit here: error: %s, tb: %s" % (e,traceback.extract_tb(exc_traceback)))
                sys.exit(1)

        publisher_.stop()

    def shutdown(self):
        """ unscribe all symbols and stop internal thread.  """

        log.info("shutdown called")
        cxa_ss = StringVector()
        asx_ss = StringVector()
        for symbol in self.quotes_:
            if symbol.endswith(".AX"):
                asx_ss.append(symbol)
            if symbol.endswith(".CHA"):
                cxa_ss.append(symbol)

        if len(asx_ss) > 0:
            if not self.listener_.unsubscribe(settings.ASX_SERVICE,asx_ss):
                log.error("unscribe failed for ASX: %s" % asx_ss)

        if len(cxa_ss) > 0:
            if not self.listener_.unsubscribe(settings.CXA_SERVICE,cxa_ss):
                log.error("unscribe failed for CXA: %s" % cxa_ss)

        self.stop_flag_ = True
        ## wait runner to finish
        self.runner_.join()
        print "finished"

    def subscribe(self,symbols):
        """ helper to subscribe symbol(s).  """

        if isinstance(symbols,list) and len(symbols) > 0:
            ## validate symbols structure
            ss = [{'symbol': str(s), 'category': 'STOCK'} for s in symbols]
            self.subscribeQueue_.put(ss)
        else:
            raise ValueError("unexpected type: symbols must in list")

import gevent
import zerorpc
from collections import namedtuple

MQuote = namedtuple("Quote","symbol,state,last,vwap,bid,ask,match,close")
class  MarketDataServer(zerorpc.Server):
    """ """

    ## black list symbols
    blacklists_ = []

    def __init__(self,mgr):
        """ hold a reference of a quote manager. """
        assert isinstance(mgr,QuoteManager)
        self.manager_ = mgr

        for symbol in settings.IGNORE_SYMBOLS:
            if symbol not in self.blacklists_:
                self.blacklists_.append(symbol)
        super(MarketDataServer,self).__init__()

    def get_quote(self,symbol):
        """ get quote for a symbol. """
        log.debug("request quote called: %s" % symbol)
        ## local reference
        _quotes = self.manager_.quotes_

        if symbol.endswith("AX") or symbol.endswith("CHA"):
            if symbol not in _quotes:
                raise ValueError("not subscribed or unknown symbol [ %s]?" % symbol)
            s = symbol
            return MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,
                          _quotes[s].bid[0:2] if _quotes[s].bid else [0,0] ,
                          _quotes[s].ask[0:2] if _quotes[s].ask else [0,0] ,
                          _quotes[s].match,
                          _quotes[s].close)

        asx_symbol = symbol.upper() + ".AX"
        cha_symbol = symbol.upper() + ".CHA"

        if asx_symbol not in _quotes and cha_symbol not in _quotes:
                raise ValueError("not subscribed or unknown symbol [%s]?" % symbol)

        ret = {'AX':None, 'CHA': None}
        if asx_symbol in _quotes:
            s = asx_symbol
            ret['AX'] = MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                 _quotes[s].match,_qiptes[s].close)
        if cha_symbol in _quotes:
            s = cha_symbol
            ret['CHA'] = MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,
                                  _quotes[s].bid[0:2] if _quotes[s].bid else [0,0],
                                  _quotes[s].ask[0:2] if _quotes[s].ask else [0,0] ,
                                  _quotes[s].match,
                                  _quotes[s].close)

        return ret

    def list_symbols(self,**kw):
        """ list active symbols for market. """

        exch = kw.get("exchange")
        with_quote = kw.get("with_quote",True)

        if exch not in ("AX","CHA",None):
            raise ValueError("invalid exchange option [%s] : AX or CHA expected." % exch)

        _quotes = self.manager_.quotes_

        if with_quote:
            if exch:
                symbols = [MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                    _quotes[s].match,_quotes[s].close)
                            for s in _quotes.keys() if s.endswith(exch) and _quotes[s].status == "STATE_OK"]
            else:
                symbols = [MQuote(s,_quotes[s].state,_quotes[s].last,_quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                    _quotes[s].match,_quotes[s].close)
                            for s in self.manager_.quotes_.keys() if self.manager_.quotes_[s].status == "STATE_OK"]

            ## filter out blacklist
            return [s for s in symbols if s[0] not in self.blacklists_]

        if exch:
            return [s for s in  _quotes.keys() if s.endswith(exch)]

        return _quotes.keys()

    def list_asx_symbols(self):
        """ helper. """
        return self.list_symbols(exchange="AX")

    def list_chia_symbols(self):
        """ helper. """
        return self.list_symbols(exchange="CHA")

    def subscribe_symbols(self,symbols):
        """ """
        if isinstance(symbols,list) and len(symbols) > 0:
            for symbol in symbols:
                if symbol not in self.manager_.quotes_.keys():
                    self.manager_.subscribe([{'symbol': symbol}])
        elif isinstance(symbols,str):
            if symbols not in self.manager_.quotes_.keys():
                self.manager_.subscribe([{'symbol': symbols}])
        else:
            raise ValueError("list of symbol or single symbol required: %s" % symbols)
    @zerorpc.stream
    def get_snapshot(self):
        """ generator for current market snapshot. """

        _quotes = self.manager_.quotes_
        ## keys return a copy of list of symbol
        for k in _quotes.keys():
            try:
                yield _quotes[k].toJson()
            except KeyError:
                continue

### helper to load symbols
def test_index():
    """ """
    symbol_idx = []
    symbol_idx.append({'category': 'STOCK', 'symbol': '0#ASXE'})
    return symbol_idx

def get_au_symbols():
    """ helper query prime for au symbols. """
    db_service = zerorpc.Client(settings.OM2DBSERVICE_URL,heartbeat=30)
    asx_symbols = db_service.list_asx_symbols()
    chia_symbols = db_service.list_chia_symbols()
    return asx_symbols + chia_symbols

def run_as_service():
    """ """
    #test_symbols = get_au_symbols()
    #assert test_symbols and len(test_symbols) > 0

    import singleton
    me = singleton.SingleInstance()
    mgr = QuoteManager()
    if mgr.init():
        print "quote manager is running"
    else:
        print "manager not running"
        exit(1)

    signal.signal(signal.SIGINT,lambda signal,frame: mgr.shutdown())

    test_symbols = ['2345.HKSHARESCASH.USD']

    mgr.subscribe(test_symbols)

    ## start rpc server 
    server = MarketDataServer(mgr)
    server.bind(settings.API_ENDPOINT)
    gevent.spawn(server.run)

    ##
    while mgr.runner_.isAlive():
        gevent.sleep(1)

    server.close()

if __name__ == "__main__":
    """ """
    run_as_service()

