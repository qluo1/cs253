#local config
import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)

## setup local lib
LIBS_DIR = os.path.join(PROJ_ROOT,"libs")

for PATH in (CUR_DIR, LIBS_DIR, PROJ_ROOT):
    if PATH not in sys.path:
        sys.path.append(PATH)

if "SETTINGS_MODULE" not in os.environ:
    raise EnvironmentError("SETTINGS_MODULE hasn't been specified")

from conf import settings
os.environ['TZ'] = settings.TIMEZONE
import time
time.tzset()

## setup GNS python path
GNS_PTH =os.path.join(CUR_DIR,"gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            assert os.path.exists(line)
            sys.path.append(line)


