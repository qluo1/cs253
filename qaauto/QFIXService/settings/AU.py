from common import *
import logging

TIMEZONE = "Australia/Sydney"
#######################################
## zmq publish end point
#ORDER_API_ENDPOINT = "ipc:///tmp/fix_order_request"
#PUBSUB_ENDPOINT = "ipc:///tmp/fix_er_sub"

ORDER_API_ENDPOINT = "tcp://0.0.0.0:6809"
PUBSUB_ENDPOINT = "tcp://0.0.0.0:6810"

## fix db repository
RDB_API_ENDPOINT = "ipc:///tmp/rdb_service"

## 
#QUICKFIX_CFG = os.path.join(ROOT,"etc","qfix.config")
QUICKFIX_CFG = os.path.join(ROOT,"etc","AUT2.config")

## fix session map
SESSION_MAPS = {
    'PTIRESS': 'FIX.4.2:LUOSAM1->GSASIAQA',
    'LUOSAM':  'FIX.4.2:LUOSAM->GSASIAQA',
    'BBRTEST': 'FIX.4.2:BBRTEST->GSCO2',
    'RONINQA': 'FIX.4.2:RONINQA->LUOSAMQA',
    'JIANGA':  'FIX.4.2:JIANGA->GSASIAQA',
    'ITGAU':   'FIX.4.2:ITGAU->GSASIA',
    'ITGSAM':  'FIX.4.2:ITGSAM->GSSAM',
    'QA13GSET':'FIX.4.2:QA13->GSET',
    'PERPETUAL':'FIX.4.2:PERPETUALQA->GSASIAQA',
    'APOLLO.TEST': 'FIX.4.2:AUT2->GSET',
}


## python 2.7+
LOG_CFG = {
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
            'filename': os.path.join(LOG_DIR,"QFIX_AU.log"),
            'level': 'INFO',
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
