""" market quote data service.


"""
import logging
import cfg
from marketDataListener import QuoteManager
import gevent
import zerorpc
import copy
from conf import settings
from collections import namedtuple,deque

## helper
from Quote import Quote, convert_depth

## config python logging
logging.config.dictConfig(settings.LOGGING)
log = logging.getLogger("marketDataService")

MQuote = namedtuple("Quote","symbol,state,last,vwap,bid,ask,match,close")


class QuoteListener(object):
    """ """
    ## track all market quote
    quotes_         = {}

    publisher_ = zerorpc.Publisher()
    publisher_.bind(settings.RPC_PUB_ENDPOINT)

    blacklists_ = []
    ## setup internal filter
    for symbol in settings.IGNORE_SYMBOLS:
        if symbol not in blacklists_:
            blacklists_.append(symbol)

    def on_market_quote(self, quote):
        """ market data publisher callback. """
        try:
            assert isinstance(quote,dict)
            symbol = quote['SYMBOL']
            ## ignore depth
            if symbol.endswith("d"):
                if symbol[:-1] in self.quotes_:
                    self.quotes_[symbol[:-1]].parse_depth(quote)
                ## ignore symbol not already registered.
                return

            if symbol not in self.quotes_:
                self.quotes_[symbol] = Quote(symbol=symbol,category="STOCK")

            log.debug("prossing mdt quote data:%s, %s" % (symbol,quote))
            ## quote object must already exist
            self.quotes_[symbol].parse(quote)
            log.info("quote updated: %s" % self.quotes_[symbol])

            ## publish to zerorpc
            method = getattr(self.publisher_,settings.MARKET_PUBLISH_METHOD)
            method(self.quotes_[symbol].toData())
        except Exception,e:
            log.exception(e)

    ### helper methods
    def get_quote(self,symbol):
        """ get quote for a symbol. """
        log.info("request quote called: %s" % symbol)
        ## local reference
        _quotes = self.quotes_

        if symbol.endswith("AX") or symbol.endswith("CHA"):
            if symbol not in _quotes:
                raise ValueError("not subscribed or unknown symbol [ %s]?" % symbol)
            if symbol in _quotes and _quotes[symbol].image_timestamp is None:
                raise ValueError("symbol: [%s] not updated yet" % sybmol)
            s = symbol
            return MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                            _quotes[s].match,_quotes[s].close)

        asx_symbol = symbol.upper() + ".AX"
        cha_symbol = symbol.upper() + ".CHA"

        if asx_symbol not in _quotes and cha_symbol not in _quotes:
                raise ValueError("not subscribed or unknown symbol [%s]?" % symbol)

        ret = {'AX':None, 'CHA': None}
        if asx_symbol in _quotes:
            s = asx_symbol
            ret['AX'] = MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                 _quotes[s].match,_quotes[s].close)
        if cha_symbol in _quotes:
            s = cha_symbol
            ret['CHA'] = MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                  _quotes[s].match,_quotes[s].close)

        return ret

    def get_depth(self,symbol,**kw):
        """ """
        log.info("request quote called: %s" % symbol)
        ## local reference
        _quotes = self.quotes_

        ret = {'asx': None, 'cxa': None}

        if symbol.endswith("AX") or symbol.endswith("CHA"):
            if symbol not in _quotes:
                raise ValueError("not subscribed or unknown symbol [ %s]?" % symbol)

            if not hasattr(_quotes[symbol],'depth'):
                ret['error'] = "error no depth found for %s" % symbol
                return ret
            ## return symbol depth
            depth = _quotes[symbol].depth

            ret['asx'] = convert_depth(copy.deepcopy(depth))
        else:
            asx_symbol = symbol + ".AX"
            cha_symbol = symbol + ".CHA"

            if asx_symbol in _quotes and hasattr(_quotes[asx_symbol],"depth"):
                ret['asx'] = convert_depth(copy.deepcopy(_quotes[asx_symbol].depth))
            if cha_symbol in _quotes and hasattr(_quotes[cha_symbol],"depth"):
                ret['cxa'] = convert_depth(copy.deepcopy(_quotes[cha_symbol].depth))

        return ret


    def list_symbols(self,**kw):
        """ list active symbols for market. """

        exch = kw.get("exchange")
        with_quote = kw.get("with_quote",True)

        if exch not in ("AX","CHA",None):
            raise ValueError("invalid exchange option [%s] : AX or CHA expected." % exch)

        ## filter out bad quote, no image timestamp 
        _quotes = self.quotes_

        if with_quote:
            if exch:
                symbols = [MQuote(s,_quotes[s].state,_quotes[s].last, _quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                    _quotes[s].match,_quotes[s].close)
                            for s in _quotes.keys() if s.endswith(exch) and _quotes[s].status == "STATE_OK" and _quotes[s].image_timestamp]
            else:
                symbols = [MQuote(s,_quotes[s].state,_quotes[s].last,_quotes[s].vwap,_quotes[s].bid[0:2],_quotes[s].ask[0:2],
                                    _quotes[s].match,_quotes[s].close)
                            for s in _quotes.keys() if _quotes[s].status == "STATE_OK" and _quotes[s].image_timestamp]

            ## filter out blacklist
            return [s for s in symbols if s[0] not in self.blacklists_]

        if exch:
            return [s for s in  _quotes.keys() if s.endswith(exch) if _quotes[s].image_timestamp]

        return _quotes.keys()

    def list_asx_symbols(self):
        """ helper. """
        return self.list_symbols(exchange="AX")

    def list_chia_symbols(self):
        """ helper. """
        return self.list_symbols(exchange="CHA")

    @zerorpc.stream
    def get_snapshot(self):
        """ generator for current market snapshot. """

        _quotes = self.quotes_
        ## keys return a copy of list of symbol
        for k in _quotes.keys():
            try:
                ## filter out bad symbol
                if _quotes[k].image_timestamp != None:
                    yield _quotes[k].toData()
            except Exception,e:
                log.exception(e)


