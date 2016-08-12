import logging
from common import *

GSLOGCFG = os.path.join(CUR_DIR,"gslog.cfg")
GSLOGNAME = "PPEAUCEA"
IVPYCFG = os.path.join(CONFIG_DIR,"PPEAUCEA.py")


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
            'filename': os.path.join(LOG_DIR,"PPE.log"),
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
            'filename': os.path.join(LOG_DIR,"messageDump_PPE.log"),
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



ORDER_API_URL = "tcp://0.0.0.0:29021"

### collect local publishing
PRIVATE_SUB_ENDPOINT = "ipc:///tmp/PPEAUCEA"

## forward to public/publish endpint.
PUBLIC_PUB_ENDPOINT = "tcp://0.0.0.0:29020"

PUB_ENDPOINT_MAP = {
    'engine-PPEAUCEA-requestResponse': PRIVATE_SUB_ENDPOINT,
    #'PPEAUCEA-Primary':                PRIVATE_SUB_ENDPOINT,
    'PPEASXA->TESTC':                  PRIVATE_SUB_ENDPOINT,
    'PPECXAA->TESTA':                  PRIVATE_SUB_ENDPOINT,
    ## transaction notification
    #'PPEAUCEA->replication':           PRIVATE_SUB_ENDPOINT,
    'PPEAUCEA->QAAUCE_Listener':       PRIVATE_SUB_ENDPOINT,
    'TESTC->PPEASXA':                  PRIVATE_SUB_ENDPOINT,
    'TESTA->PPECXAA':                  PRIVATE_SUB_ENDPOINT,
    'imageliveserver-PPEAUCEA':        PRIVATE_SUB_ENDPOINT,
}

