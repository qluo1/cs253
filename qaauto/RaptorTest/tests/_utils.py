from datetime import datetime
import config.service.cfg
from conf import settings
import gevent
import copy
import logging.config
import os

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

def verify_fix_message(received_msg, expected_msg):
    assert type(received_msg) == dict
    assert type(expected_msg) == dict
    for field in expected_msg:
        assert field in received_msg
        assert expected_msg[field] == received_msg[field]

def clean_up(zcmd = None, fix_listener = None, dc_listener = None):
    assert zcmd is not None

    ## Cancel all outstanding orders in raptor
    zcmd.cancel_open_orders()
    gevent.sleep(1)

    ## Flush listener cache for fix line and dropcopy line
    if fix_listener is not None:
        fix_listener.flush_cache()
    if dc_listener is not None:
        dc_listener.flush_cache()

def ahd_price(price):
    if type(price) == str:
        return price
    if type(price) == int:
        return ('%9d0000' % (price))
    else:
        return ('%13d' % (price * 10000))

def ahd_qty(qty):
    if type(qty) == int:
        return ('%13d' % (qty))
    else:
         return ('%13s' % (qty))

def verify_ahd_message(received_msg, expected_msg):
    assert type(expected_msg) == dict
    for field in expected_msg:
        if field in ['Price']:
            assert received_msg.getfieldval(field) == ahd_price(expected_msg[field])
            continue
        if field in ['Qty', 'PartExecQty']:
            assert received_msg.getfieldval(field) == ahd_qty(expected_msg[field])
            continue
        assert received_msg.getfieldval(field) == expected_msg[field]

def setup_logs(module_name):
    cfg = copy.deepcopy(settings.LOG_CFG)
    cfg['handlers']['logfile']['filename'] = os.path.join(settings.LOG_DIR, module_name  + '.log')
    logging.config.dictConfig(cfg)
