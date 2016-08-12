import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)
LIBS_DIR = os.path.join(PROJ_ROOT,"libs")
RDSDATA = os.path.join(PROJ_ROOT, "rdsdata")

if LIBS_DIR not in sys.path:
    sys.path.append(LIBS_DIR)

if PROJ_ROOT not in sys.path:
    sys.path.append(PROJ_ROOT)

## local project settings
os.environ["SETTINGS_MODULE"] = "settings.config"

## setup GNS python path
GNS_PTH =os.path.join(CUR_DIR,"gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            sys.path.append(line)



import ujson as json
