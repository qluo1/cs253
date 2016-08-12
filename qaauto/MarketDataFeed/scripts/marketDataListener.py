"""Python MDT listener -- listening and publishing live market data to internal stocket.

subscribe GS MarketDataToolkit and publish live quote data.

also expose API for query,subscribe current market data via zerorpc.
"""
import sys
import random
import Queue
import collections
import time
import traceback
import logging
import logging.config
from threading import Thread
## app specific config
from cfg import MyMDTListener, StringVector, setuplog, json
from cfg import settings
import zmq
import zerorpc
import gevent

log = logging.getLogger(__name__)

## ignore following fields
filters = ()

class QuoteManager(object):

    """ main class manage MDT live quote.

    - init MDT envrionment
    - subscribe symbol for live qutoes
    - unscribe symbol

    """
    ## internal processing queue
    #quoteData_      = Queue.Queue()
    quoteData_      = collections.deque()
    ## subscribe queue
    subscribeQueue_ = Queue.Queue()
    ## caching latest quote data
    quotes_         = {}
    ## running flag
    stop_flag_      = False

    def onQuoteData(self,data):
        """ callback function, from MyMDTListener.

        quote data is a pydict.
        """
        try:
            #log.debug("onQuoteData called:%s" % data)
            #ret = {}
            #for k,v in data.items():
            #    if k in filters:
            #        continue
            #    else:
            #        ret[k] = v
            #self.quoteData_.put(ret)
            #self.quoteData_.put(data)
            self.quoteData_.append(data)
        except Exception,e:
            log.error("unexpected error on process incoming MDT quote data: %s" % e)

    def onStatusUpdate(self,data):
        """ callback function, from MyMDTListener on status.

        remove any invalid symbol. based on status code.
        {'desc': 'F10: Not In Cache', 'code': 'CODE_INFO', 'class': 'CLASS_ITEM','entity': 'ORSN.CHA'}
        {'desc': 'No Longer Trading', 'code': 'CODE_INFO', 'class': 'CLASS_ITEM', 'entity': 'BCT.AXd'}
        """
        try:
            code = data['code']
            entity = data['entity']
            class_item = data['class']
            desc = data['desc']
            ## important info for subscriber status
            if class_item == "CLASS_SUBSCRIBER":
                log.info("onStatus CLASS_SUBSCRIBER: %s" % data)
            else:
                log.debug("onStatus called: %s" %  data)
            ## remove junk symbol
            if code == 'CODE_INFO' and desc in ('F10: Not In Cache',
                                                'F2: Source application did not respond.',
                                                'No Longer Trading'):
                ## work out symbol in which service
                for service,quotes in self.quotes_.items():
                    if entity in quotes:
                        self.quotes_[service].pop(entity)

        except Exception,e:
            log.error("unexpected error on processing onStatusUpdate: %s" % e)

    def init(self):
        """ kick off listener and processing thread. """

        ## setup gslogging
        if not setuplog(settings.LOGCFG,"marketDataListener",settings.LOG_DIR):
            log.error("setup gs logging failed")
            return False
        services = StringVector()
        for service in settings.SERVICES:
            services.append(service)
            self.quotes_[service] = {}

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
        publisher_.bind(settings.INTERNAL_PUB_ENDPOINT)
        while not self.stop_flag_:
            """
            1. check quote queue
            2. publish quote to ZMQ internal configured endpoint.
            """
            try:
                try:
                    reqs = self.subscribeQueue_.get_nowait()
                    log.info("subscribe quote for :%s" % reqs)
                    assert isinstance(reqs,dict)
                    ## req should be already validated as a dict of 
                    ## {'service_name': [list of symbol],}
                    for service,symbols in reqs.iteritems():
                        ## should never happen
                        assert service in self.quotes_, "service [%s] not registered" % service

                        ss = StringVector()
                        assert isinstance(symbols,list)
                        ## track subscribed symbols
                        for symbol in symbols:
                            if symbol not in self.quotes_[service]:
                                self.quotes_[service][symbol] = None
                                ss.append(symbol)

                        ## subscribe symbols for the service.
                        if len(ss) > 0:
                            if not self.listener_.subscribe(service,ss):
                                log.error("subsribe failed for : %s, %s" % (service, ss))
                except Queue.Empty:
                    pass

                try:
                    ## process incoming quote data
                    #quote = self.quoteData_.get(timeout=0.01)
                    quote = self.quoteData_.popleft()
                    symbol = quote['SYMBOL']
                    #log.info("prossing mdt quote data:%s, size:%d" % (symbol,self.quoteData_.qsize()))
                    log.info("prossing mdt quote data:%s, size:%d" % (symbol,len(self.quoteData_)))

                    ## publish to zerorpc
                    method = getattr(publisher_,settings.MARKET_PUBLISH_METHOD)
                    method(quote)
                #except Queue.Empty:
                except IndexError:
                    gevent.sleep(0.01)

            except Exception,e:
                log.exception(e)

        publisher_.close()

    def shutdown(self):
        """ unscribe all symbols and stop internal thread.  """

        log.info("shutdown called")

        for service in self.quotes_.keys():
            ss = StringVector()
            for symbol in self.quotes_[service].keys():
                ss.append(symbol)
                if len(ss) > 0:
                    if not self.listener_.unsubscribe(service,ss):
                        log.error("unscribe failed for %s: %s" % (service,ss))

        self.stop_flag_ = True
        ## wait runner to finish
        self.runner_.join()
        log.info(" ===== market data listener stopped ==== ")
        print "finished"

    def subscribe(self,service, symbols):
        """ helper to subscribe symbol(s).  """

        if service not in self.quotes_:
            raise ValueError("service [%s] hasn't not registered, available service: %s" % (service,self.quotes_.keys()))

        if isinstance(symbols,list) and len(symbols) > 0:
            ## validate symbols structure
            ss = {service: symbols}
            self.subscribeQueue_.put(ss)
        else:
            raise ValueError("unexpected type: symbols must in list")

