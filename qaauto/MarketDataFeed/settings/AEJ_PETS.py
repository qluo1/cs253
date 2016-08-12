from common import *

TIMEZONE = "Australia/Melbourne"

ENV = "RMDS6/HONGKONG/LAB"
USER = "oma_gsetqa_hk_6744"

SERVICES = [
            #"AEJ_PETS_POS_QA",
            "ASIA_PETS_POS_DMA_QA"
            ]

###################################
##0RPC data server
API_ENDPOINT = "tcp://*:21195"
## zerorpc publishing endpoint
RPC_PUB_ENDPOINT = "tcp://*:21196"

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
            'filename': os.path.join(LOG_DIR,"PETS.log"),
            'level':    logging.DEBUG,
            'when':     'D',
            'interval': 1,
            'backupCount': 0,
            'delay':    True,
            'formatter': 'verbose',
        },
        'console':{
            'level': 'DEBUG',
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
