#!/bin/env python
import os
import sys
from pprint import pprint
import logging


## loookup OM2 ENV
if 'ENV' not in os.environ:
    print "envrionment variable ENV not set?: PPE/QAE/PME"
    exit(0)
## check which environment
if os.environ['ENV'] in ('QAE','PPE','PME'):
    os.environ["SETTINGS_MODULE"] = "config.settings"
else:
    print "unknown environment variable: %s" % os.environ['ENV']
    exit(0)


import localconf

from docopt import docopt
#from gsatest.om2.TestSymbols import TestSymbols
#from gsatest.om2.db.gssymbol import GSSymbolAttr
#symbolattr = GSSymbolAttr()

logging.basicConfig(filename="query_symbol.log",
                    level=logging.INFO,
                    format='%(asctime)-15s %(levelname)s %(name)-8s %(lineno)s %(message)s'
                    )


if __name__ == "__main__":
    """ test main. """
    doc = """Usage:
        query_symbol.py quote <symbol>
        query_symbol.py random (--open|--close|--auction) [ --price=<price> ] [ --num=<num> ] [--dep] [--phase=<phase>] [--ext=<ext>]
        query_symbol.py rule <symbol> [ --verbose ]

        options:

    """
    opt = docopt(doc,sys.argv[1:])
    #print opt

    util = TestSymbols()
    if opt['quote']:
        print "query: %s" % opt['<symbol>'].upper()
        pprint(util.test_instrument(symbol=opt['<symbol>'].upper()))
        #pprint(util.test_instrument(num=5))
    num = opt['--num'] or 3
    if opt['random']:
        if opt['--open']:
            if opt['--price']:
                pprint(util.random_open_symbols(price=opt['--price'],dep=opt.get('--dep',False),ext=opt.get('--ext')))
            else:
                pprint(util.random_open_symbols(dep=opt.get('--dep',False),ext=opt.get('--ext')))
        if opt['--close']:
            pprint(util.random_closed_symbols(num=num))
        if opt['--auction']:
            ## set phase ALL/OPEN/CLOSE
            phase = "ALL"
            if '--phase' in opt:
                phase = opt['--phase']

            if opt['--price']:
                pprint(util.random_auction_symbols(price=opt['--price'],num=num,phase=phase))
            else:
                pprint(util.random_auction_symbols(num=num,phase=phase))

    if opt['rule']:
        quote = util.test_instrument(symbol=opt['<symbol>'])
        rules = find_rules(quote,quote['last'])

        rules['attrs'] = symbolattr.query_symbol(rules['symbol'])
        if opt['--verbose']:
            pprint(rules)
        else:
            rules.pop("rules_%last")
            rules.pop("rules_priceSteps")
            pprint(rules)


