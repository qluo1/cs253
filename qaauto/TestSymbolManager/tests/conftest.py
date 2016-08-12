import os
import sys

PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJ_ROOT,"scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)

LOG_DIR = os.path.join(PROJ_ROOT,"logs")
## setup local python path
os.environ['SETTINGS_MODULE']='settings.localconfig'
import cfg

import logging
logging.basicConfig(filename=os.path.join(LOG_DIR,"test_symbolManager.log"),
                    level=logging.INFO,
                    format='%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s')

