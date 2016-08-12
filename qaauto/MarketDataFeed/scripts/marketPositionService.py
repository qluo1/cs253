""" market quote data service.


"""
import logging
import cfg
from marketDataListener import QuoteManager
import gevent
import zerorpc
from conf import settings
from collections import namedtuple

## config python logging
logging.config.dictConfig(settings.LOGGING)
log = logging.getLogger("marketPositionService")

class QuoteListener(object):
    """ """
    ## track all market quote
    quotes_         = {}

    publisher_ = zerorpc.Publisher()
    publisher_.bind(settings.RPC_PUB_ENDPOINT)

    def on_market_quote(self, quote):
        """ market data publisher callback. """
        try:
            assert isinstance(quote,dict)
            symbol = quote['SYMBOL']
            if symbol not in self.quotes_:
                self.quotes_[symbol] = None
            self.quotes_[symbol] = quote

            method = getattr(self.publisher_,settings.MARKET_PUBLISH_METHOD)
            method(self.quotes_[symbol])
        except Exception,e:
            log.exception(e)


    def get_pos_data(self,starId):
        """ """

        ret = {}
        for key in self.quotes_.keys():
            if key.startswith(starId):
                ret[key] = self.quotes_[key]
        return ret

class  MarketDataServer(zerorpc.Server):
    """ """
    def __init__(self,dataMgr,dataListener):
        """ hold a reference of a quote manager. """
        assert isinstance(dataMgr,QuoteManager)
        assert isinstance(dataListener,QuoteListener)
        self.manager_ = dataMgr
        self.listener_ = dataListener


        super(MarketDataServer,self).__init__(methods= {
                        ## 
                        'subscribe_symbols': self.subscribe_symbols,
                        'get_position': self.listener_.get_pos_data,
                        }
                        )

    def subscribe_symbols(self,symbols,**kw):
        """ """
        service = kw.get("service",settings.SERVICES[0])
        if isinstance(symbols,list) and len(symbols) > 0:
            ss = [s for s in symbols if s not in self.manager_.quotes_.keys()]
            if ss:
                self.manager_.subscribe(service,ss)
            else:
                raise ValueError("list of symbol required or symbol already subscribed: %s" % symbols)


_starIds = []
def get_pos_keys():
    """ helper query starId for au client. """
    global _starIds
    if not any(_starIds):
        db_service = zerorpc.Client(settings.OM2DBSERVICE_URL,heartbeat=30)
        _starIds = db_service.list_client_starId()

    au_starIds = ["%s.AUSHARESCASH.USD" % i for i in _starIds]
    au_starIds += ["%s.AUSHARESCFD.USD" % i for i in _starIds]

    return au_starIds

def run_as_service():
    """ """
    ## get market symbol
    symbols = get_pos_keys()
    import signal
    import singleton
    me = singleton.SingleInstance()
    dataMgr = QuoteManager()
    if dataMgr.init():
        print "quote manager is running"
    else:
        print "manager not running"
        exit(1)
    dataListener = QuoteListener()
    ## setup listener
    subscriber = zerorpc.Subscriber(methods={settings.MARKET_PUBLISH_METHOD:dataListener.on_market_quote})
    subscriber.connect(settings.INTERNAL_PUB_ENDPOINT)
    gevent.spawn(subscriber.run)

    ## subscribe market data for symbol
    dataMgr.subscribe(settings.SERVICES[0],symbols)
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

