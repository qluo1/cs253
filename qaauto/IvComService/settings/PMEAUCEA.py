import logging
from common import *

GSLOGCFG = os.path.join(CUR_DIR,"gslog.cfg")
GSLOGNAME = "PMEAUCEA"
IVPYCFG = os.path.join(CONFIG_DIR,"PMEAUCEA.py")


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
            'filename': os.path.join(LOG_DIR,"PME.log"),
            'level': logging.INFO,
            'when':     'D',
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

MSGDUMPER_LOGGING = {
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
            'filename': os.path.join(LOG_DIR,"messageDump_PME.log"),
            'level': logging.INFO,
            'when':     'D',
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



ORDER_API_URL = "tcp://0.0.0.0:29031"

### collect local publishing
PRIVATE_SUB_ENDPOINT = "ipc:///tmp/PMEAUCEA"

## forward to public/publish endpint.
PUBLIC_PUB_ENDPOINT = "tcp://0.0.0.0:29030"

PUB_ENDPOINT_MAP = {
    ## comment out will return ack, not using pub
    'engine-PMEAUCEA-requestResponse': PRIVATE_SUB_ENDPOINT,
    #'PMEAUCEA-Primary':                PRIVATE_SUB_ENDPOINT,
    ## transaction notification
    #'PMEAUCEA->replication':           PRIVATE_SUB_ENDPOINT,
    'PMEAUCEA->QAAUCE_Listener':       PRIVATE_SUB_ENDPOINT,
    'imageliveserver-PMEAUCEA':        PRIVATE_SUB_ENDPOINT,
}

