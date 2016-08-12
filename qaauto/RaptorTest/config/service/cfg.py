#local config
import os
import sys

PROJ_ROOT = os.environ['BASE_DIR']
## setup local lib
LIBS_DIR = os.path.join(PROJ_ROOT,"lib")
## 
CUR_DIR = os.path.dirname(os.path.abspath(__file__))

for PATH in (PROJ_ROOT,LIBS_DIR,CUR_DIR):
    if PATH not in sys.path:
        sys.path.append(PATH)

if "SETTINGS_MODULE" not in os.environ:
    raise EnvironmentError("SETTINGS_MODULE hasn't been specified")

from conf import settings
os.environ['TZ'] = settings.TIMEZONE
import time
time.tzset()

## setup GNS python path
GNS_PTH =os.path.join(PROJ_ROOT,"config/gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            assert os.path.exists(line)
            sys.path.append(line)


