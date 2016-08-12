## setup pytest environment
import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)
## test utils
COMMON_DIR = os.path.join(PROJ_ROOT,"scripts")
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

LOG_DIR = os.path.join(PROJ_ROOT,"logs")

## setup local python path
import cfg

from conf import settings
import zerorpc

import logging
## customised plugin
pytest_plugins = ["report.plugin"]


logging.basicConfig(filename=os.path.join(LOG_DIR,"unittest.log"),
                    level=logging.INFO,
                    format="%(asctime)-15s %(levelname)s %(process)s %(threadName)s %(name)-8s %(lineno)s %(message)s"
                    )



