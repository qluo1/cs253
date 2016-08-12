from common import *

TIMEZONE = "Australia/Melbourne"

ENV = "RMDS6/SYDNEY/LAB"
USER = "omaqa"
SERVICES = ["DF_NSE_QA", "DF_BSE_QA"]

## random internal socket publish MDT raw data
import random
INTERNAL_PUB_ENDPOINT = "ipc:///tmp/MarketDataFeed_{0}.sock".format(str(random.random())[2:])

##  publish for market data feed in normal 0MQ
PUB_QUOTE_ENDPOINT = "tcp://*:20290"
###################################
##0RPC data server
API_ENDPOINT = "tcp://*:20292"
## zerorpc publishing endpoint
RPC_PUB_ENDPOINT = "tcp://*:20293"

# random symbol ignore list
## AAX.AX configured as block security
IGNORE_SYMBOLS = [ ]

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
            'class':    'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR,"INDA_MarketData.log"),
            'level':    'DEBUG',
            'when':     'D',
            'interval': 1,
            'backupCount': 0,
            'delay':    True,
            'formatter': 'verbose',
        },
        'console':{
            'level': logging.WARN,
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['logfile','console',],
            'level': logging.DEBUG,
            'propagate': True

        },

    }

}

try:

    from local import *
except ImportError:
    pass
