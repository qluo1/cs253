import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)

CONFIG_DIR = os.path.join(PROJ_ROOT,"config")
LIBS_DIR = os.path.join(PROJ_ROOT,"libs")
SCRIPT_DIR = os.path.join(PROJ_ROOT,"scripts")
## setup search path
for PATH in (SCRIPT_DIR,CONFIG_DIR,LIBS_DIR,PROJ_ROOT):
    if PATH not in sys.path:
        sys.path.append(PATH)

if "SETTINGS_MODULE" not in os.environ:
    raise EnvironmentError("SETTING_MODULE hasn't been specified")

import logging

LOG_CFG = {
        'filename': os.path.join(PROJ_ROOT,"logs","test.log" ),
        'level': logging.DEBUG,
        'format': '%(asctime)-15s %(levelname)s %(process)d %(threadName)s %(name)-8s %(lineno)s %(message)s',
        }

logging.basicConfig(**LOG_CFG)

