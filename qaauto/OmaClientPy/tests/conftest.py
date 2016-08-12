## setup python path
import os
import sys
import pytest

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CUR_DIR)
SCRIPT_DIR = os.path.join(PROJ_DIR,"scripts")
LOG_DIR = os.path.join(PROJ_DIR,"logs")

if PROJ_DIR not in sys.path:
    sys.path.append(PROJ_DIR)

if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

## setup python path
import localcfg
from conf import settings


from datetime import date
import logging
logging.basicConfig(filename=os.path.join(LOG_DIR,"unittest_%s.log" % date.today()),
                    level =logging.DEBUG,
                    format = "%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s")
