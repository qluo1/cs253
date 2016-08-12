from common import *


GSLOGCFG = os.path.join(SETTING_DIR,"gslog.cfg")
OMA_SEQ_FILE = os.path.join(TMP_DIR,"oma_seq.dat")
##  internal nvp publish endpoint
PUB_ENDPOINT = "ipc:///tmp/omapy_publisher"
##  external OMA NVP API
#OMA_API_URL = "ipc:///tmp/omaapi"
## oma rpc server endpoint
OMA_API_URL = "ipc:///tmp/oma_graph_py"


## redis server
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1

## nun of days that nvp time to live in redis
NVP_TTL = 2

## python 2.7+
LOG_CFG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(process)d %(threadName)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'logfile': {
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR,"OMAClientPy.log"),
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
