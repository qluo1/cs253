## setup pytest environment
import os
import sys
from datetime import datetime, date
import pytest
from xml.sax import saxutils

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)
## test utils
COMMON_DIR = os.path.join(PROJ_ROOT,"scripts")
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

LOG_DIR = os.path.join(PROJ_ROOT,"logs")
REPORT_DIR = os.path.join(PROJ_ROOT,"reports")

import logging
logging.basicConfig(filename=os.path.join(LOG_DIR,"test_run_%s.log" % date.today().isoformat()),
                    level=logging.INFO,
                    format="%(asctime)-15s %(levelname)s %(process)s %(threadName)s %(name)-8s %(lineno)s %(message)s"
                    )

## setup local python path
import cfg
from conf import settings
import zerorpc
import atexit

### remote rpc
symbol_manager = zerorpc.Client(settings.SYMBOL_MANAGER_ENDPOINT,timeout=180,heartbeat=180)
### db service.
om2db_service = zerorpc.Client(settings.OM2DB_SERVICE_ENDPOINT,heartbeat=30)
##  rule service
om2rule_service = zerorpc.Client(settings.OM2RULE_SERVICE_ENDPOINT,heartbeat=30)
## cleanup at exit
atexit.register(symbol_manager.close)
atexit.register(om2db_service.close)
atexit.register(om2rule_service.close)


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

        kw['blacklist'] = settings.BLACKLIST_SYMBOLS
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
        if self.symbol_:
            quote = symbol_manager.get_symbol_quote(self.symbol_)
            attrs = om2db_service.query_symbol_attrs(self.symbol_)
            return (self.symbol_,quote[0],quote[1],attrs)

        res = symbol_manager.get_test_symbol(self.pid_,**kw)
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0]['symbol'])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0]['symbol'], res[0],res[1],attrs)

    def get_pre_open_symbol(self,**kw):
        """ helper return open auction symbol."""
        kw['state'] = "PRE_OPEN"
        res = symbol_manager.get_test_symbol(self.pid_,**kw)
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0]['symbol'])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0]['symbol'], res[0],res[1],attrs)

    def get_pre_cspa_symbol(self,**kw):
        """ helper return close auction symbol."""
        kw['state'] = "PRE_CSPA"
        res = symbol_manager.get_test_symbol(self.pid_,**kw)
        ## enrich symbol attrs.
        attrs = om2db_service.query_symbol_attrs(res[0]['symbol'])
        ## return (symbol,quote_asx,quote_cha,attrs)
        return (res[0]['symbol'],res[0],res[1],attrs)

    def get_symbol_attrs(self,symbol):
        """ """
        return om2db_service.query_symbol_attrs(symbol)

@pytest.fixture(scope="module")
def symbol_depth(request):
    """ """
    if hasattr(request.module,'symbol'):
        return SymbolDepthManager(request.module.symbol)
    return SymbolDepthManager()

## customised plugin
pytest_plugins = ["rerun_failed_test",
                  "report.plugin",
                  "xdist.plugin"
                 ]


###############################################
## test generator for class based test cases
##
###############################################
def pytest_generate_tests(metafunc):
    """ test generator for class based test scenarios.

    generate test cases based on scenarios configured inside test class

    scenarios is a list of dict, key must match test function parameters.

    """
    if metafunc.cls and hasattr(metafunc.cls,'scenarios'):
        #
        argnames = []
        argvalues = []
        for scenario in metafunc.cls.scenarios:
            argnames = scenario.keys()
            argvalues.append([scenario[name] for name in argnames])

        # import pytest;pytest.set_trace()
        if argnames and argvalues:
            metafunc.parametrize(argnames,argvalues,scope='class')
        else:
            pytest.skip("skip test")

###############################################
## html test reporter plugin
##
###############################################


## help func
def timeStamped(fname, fmt='{fname}_%Y-%m-%d-%H-%M-%S'):
    return datetime.now().strftime(fmt).format(fname=fname)
def get_current_om_version():
    """ helper """
    cur_setting = os.environ['SETTINGS_MODULE'].split(".")[-1]

    res = om2rule_service.get_om2_version()
    assert res
    assert 'QAE' in res
    assert 'PPE' in res
    assert 'PME' in res
    #import pdb;pdb.set_trace()

    for k,v in res.iteritems():
        if cur_setting.startswith(k):
            ## train deploy
            if v.startswith("/home/eqtdata/install"):
                items = v.split("/")
                if items[8] == "omengineBin":
                    assert items[7] == "hk"
                    assert items[-1] == "omengine"
                    return items[9]
            else:
                ## anything else, could be local deployment
                return v

## test report setting
def pytest_cmdline_preparse(config,args):
    """ modify pytests args with htmlreport """
    ## local default
    REPORT_TITLE = "Target OM2 Release: %s" % get_current_om_version()
    REPORT_DESC = "test report generated for IvComPy testsuites. "
    REPORT_APP = "IvComPy testsuites"

    plugin = config.pluginmanager.getplugin("report.plugin")
    if plugin != -1:
        test_script = args[0]
        try:
            test_script_name = test_script.split("/")[-1].split(".")[0]
        except Exception:
            test_script_name=""


        has_htmlreport = True if len([i for i in args if i.startswith("--htmlreport")] ) > 0 else False
        if not has_htmlreport:
            ## default fname
            fname = os.path.join(REPORT_DIR,timeStamped('%s_%s_pytest_report' % (get_current_om_version(),test_script_name))) + '.html'
            args.append("--htmlreport=%s" % fname)
        args.append("--htmlreporttitle=%s" % REPORT_TITLE)
        args.append("--htmlreportdesc=%s" % saxutils.escape(REPORT_DESC))
        args.append("--htmlreportapp=%s" % REPORT_APP)

