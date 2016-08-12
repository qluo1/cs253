### setup project python path
import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)
LIBS_PATH = os.path.join(PROJ_ROOT,"libs")

## setup GNS python path
GNS_PTH =os.path.join(CUR_DIR,"gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            sys.path.append(line)
## local python lib
if LIBS_PATH not in sys.path:
    sys.path.append(LIBS_PATH)

## required for MyMDTModule.so/C++ plugin
if PROJ_ROOT not in sys.path:
    sys.path.append(PROJ_ROOT)

try:
    import ujson as json
except ImportError:
    import json

from MyMDTModule import MyMDTListener,StringVector,setuplog

## local settings
if "SETTINGS_MODULE" not in os.environ:
    raise ValueError("env variable: SETTINGS_MODULE hasn't set")

from conf import settings

os.environ['TZ'] = settings.TIMEZONE
import time
time.tzset()


__all__ = [
        'json',
        'MyMDTListener',
        'StringVector',
        'setuplog',
    ]

### enable GNS python libs

