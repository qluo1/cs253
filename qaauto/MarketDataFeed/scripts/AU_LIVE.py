""" module for loading subscribe symbols for AU LIVE.

"get_subscribe_symbols" WILL be called by marktetQuoteService.

which return dict with {service_name: list of sybols for the service name}

"""
import cfg
import zerorpc
import gevent
import logging
## 
from conf import settings

log = logging.getLogger(__name__)

def get_subscribe_symbols():
    """ helper query prime for au symbols. """
    log.info("query db service : %s" % settings.OM2DBSERVICE_URL)
    db_service = zerorpc.Client(settings.OM2DBSERVICE_URL,heartbeat=30)
    asx_symbols = db_service.list_asx_stocks()
    chia_symbols = db_service.list_chia_symbols()
    log.info("asx symbols: %s" % len(asx_symbols))
    log.info("cxa symbols: %s" % len(chia_symbols))
    assert len(asx_symbols) > 0
    assert len(chia_symbols) > 0
    ###################################
    ##subscribe full depth service.
    ##'IDN_SELECT_PLUS' no full depth
    return {'IDN_SELECT_PLUS': asx_symbols + chia_symbols}

