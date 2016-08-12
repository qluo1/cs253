""" setup fixture for GSET.

i.e. - AU Symbol service.
     - AU market depth/price service.

"""
import os
import pytest
import atexit

## setup local python path
import cfg
import zerorpc
import gevent

IVCOMSERVICE_HOST_REMOTE = "d48965-004.dc.gs.com"

########################################
### sybase db service.
OM2DB_SERVICE_ENDPOINT = "tcp://%s:39010" % IVCOMSERVICE_HOST_REMOTE
## 
SYMBOL_MANAGER_ENDPOINT = "tcp://%s:20195" % IVCOMSERVICE_HOST_REMOTE
##
MARKEDATA_SERVICE_ENDPOINT = "tcp://%s:20192" % IVCOMSERVICE_HOST_REMOTE
##
OM2RULE_SERVICE_ENDPOINT = "tcp://%s:49010" % IVCOMSERVICE_HOST_REMOTE

### remote rpc
symbol_manager = zerorpc.Client(SYMBOL_MANAGER_ENDPOINT,timeout=160,heartbeat=160)
### db service.
om2db_service = zerorpc.Client(OM2DB_SERVICE_ENDPOINT,heartbeat=30)
##  rule service
om2rule_service = zerorpc.Client(OM2RULE_SERVICE_ENDPOINT,heartbeat=30)

## position data
position_service = zerorpc.Client("tcp://localhost:21195")

OMA_API_URL = "ipc:///tmp/oma_graph_py"
## nvp/oma service
nvpService = zerorpc.Client(OMA_API_URL)

## cleanup at exit
atexit.register(symbol_manager.close)
atexit.register(om2db_service.close)
atexit.register(om2rule_service.close)
atexit.register(position_service.close)

## ignore ETF
BLACKLIST_SYMBOLS = ['IJP.AX','SYI.AX','IJH.AX','VEU.AX']
class SymbolDepthManager(object):
    """ wrapper of remote symbol_manager service. """
    def __init__(self,symbol = None):
        """ """
        self.pid_ = os.getpid()
        self.symbol_ = symbol

    def get_tradable_symbol(self,**kw):
        """ """
        if "state" not in kw:
            kw["state"] = "OPEN"
        assert kw["state"] == "OPEN"
        ## different pid will force refresh test symbol
        if 'pid' in kw:
            pid = kw.pop("pid")
        else:
            pid = self.pid_

        if self.symbol_:
            kw['symbol'] = self.symbol_

        kw['blacklist'] = BLACKLIST_SYMBOLS
        ## clear depth and get tradable symbol (symbol,quote_asx,quote_cha)
        res = symbol_manager.get_tradable_symbol(pid,**kw)
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0],res[1],res[2],attrs)

    def get_symbol_quote(self,symbol):
        return symbol_manager.get_symbol_quote(symbol)

    def get_test_symbol(self,**kw):
        """ """
        res = symbol_manager.get_test_symbol(self.pid_,**kw)
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0]['symbol'])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0]['symbol'], res[0],res[1],attrs)

    def get_pre_open_symbol(self):
        """ helper return open auction symbol."""
        res = symbol_manager.get_test_symbol(self.pid_,state="PRE_OPEN")
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0]['symbol'])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0]['symbol'], res[0],res[1],attrs)

    def get_pre_cspa_symbol(self):
        """ helper return close auction symbol."""
        res = symbol_manager.get_test_symbol(self.pid_,state="PRE_CSPA")
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0]['symbol'])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0]['symbol'],res[0],res[1],attrs)

    def get_symbol_attrs(self,symbol):
        """ """
        return om2db_service.query_symbol_attrs(symbol)


@pytest.fixture(scope="module")
def  position(request):
    """ has get_position method(starId) """

    class Dummy():
        def get_position(self,starId):
            """ """
            return "dummy"
    return Dummy()
    #return position_service


@pytest.fixture(scope="module")
def symbol_depth(request):
    """ """
    if hasattr(request.module,'symbol'):
        return SymbolDepthManager(request.module.symbol)
    return SymbolDepthManager()


@pytest.fixture(scope="module")
def nvp_service(request):
    """ """
    return nvpService
