""" find/calculate price step. """
import os
import random
import logging
## 
if 'SETTINGS_MODULE' not in os.environ:
    os.environ['SETTINGS_MODULE'] = 'settings.PPEAUCEA'

import cfg
## zerorpc
import zerorpc
import gevent

from conf import settings

logging.basicConfig(filename=os.path.join(cfg.LOG_DIR,"findPriceStep.log"),level=logging.INFO)

log = logging.getLogger("FindPriceStep")

##########################################
rule_server_ = zerorpc.Client()
rule_server_.connect(settings.OM2RULE_SERVICE_ENDPOINT)

om2db_service_ = zerorpc.Client()
om2db_service_.connect(settings.OM2DB_SERVICE_ENDPOINT)

def find_sizeLimit(symbol,**kw):
    """ """
    return rule_server_.get_sizeLimit(symbol,**kw)

def find_rules(quote,price,**kw):
    """ return calculated priceStep.

    price in max_buy, min_sell

    input:
        - order price
        - quote data with bid/ask/last

        - quote is a dict
            {u'ask': {u'ask': 27.0, u'askSize': 5000.0, u'npls': 1.0, u'numAsks': 1.0},
            u'bid': {u'bid': 48.29, u'bidSize': 156.0, u'npls': 1.0, u'numBids': 1.0},
            u'close': 29.38,
            u'high': 0,
            u'hstclsdate': u'3/11/2015',
            u'hstclsdateclose': 29.38,
            u'last': 29.38,
            u'match': 33.25,
            u'name': u'WOOLWORTHS FPO',
            u'open': 0,
            u'state': u'PRE_OPEN',
            u'status': u'STATE_OK',
            u'symbol': u'WOW.AX',
            u'timestamp': u'2015-03-23T09:24:09.715183',
            u'tradeDate': None,
            u'turnover': No

    1, locate price band based last
    2, if not last, using order price

    """
    ## for random symbols , bid/ask as list, for single symbol, bid/ask as dict
    bid= quote.bid[0]
    bidSize = quote.bid[1]

    ask = quote.ask[0]
    askSize = quote.ask[1]

    symbol = quote.symbol
    last = quote.last
    match = quote.match
    state = quote.state or 'OPEN'

    ordType = kw.get("orderType","limit")
    businessUnit = kw.get("businessUnit","DEFAULT")
    ret = {}

    ## om2 treate PRE_NR as CLOSE auction
    if state == "OPEN":
        rule_tag = "exchange-continuous-" + ordType
    elif state in ("PRE_OPEN",):
        rule_tag = "exchange-open-auction-" + ordType
    elif state in( "PRE_NR", "PRE_CSPA"):
        rule_tag = "exchange-close-auction-" + ordType
    else:
        raise ValueError("unknown rule_tags for current state: %s" % state)

    #import pdb;pdb.set_trace()
    ## lookup rule based on last, or based on price i.e. can be order price.
    if last > 0:
        rule = rule_server_.find_price_step(last,rule_tag,symbol=symbol,businessUnit=businessUnit)
    else:
        assert price and price > 0, "missing last and price not specified correctly"
        last = price
        rule = rule_server_.find_price_step(price,rule_tag,symbol=symbol,businessUnit=businessUnit)

    log.info("found rule: %s " % str(rule))

    assert 'price_overlap' in rule and 'price_last' in rule and 'price_step' in rule

    if state in ("PRE_OPEN","PRE_CSPA","PRE_NR"):
        assert 'per_last' in rule
        #if match > 0:
        #    band = data.find_rule_priceStep(match,state)

        ## generally, buy =
        max_buy = max(last+rule['price_last'],
                        min(bid+rule['price_step'],match+rule['price_overlap']))
        ## if missing match
        if not match:
            max_buy = max(last + rule['price_last'], bid + rule['price_step'])
        ## if missing bid and match
        if not bid:
            max_buy = last + rule['price_last']

        log.info("max_buy: %s, formular: max(last(%s)+rule['price_last'](%s), min(bid(%s)+rule['price_step'](%s),match(%s)+rule['price_overlap'](%s)))" %
                 (max_buy, last,rule['price_last'],bid,rule['price_last'],match,rule['price_overlap']))

        ##
        min_sell = min(last-rule['price_last'],
                        max(ask-rule['price_step'],match-rule['price_overlap']))

        #
        log.info("min_sell: %s, formular: min(last(%s)-rule[LAST_PRICE_STEP](%s), max(bid(%s)-rule[price_step](%s),match(%s)-rule[price_overlap](%s)))" %
                 (min_sell,last,rule['price_last'],ask,rule['price_step'],match,rule['price_overlap']))

        if not match:
            min_sell = min(last - rule['price_last'],ask - rule['price_step'])
        ## no ask and no match
        if not ask:
            min_sell = last - rule['price_last']

    else:
        #print "state not checked: %s" % state
        ## generally, max buy = min(ask+o, max(last+s,bid_s))
        max_buy = min(ask+rule['price_overlap'],
                        max(last+rule['price_last'],bid+rule['price_step']))

        ## if no ask and/or no bid, ignore ask
        if not ask:
            max_buy = max(last+rule['price_last'],bid+rule['price_step'])

        log.debug("max buy:%s,  min(ask(%s)+rule['price_overlap'](%s), max(last(%s)+rule['price_last'](%s),bid(%s)+rule['price_step'](%s))) " %
                  (max_buy,ask,rule['price_overlap'],last,rule['price_last'],bid,rule['price_step']))

        ### default min sell calculaiton
        ## min sell = max(bid-o , min(last-s, ask-s))
        min_sell = max(bid-rule['price_overlap'],
                        min(last-rule['price_last'],ask-rule['price_step']))

        ## missing ask but with bid, ignore ask
        if not ask and bid:
            min_sell = max(bid-rule['price_overlap'], last-rule['price_last'])

        ## missing bid, with ask, ignore bid
        if not bid and ask:
            min_sell = min(last-rule['price_last'],ask-rule['price_step'])

        ## missng both bid/ask, ignore both bid/ask
        if not bid and not ask:
            min_sell = last-rule['price_last']

        log.info("min sell:%s, max(bid(%s)-rule['price_overlap'](%s), min(last(%s)-rule['price_last'](%s),ask(%s)-rule['price_step'](%s))) " %
                  (min_sell,bid,rule['price_overlap'],last,rule['price_last'],ask,rule['price_step']))


    if 'per_last' in rule:
        per_last = rule['per_last']

        ret =  {
                'priceStep': {'max': float("%g" % max_buy),
                              'min': float("%g" % min_sell),
                              'state': state
                              },
                '%last' :  {'max': float("%g" % (last + last * per_last /100.0)),
                            'min': float("%g" % (last - last * per_last /100.0)),
                            'per': per_last,
                            },
                'rule': rule,
                'quote': {'bid': bid,'ask': ask,'last': last, 'match': match,
                          'state': state,'bidSize': bidSize,'askSize':askSize,
                          },
                'symbol': symbol,
                }

    else:
        ret =  {
                'priceStep': {'max': "%g" % max_buy,
                              'min': "%g" % min_sell,
                              'state': state
                              },
                'max': max_buy,
                'min': min_sell,
                'rule': rule,
                'quote': {'bid': bid,'ask': ask,'last': last,
                          'state': state, 'bidSize': bidSize,'askSize':askSize,
                          },
                'symbol': symbol,
                }

    ## workout auction max/min
    if '%last' in ret:
        ret['max'] = ret['priceStep']['max'] if ret['priceStep']['max'] < ret['%last']['max'] else ret['%last']['max']
        ret['min'] = ret['priceStep']['min'] if ret['priceStep']['min'] > ret['%last']['min'] else ret['%last']['min']

    ## remove rounding
    ret['max'] = float("%g" % ret['max'])
    ret['min'] = float("%g" % ret['min'])

    ## query sizeLimit
    ret.update(rule_server_.get_sizeLimit(symbol,businessUnit=businessUnit))
    return ret

if __name__ == "__main__":
    """ """
    import sys
    from pprint import pprint
    import argparse

    ## market data server
    client = zerorpc.Client()
    client.connect(settings.MARKEDATA_SERVICE_ENDPOINT)
    from collections import namedtuple
    MQuote = namedtuple("Quote","symbol,state,last,vwap,bid,ask,match,close")


    parser = argparse.ArgumentParser(description="parsing find price step.")
    parser.add_argument("-s",dest="symbol")
    parser.add_argument("-p",dest="price")
    parser.add_argument("-b",dest="business",default="DEFAULT")

    args = parser.parse_args()

    if not args.symbol:
        print parser.print_usage()
        exit(0)
    symbol = args.symbol

    data = client.get_quote(symbol)
    print data
    assert 'AX' in data and 'CHA' in data
    asx_data = data['AX']
    quote = MQuote(*asx_data)
    print quote

    price = None
    if args.price:
        price = float(args.price)
    else:
        if quote.last:
            price = quote.last
        else:
            attrs = om2db_service_.query_symbol_attrs(quote.symbol)
            close_price = float(attrs["CLOSEPRICE"])
            price = close_price


    pprint(find_rules(quote,price,businessUnit=args.business))

