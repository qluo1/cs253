## setup local config
import os
import sys
try:
    import ujson as json
except ImportError:
    import json

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)

LIBS_DIR = os.path.join(PROJ_ROOT,"libs")
## setup search path
for PATH in (CUR_DIR,LIBS_DIR,PROJ_ROOT):
    if PATH not in sys.path:
        sys.path.append(PATH)

if "SETTINGS_MODULE" not in os.environ:
    os.environ["SETTINGS_MODULE"] = "settings.localconfig"

from conf import settings

os.environ['TZ'] = settings.TIMEZONE
import time
time.tzset()

### enable GNS python libs
try:
    import gevent
except ImportError:
    GNS_GEVENTS =["/gns/mw/lang/python/modules/2.7.2/gevent-1.0.2/lib/python2.7/site-packages",
                  "/gns/mw/lang/python/modules/2.7.2/greenlet-0.4.7/lib/python2.7/site-packages",
                  ]
    for lib in GNS_GEVENTS:
        if lib not in sys.path:
            sys.path.append(lib)

try:
    import zmq
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/pyzmq-14.5.0/lib/python2.7/site-packages")

try:
    import msgpack
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/msgpack-python-0.4.6/lib/python2.7/site-packages")

