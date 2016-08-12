from common import *
import logging
import os

TIMEZONE = "Asia/Hong_Kong"
INSTANCE = 'HK'

## FIX session
FIX_CFG = os.path.join(ROOT,"config","HK.fix.config")

## DC session
DC_CFG = os.path.join(ROOT,"config","HK.DC.fix.config")

## fix session map
SESSION_MAPS = {
    'RONINDO': 'FIX.4.2:RONINDO->GSHKG',
    'DC_RAPTOR': 'FIX.4.2:HKAPLDCQA->RAPTORHKQA'
}

FIXORDER_MAPPING_PROCESS = (
    'tests.processor.Base_Processor',
    'tests.processor.NewOrderSingle',
    'tests.processor.OrderCancelReplaceRequest',
    'tests.processor.OrderCancelRequest',
)

FIXER_MAPPING_VALIDTE = (
    'tests.validator.Generic_Validator',
)

ACK_ER_REQUEST = False
DEFAULT_CURRENCY = "HKD"
DEFAULT_SECURITY_EXT = ".HK"
WAIT_ACK = 10

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
            'filename': os.path.join(LOG_DIR,"HK_Raptor.log"),
            'level': 'INFO',
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

