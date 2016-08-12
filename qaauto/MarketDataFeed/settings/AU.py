from common import *

TIMEZONE = "Australia/Melbourne"

ENV = "RMDS6/SYDNEY/LAB"
USER = "oma_gsetqa_hk_6744"

SERVICES = ["IDN_SELECT_PLUS"]


##  publish for market data feed in normal 0MQ
PUB_QUOTE_ENDPOINT = "tcp://*:20990"
###################################
##0RPC data server
API_ENDPOINT = "tcp://*:20992"
## zerorpc publishing endpoint
RPC_PUB_ENDPOINT = "tcp://*:20993"

# random symbol ignore list
## AAX.AX configured as block security
IGNORE_SYMBOLS = ['ARP.AX',
                  'FFF.AX',
                  'EWC.AX',
                  ## block security
                  'AAX.AX',
                  ]
SYMBOL_MODULE = "AU_LIVE"

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
            'filename': os.path.join(LOG_DIR,"Live_MarketData.log"),
            'level':    'INFO',
            'when':     'midnight',
            'interval': 1,
            'backupCount': 0,
            'delay':    True,
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
            'level': logging.DEBUG,
            'propagate': True

        },

    }

}
