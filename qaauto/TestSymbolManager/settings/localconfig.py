from common import *
import logging

HEARTBEAT_TIMEOUT = 60
########################################
##  export  symbolManager servie endpoint
SYMBOL_MANAGER_API_ENDPOINT = "tcp://*:20195"

VIKING_ENV="QAE"
VIKING_ACK_WAIT = 20
SYMBOL_BLACK_LIST = [
'AAC.AX', ## block security for size limit = $0
]

##################### service depencency #################
## service depency
## -- IvComService for VIKING
## -- MarketData for active symbol
## -- OM2DBService for symbol attrs
#########################################################
HOST = "d48965-004.dc.gs.com" ## OM2-P
#HOST = "localhost"

#HOST = "localhost"
## viking endpoint
VIKING_SUB_ENDPOINT = "tcp://%s:29010"  % HOST
VIKING_ORDER_ENDPOINT = "tcp://%s:29011" % HOST

##0RPC market data server endpoint
QUOTE_RPC_ENDPOINT = "tcp://%s:20192" % HOST
## zerorpc publishing endpoint
QUOTE_PUB_ENDPOINT = "tcp://%s:20193" % HOST

### OM2DBService for symbol attrs
#OM2DBSERVICE_RPC_ENDPOINT = "tcp://%s:39010" % HOST
OM2DBSERVICE_RPC_ENDPOINT = "tcp://%s:62001" % HOST

## redis
REDIS_HOST="d127601-081.dc.gs.com"
REDIS_PORT=6379
REDIS_DB=2

## python 2.7+
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'logfile': {
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR,"symbolManager.log"),
            'level': 'WARN',
            'when':     'midnight',
            'interval': 1,
            'backupCount': 0,
            'delay': True,
            'formatter': 'verbose',
        },
        'console':{
            'level': 'WARN',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['logfile','console',],
            'level': 'DEBUG',
            'propagate': True
        },

    }
}

