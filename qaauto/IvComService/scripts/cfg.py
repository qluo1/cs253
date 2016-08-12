#local config
import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)

CONFIG_DIR = os.path.join(PROJ_ROOT,"config")
LIBS_DIR = os.path.join(PROJ_ROOT,"libs")
## setup search path
for PATH in (CUR_DIR,CONFIG_DIR,LIBS_DIR,PROJ_ROOT):
    if PATH not in sys.path:
        sys.path.append(PATH)

if "SETTINGS_MODULE" not in os.environ:
    raise EnvironmentError("SETTINGS_MODULE hasn't been specified")

from conf import settings

os.environ['TZ'] = settings.TIMEZONE
import time
time.tzset()

from om2CompleteCatalog import om2CompleteCatalog ,om2CompleteCatalogEnums

from IvComPy import IvComPyManager,IvComPyClient,IvComPyDssClient, IvComPySvrDSClient,IvComPyImgLiveClient

try:
    import ujson as json
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/ujson-1.35/lib/python2.7/site-packages")
    import ujson as json

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

try:
    import pymongo
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/pymongo-2.9/lib/python2.7/site-packages")

### 
try:
    import redis
except ImportError:
    ############################################
    ## GSN redis is bit old not support iterator
    GNS_REDIS = "/gns/mw/lang/python/modules/2.7.2/redis-2.7.6/lib/python2.7/site-packages"
    if GNS_REDIS not in sys.path:
        sys.path.append(GNS_REDIS)
    import redis

try:
    import docopt
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/docopt-0.6.2/lib/python2.7/site-packages")

## redis db
#rdb = redis.Redis(host=settings.REDIS_HOST,
#                  port=settings.REDIS_PORT,
#                  db=settings.REDIS_DB)
#

#####################################################
## om2 mongo db need create user "dss_client"
import pymongo
mongo_client = pymongo.MongoClient("mongodb://dss_client:dss_client@%s:%s" % settings.MONGO_CFG)

## dynamically set dss db based on instance.
mongo_database = eval("mongo_client.%s" % os.environ['SETTINGS_MODULE'].split(".")[-1])
## dss collection
dss_db = mongo_database.dss
## image live collection
imagelive_db = mongo_database.imagelive


