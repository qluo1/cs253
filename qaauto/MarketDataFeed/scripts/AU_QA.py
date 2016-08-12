""" module for loading subscribe symbols for AU QA.

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
    asx_symbols = db_service.list_asx_symbols()
    chia_symbols = db_service.list_chia_symbols()
    log.info("asx symbols: %s" % len(asx_symbols))
    log.info("cxa symbols: %s" % len(chia_symbols))
    assert len(asx_symbols) > 0
    assert len(chia_symbols) > 0
    ##subscribe full depth
    asx_symbols = asx_symbols + [i +"d" for i in asx_symbols]
    chia_symbols = chia_symbols + [i +"d" for i in chia_symbols]

    ## test symbols
    #asx_symbols = ['ANZ.AX','NAB.AX','CBA.AX']
    #chia_symbols = ['ANZ.CHA','NAB.CHA','CBA.CHA']

    return {'DF_ASX_QA': asx_symbols, 'DF_CXA_QA': chia_symbols}
    #return {'IDN_SELECT_PLUS': asx_symbols }, {'IDN_SELECT_PLUS': chia_symbols}

