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
    ## test symbols
    asx_symbols = ['ANZ.AX','NAB.AX','CBA.AX','ANZ.AX']
    chia_symbols = ['ANZ.CHA','NAB.CHA','CBA.CHA']

    return {'DF_ASX_QA': asx_symbols, 'DF_CXA_QA': chia_symbols}
    #return {'IDN_SELECT_PLUS': asx_symbols }, {'IDN_SELECT_PLUS': chia_symbols}

