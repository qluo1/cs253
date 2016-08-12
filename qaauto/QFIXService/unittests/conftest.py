## setup python path
import os
import sys
import pytest

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CUR_DIR)
SCRIPT_DIR = os.path.join(PROJ_DIR,"scripts")
LOG_DIR = os.path.join(PROJ_DIR,"logs")
TEST_DIR = os.path.join(PROJ_DIR,"tests")

## 
CFG_DIR = os.path.join(PROJ_DIR,"config")

if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

##apolloSimulator test cases
if CFG_DIR not in sys.path:
    sys.path.append(CFG_DIR)


@pytest.fixture()
def apollo_path():
    return CFG_DIR

os.environ['SETTINGS_MODULE'] = "settings.AU_Test"

## setup python path
import cfg
from conf import settings


from datetime import date
import logging
logging.basicConfig(filename=os.path.join(LOG_DIR,"unittest_%s.log" % date.today()),
                    level =logging.INFO,
                    format = "%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s")
