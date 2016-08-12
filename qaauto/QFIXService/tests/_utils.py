from datetime import datetime
import cfg
import gevent

def active_wait(predicate,**kw):
    """ """
    assert callable(predicate)
    timeout = kw.get("timeout",5)
    raise_timeout = kw.get("raise_timeout",False)

    start = datetime.now()
    while True:
        if predicate():
            break
        else:
            now = datetime.now()
            if (now - start).total_seconds() < timeout:
                gevent.sleep(0.01)
            else:
                if raise_timeout:
                    raise TimeoutError("timeout: %d for %s" % (timeout,predicate()))
                return predicate()

    return True


import importlib

def import_proc(name):
    """ import processor based on string at runtime."""
    components = name.split('.')
    mod = importlib.import_module(".".join(components[:-1]))
    mod = getattr(mod, components[-1])
    return mod


from helper import *


def get_passive_price(side,quote):
    """ return passive price.

    workout passive price based on side, test_instrument.

    input:
        - quote, current quote snapshot
        - side order side



    """
    assert 'bid' in quote and 'ask' in quote and 'last' in quote

    bid,ask,last = quote['bid']['bid'],quote['ask']['ask'],quote['last']

    ## check price not breach priceStep
    if side == "Buy":
        # bid isn't too far from last
        if bid > 0 and bid < last  and last/bid-1 < 0.03 :
            price = bid
        else:
            price = last - tickSize(last,5)
            if price < 0:
                price = 0.001

    else:
        # ask isn't too far from last 3% or 3 tick
        if ask > 0 and ask > last and ask/last -1 < 0.03:
            price = ask
        else:
            price = last + tickSize(last,5)

    ##remove off-tick price if any
    return round_price(price,side=side)

