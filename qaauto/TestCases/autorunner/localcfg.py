## all external dependency
import os
import sys

## project folder reference
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CUR_DIR)
LIB_DIR = os.path.join(PROJ_DIR,"libs")
LOG_DIR = os.path.join(PROJ_DIR,"logs")
OM2_TEST_DIR = os.path.join(PROJ_DIR,"tests","om2")

## test runtime / result folder
LOCAL_TMP = os.path.join(CUR_DIR,"runtime")
LOCAL_RESULT = os.path.join(CUR_DIR,"results")

## setup GNS python path
GNS_PTH =os.path.join(CUR_DIR,"gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            sys.path.append(line)
## local shared libs
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

from plumbum import local, BG
## local pytest command
pytest = local[os.path.join(PROJ_DIR,"bin","run_pytest.bash")]


IVCOMSERVICE_HOST_REMOTE = "d48965-004.dc.gs.com"
########################################
OM2RULE_SERVICE_ENDPOINT = "tcp://%s:49010" % IVCOMSERVICE_HOST_REMOTE

#### #######################
## pytest params
DEFAULT_RERUNS=2
DEFAULT_MAXFAIL=5

## num of thread for execute test cases.
MAX_EXECUTOR=3

OM2_NO_XDIST_TESTS = (
    'order_rule_new.py'
)

OM2_EXCLUDE_TESTS = [

]
OM2_PME_EXCLUDE_TESTS = [

    'order_regdata_priority.py',
    'order_rule_new.py',
    'test_autorunner.py',
    'order_si_bpmv.py',

] + OM2_EXCLUDE_TESTS

OM2_PPE_EXCLUDE_TESTS = [

    'order_regdata_priority.py',
    'order_rule_new.py',
    'test_autorunner.py',
    'order_si_bpmv.py',

] + OM2_EXCLUDE_TESTS

AUTORUNNER_SERVICE_ENDPOINT = "ipc:///tmp/autorunner.sock"

import logging
## python 2.7+
LOG_CFG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'logfile': {
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR,"autorunner.log"),
            'level': 'DEBUG',
            'when':     'D',
            'interval': 1,
            'backupCount': 0,
            'delay': True,
            'formatter': 'verbose',
        },
        'console':{
            'level': 'WARN',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['logfile','console',],
            'level': 'DEBUG',
            'propagate': True

        },

    }

}
