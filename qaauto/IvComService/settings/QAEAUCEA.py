import logging
from common import *

GSLOGCFG = os.path.join(CUR_DIR,"gslog.cfg")
GSLOGNAME = "QAEAUCEA"
IVPYCFG = os.path.join(CONFIG_DIR, "QAEAUCEA.py")


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
            'filename': os.path.join(LOG_DIR,"QAE.log"),
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
            'filename': os.path.join(LOG_DIR,"messageDump_QAE.log"),
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



ORDER_API_URL = "tcp://0.0.0.0:29011"

### collect local publishing
#PRIVATE_SUB_ENDPOINT = "tcp://0.0.0.0:29009"
PRIVATE_SUB_ENDPOINT = "ipc:///tmp/QAEAUCEA"

## forward to public/publish endpint.
PUBLIC_PUB_ENDPOINT = "tcp://0.0.0.0:29010"

PUB_ENDPOINT_MAP = {
 ## handle RF as sync, uncomment to handle RF as async rquest/sub.
   'engine-QAEAUCEA-requestResponse': PRIVATE_SUB_ENDPOINT,
 #  'QAEAUCEA-Primary':                PRIVATE_SUB_ENDPOINT,
 ####### datastream
    'QAEASXA->TESTC':                  PRIVATE_SUB_ENDPOINT,
    'QAECXAA->TESTA':                  PRIVATE_SUB_ENDPOINT,
    ## transaction notification
    #'QAEAUCEA->replication':           PRIVATE_SUB_ENDPOINT,
    'QAEAUCEA->QAAUCE_Listener':       PRIVATE_SUB_ENDPOINT,
    'TESTC->QAEASXA':                  PRIVATE_SUB_ENDPOINT,
    'TESTA->QAECXAA':                  PRIVATE_SUB_ENDPOINT,
 ####### imagelive
    'imageliveserver-QAEAUCEA':        PRIVATE_SUB_ENDPOINT,
}

