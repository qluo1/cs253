from collections import namedtuple
MQuote = namedtuple("Quote","symbol,state,last,vwap,bid,ask,match,close")
## bid/ask with large qty of orders.
SIZELIMIT = 100000

import cfg
from conf import settings
import zerorpc
import gevent
## setup local env too.
from FindPriceStep import find_rules
##########################################
mdt_service = zerorpc.Client(heartbeat=30,timeout=30)
mdt_service.connect(settings.MARKEDATA_SERVICE_ENDPOINT)

om2db_service =  zerorpc.Client()
om2db_service.connect(settings.OM2DB_SERVICE_ENDPOINT)

class RandomSymbol(object):
    """ """
    ## generate random test symbols
    def _gen_test_symbols(self):
        """ generator: return all test quotes."""

        all_symbols = mdt_service.list_symbols()
        asx_symbols = [s for s in all_symbols if s[0].endswith("AX")]
        cha_symbols = [s for s in all_symbols if s[0].endswith("CHA")]

        for item in asx_symbols:
           gevent.sleep(0.01)
           quote = MQuote(*item)
           try:
               attrs = om2db_service.query_symbol_attrs(quote.symbol)
           except Exception,e:
               log.error("can't find gs symbol attrs: %s" % quote.symbol)
               continue
           keys = quote.symbol.split(".")
           #print keys
           cxa_q = [s for s in cha_symbols if s[0] == keys[0] + ".CHA"]
           if len(cxa_q) == 0: continue
           cxa_quote = MQuote(*cxa_q[0])
           ## CHIA is not suspended
           if cxa_quote.state == None:
               if quote.state == "OPEN" and \
                  quote.bid[0] * quote.bid[1] < SIZELIMIT and \
                  quote.ask[0] * quote.ask[1] < SIZELIMIT:
                    yield (quote, cxa_quote,attrs)
               else:
                    yield (quote, cxa_quote,attrs)
    def _gen_open_symbols(self):
        """ """
        for quote,cxa_quote,attrs in self._gen_test_symbols():
            if quote.state == "OPEN":
                yield (quote,cxa_quote,attrs)

    def _gen_open_symbols_with_last(self):
        """ """
        for quote,cxa_quote,attrs in self._gen_test_symbols():
            if quote.state == "OPEN" and quote.last:
                yield (quote,cxa_quote,attrs)

    def _gen_auction_open_symbols(self):
        """ """
        for quote,cxa_quote,attrs in self._gen_test_symbols():
            if quote.state in ('PRE_OPEN',):
                if quote.bid[0] == quote.ask[0] == quote.last == 0:
                    continue
                yield (quote,cxa_quote,attrs)

    def _gen_auction_close_symbols(self):
        """ """
        for quote,cxa_quote,attrs in self._gen_test_symbols():
            if quote.state in ('PRE_CSPA','PRE_NR'):
                if quote.bid[0] == quote.ask[0] == quote.last == 0:
                    continue
                yield (quote, cxa_quote,attrs)

    def _gen_adjust_symbols(self):
        """ """
        for quote,cxa_quote,attrs in self._gen_test_symbols():
            if quote.state == 'ADJUST':
                yield (quote, cxa_quote,attrs)

    def _gen_closed_symbols(self):
        for quote,cxa_quote,attrs in self._gen_test_symbols():
            if quote.state not in ('OPEN','PRE_OPEN','PRE_NR', 'PRE_CSPA','ADJUST'):
                yield (quote, cxa_quote,attrs)

    def _gen_open_symbol_with_depth(self):
        """ return symbol with depth: i.e. bid/ask"""
        for quote, cxa_quote,attrs in self._gen_open_symbols():
            if quote.bid[0] and quote.ask[0]:
                yield (quote,cxa_quote,attrs)

    def _gen_open_symbol_with_depth_and_last(self):
        """ return symbol with depth: i.e. bid/ask"""
        for quote, cxa_quote,attrs in self._gen_open_symbols():
            if quote.bid[0] and quote.ask[0] and quote.last:
                yield (quote,cxa_quote,attrs)

    def _gen_open_symbol_without_depth(self):
        """ return symbol without depth: i.e. bid/ask"""
        for quote, cxa_quote,attrs in self._gen_open_symbols():
            if quote.bid[0] ==0  and quote.ask[0] == 0:
                yield (quote,cxa_quote,attrs)

    def _gen_open_symbol_with_last_without_depth(self):
        """ return symbol without depth, but with last"""
        for quote, cxa_quote,attrs in self._gen_open_symbols():
            if quote.bid[0] ==0  and quote.ask[0] == 0 and quote.last:
                yield (quote,cxa_quote,attrs)

    def _random_symbols(self,**kw):
        """ """
        size = kw.get("size",5)
        state = kw.get("state","OPEN")
        ## price range
        less = kw.get("less",999)
        great= kw.get("great",0.10)
        ## filter on less/great/state
        if state.upper() == "OPEN":
            candidate = [s for s in self._gen_open_symbols() if s[0].last < less and s[0].last > great]
        elif state.upper() == "PRE_OPEN":
            candidate = [s for s in self._gen_auction_open_symbols() if s[0].last < less and s[0].last > great]
        elif state.upper() == "PRE_CLOSE":
            candidate = [s for s in self._gen_auction_close_symbols() if s[0].last < less and s[0].last > great]
        elif state.upper() == "ADJUST":
            candidate = [s for s in self._gen_adjust_symbols()]
        else:
            candidate = [s for s in self._gen_closed_symbols()]

        return random.choice(candidate)

    def _get_quote(self,symbol):
        """ """
        keys = symbol.split(".")
        assert len(keys) == 2
        quotes = mdt_service.get_quote(keys[0])
        return (MQuote(*quotes['AX']),MQuote(*quotes['CHA']))

    def _find_rule(self,quote,**kw):
        """ """
        last = quote.last
        state = quote.state or "OPEN"
        price = kw.get("price",last)
        ordType = kw.get("orderType","limit")
        symbol = kw.get("symbol")
        businessUnit = kw.get("businessUnit","DEFAULT")

        assert symbol.endswith("AX")
        if state in ("OPEN","PRE_OPEN","PRE_NR","PRE_CSPA"):
            rule = find_rules(quote,price,orderType=ordType,businessUnit=businessUnit)
        else:
            rule = {}
        return rule


if __name__ == "__main__":
    """ """