class  MarketDataServer(zerorpc.Server):
    """ """
    ## black list symbols
    blacklists_ = []

    def __init__(self,dataMgr,dataListener):
        """ hold a reference of a quote manager. """
        assert isinstance(dataMgr,QuoteManager)
        assert isinstance(dataListener,QuoteListener)
        self.manager_ = dataMgr
        self.listener_ = dataListener


        super(MarketDataServer,self).__init__(methods= {
                        'get_quote': self.listener_.get_quote,
                        'get_depth': self.listener_.get_depth,
                        'list_symbols': self.listener_.list_symbols,
                        'list_asx_symbols': self.listener_.list_asx_symbols,
                        'list_chia_symbols': self.listener_.list_chia_symbols,
                        'get_snapshot': self.listener_.get_snapshot,
                        ## 
                        'subscribe_symbols': self.subscribe_symbols,
                        }
                        )

    def subscribe_symbols(self,service,symbols):
        """ """
        if isinstance(symbols,list) and len(symbols) > 0:
            ss = [s for s in symbols if s not in self.manager_.quotes_.keys()]
            if ss:
                self.manager_.subscribe(service,ss)
            else:
                raise ValueError("list of symbol required or symbol already subscribed: %s" % symbols)



def run_as_service():
    """ """

    import importlib
    import signal
    import singleton
    import sys
    if (sys.argv)>1:
        me = singleton.SingleInstance(sys.argv[1])
    else:
        me = singleton.SingleInstance()

    #############################################
    ## get market symbol from configured module
    mod = importlib.import_module(settings.SYMBOL_MODULE)
    symbols = mod.get_subscribe_symbols()

    ####################################
    ## start listener 
    dataListener = QuoteListener()
    ## setup listener
    subscriber = zerorpc.Subscriber(methods={settings.MARKET_PUBLISH_METHOD:dataListener.on_market_quote})
    subscriber.connect(settings.INTERNAL_PUB_ENDPOINT)
    gevent.spawn(subscriber.run)

    ####################################
    ## start pubisher
    dataMgr = QuoteManager()
    if dataMgr.init():
        print "quote manager is running"
    else:
        print "manager not running"
        exit(1)

    ## subscribe market data for symbol
    for service,symbols in symbols.iteritems():
        dataMgr.subscribe(service,symbols)

    ####################################
    ## start rpc server 
    server = MarketDataServer(dataMgr,dataListener)
    server.bind(settings.API_ENDPOINT)

    def trigger_shutdown():
        log.info("shutdown called")
        server.close()
        subscriber.close()
        dataMgr.shutdown()

    log.info("register signal interrupt")
    ## register signal INT/QUIT for proper shutdown
    gevent.signal(signal.SIGINT,trigger_shutdown)
    server.run()

if __name__ == "__main__":
    """ """
    run_as_service()

