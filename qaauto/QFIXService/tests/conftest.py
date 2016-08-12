## setup python path
import os
import sys
import pytest

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CUR_DIR)
SCRIPT_DIR = os.path.join(PROJ_DIR,"scripts")
LOG_DIR = os.path.join(PROJ_DIR,"logs")

## 
CFG_DIR = os.path.join(PROJ_DIR,"config")

if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

assert 'SETTINGS_MODULE' in os.environ
#os.environ['SETTINGS_MODULE'] = "settings.AU_Test"

pytest_plugins = ['report.plugin']

from datetime import date
import logging
logging.basicConfig(filename=os.path.join(LOG_DIR,"tests_%s.log" % date.today()),
                    level =logging.INFO,
                    format = "%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s")


from fetchMarketData import query_symbol_quote

@pytest.fixture(scope="module")
def fetch_market_data(request):
    """ return query symbol funciton."""
    return query_symbol_quote

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


