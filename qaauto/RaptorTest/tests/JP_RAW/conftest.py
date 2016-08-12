import pytest
import copy
import os
import logging
import logging.config
import config.service.cfg
from conf import settings

from tests.dc_util import DCMsgListener
from tests.JP_RAW.zcmd_util import Zcmd
from tests.JP_RAW.ahd_util import AHDMessageListener, AHDOrder, AHDMessageVerifier
from tests.csv_util import CSVExportHelper

dc_session = 'DC_RAPTOR'
ahd_session = 'VS0030'

@pytest.fixture(scope='session')
def dc(request):
    return DCMsgListener(dc_session)

@pytest.fixture(scope='session')
def zcmd(request):
    return Zcmd()

@pytest.fixture(scope='session')
def ahd(request):
    return AHDMessageListener()

@pytest.fixture(scope='module')
def csv(request):
    csv_file_name = settings.LOG_DIR + '/' + request.module.__name__ + '.csv'
    csv_helper = CSVExportHelper(csv_file_name)
    def fin():
        csv_helper.close()
    request.addfinalizer(fin)
    return csv_helper
    
@pytest.fixture(scope='module', autouse=True)
def setup_log(request):
    cfg = copy.deepcopy(settings.LOG_CFG)
    log_file_name = request.module.__name__ + '.log'
    cfg['handlers']['logfile']['filename'] = os.path.join(settings.LOG_DIR, log_file_name)
    cfg['handlers']['logfile']['mode'] = 'a'
    logging.config.dictConfig(cfg)

@pytest.fixture(autouse=True)
def print_testcase_name(request):
    log = logging.getLogger('TestAdmin')
    log.info('Start of test method: %s' % request.function.__name__)
    def fin():
        log.info('End of test method: %s' % request.function.__name__)
    request.addfinalizer(fin)
   
@pytest.fixture
def ahd_verifier(expect):
    return AHDMessageVerifier(expect)

@pytest.fixture
def ahd_service(request, ahd, dc, zcmd, csv, ahd_verifier, reporter):
    return AHDOrder(ahd_session, ahd_verifier, ahd, dc, csv, zcmd, reporter) 
    
