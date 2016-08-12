import os

TIMEZONE = "Australia/Sydney"

## server-datastream enqueue sequence Id depend on redis.
## running on luosam@gs.com dev sandbox
REDIS_HOST = "d127601-081.dc.gs.com"
REDIS_PORT = 6379
REDIS_DB = 3


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(CUR_DIR)
LOG_DIR = os.path.join(PROJ_ROOT,"logs")
TMP_DIR = os.path.join(PROJ_ROOT,"tmp")

CONFIG_DIR  = os.path.join(PROJ_ROOT,"config")


## om2 mongodb 

MONGO_HOST_P = "qaeaucea-1.qa.om2.services.gs.com"
MONGO_HOST_S = "qaeaucea-2.qa.om2.services.gs.com"
MONGO_PORT = 6275
## using om2 secondary as main storage.
MONGO_CFG = (MONGO_HOST_P,MONGO_PORT)

## rf request/response queue timeout 
RF_ACK_WAIT = 4
