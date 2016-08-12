#! /bin/env python
import os
import sys
import time
import traceback

from cfg import json
from conf import settings
import logging
import logging.config
import threading
import gevent
import zerorpc
import signal
from collections import deque
from pprint import pprint

log = logging.getLogger("listenQuote")
## config python logging
logging.basicConfig(filename="quotehist.log",level=logging.DEBUG,format='%(asctime)s %(message)s')



def format_current_quote(quote):
    """ """

    

class Listener:

    current_quote = {'asx': deque(maxlen=1),
                     'cxa': deque(maxlen=1)}

    def __init__(self,endpoint,symbol="BHP"):
        """ init """
        self.symbol = symbol.upper()
        ## setup listener
        self.subscriber = zerorpc.Subscriber(methods={settings.MARKET_PUBLISH_METHOD:self.on_market_quote})
        self.subscriber.connect(endpoint)
        self.subscriber.run()

        if "." in self.symbol:
            self.symbol = self.symbol.split(".")[0]

    def on_market_quote(self, data):
        """ market data publisher callback. """
        try:
            quote = json.loads(data)
            assert isinstance(quote,dict)
            symbol = quote['symbol']
            if symbol.startswith(self.symbol):
                if symbol.endswith("AX"):
                    self.current_quote['asx'].append(quote)
                else:
                    self.current_quote['cxa'].append(quote)

                print " -------- "
                pprint(self.lastest)

        except Exception,e:
            log.exception(e)
    @property
    def lastest(self):
        """ """
        ret = {'asx': None,
               'cxa': None
               }
        if len(self.current_quote['asx']) == 1:
            ret['asx'] = self.current_quote['asx'][0]
        if len(self.current_quote['cxa']) ==1:
            ret['cxa'] = self.current_quote['cxa'][0]

        return ret

if __name__ == "__main__":
    """ main. """

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", dest="symbol", action="store")
    parser.add_argument("-e", dest="endpoint",action="store",default="tcp://localhost:30193")

    args = parser.parse_args()
    print args

    endpoint = args.endpoint
    print "endpoint: " , endpoint

    if args.symbol:
        listenr = Listener(endpoint,args.symbol)
    else:
        listener = Listener(endpoint,"CCL")

    try:
        while True:
            gevent.sleep(5)
    except KeyboardInterrupt:
        pass
