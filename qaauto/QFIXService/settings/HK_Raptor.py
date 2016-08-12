from common import *
import logging

TIMEZONE = "Asia/Hong_Kong"
#######################################
## zmq publish end point
#ORDER_API_ENDPOINT = "ipc:///tmp/fix_order_request"
#PUBSUB_ENDPOINT = "ipc:///tmp/fix_er_sub"

ORDER_API_ENDPOINT = "tcp://10.152.138.253:6809"
PUBSUB_ENDPOINT = "tcp://10.152.138.253:6810"

## fix db repository
RDB_API_ENDPOINT = "ipc:///tmp/rdb_service"

## 
#QUICKFIX_CFG = os.path.join(ROOT,"etc","qfix.config")
QUICKFIX_CFG = os.path.join(ROOT,"etc","HK_Raptor.config")

## fix session map
SESSION_MAPS = {
    'RONINDO': 'FIX.4.2:RONINDO->GSHKG',
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
