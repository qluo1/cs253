import os
cur_dir = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(cur_dir)
TMP_DIR = os.path.join(PROJ_ROOT,"tmp")


TIMEZONE = "Australia/Sydney"

#IVCOMSERVICE_HOST_REMOTE = "d153578-002.dc.gs.com"
IVCOMSERVICE_HOST_REMOTE = "d48965-004.dc.gs.com"
IVCOMSERVICE_HOST = "localhost"

########################################
### sybase db service.
#OM2DB_SERVICE_ENDPOINT = "tcp://%s:39010" % IVCOMSERVICE_HOST_REMOTE
OM2DB_SERVICE_ENDPOINT = "tcp://%s:62001" % IVCOMSERVICE_HOST_REMOTE

## 
SYMBOL_MANAGER_ENDPOINT = "tcp://%s:20195" % IVCOMSERVICE_HOST_REMOTE
##
MARKEDATA_SERVICE_ENDPOINT = "tcp://%s:20192" % IVCOMSERVICE_HOST_REMOTE
##
OM2RULE_SERVICE_ENDPOINT = "tcp://%s:49010" % IVCOMSERVICE_HOST_REMOTE

QFIX_ORDER_ENDPOINT = "ipc:///tmp/fix_order_request"
QFIX_PUBSUB_ENDPOINT = "ipc:///tmp/fix_er_sub"

QFIX_ORDER_API =""
## internal sync wait for RF ack.
RF_ACK_WAIT = 5

##  dss ack timeout 5 seconds
DSS_ACK_WAIT = 10
CANCEL_DELAY = 3
## timeout for order expected status
EXPECT_STATUS_WAIT = 10

## used for lookup dss exernalReferneces
EXTERNALOBJECTIDTYPE = 1 # 'FixOrderId'

HEARTBEAT_TIMEOUT = 20

## redis config for clientOrderId 
REDIS_HOST ="d127601-081"
REDIS_PORT = 6379
REDIS_DB = 0
## om2 mongodb 
MONGO_HOST_P = "qaeaucea-1.qa.om2.services.gs.com"
MONGO_HOST_S = "qaeaucea-2.qa.om2.services.gs.com"
MONGO_PORT = 6275
## using om2 secondary as main storage.
MONGO_CFG = (MONGO_HOST_P,MONGO_PORT)

## test case related cofig
from testCaseConfig import *

ETFS = ['IKO.AX',]

try:
    ## override config from local settings.
    from localcfg import *
except ImportError,e:
    pass
