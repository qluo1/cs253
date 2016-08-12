import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)
LIBS_DIR = os.path.join(PROJ_ROOT,"libs")

if PROJ_ROOT not in sys.path:
    sys.path.append(PROJ_ROOT)

if LIBS_DIR not in sys.path:
    sys.path.append(LIBS_DIR)

if "SETTINGS_MODULE" not in os.environ:
    os.environ["SETTINGS_MODULE"] = "settings.localconfig"

## project settings.
from conf import settings


