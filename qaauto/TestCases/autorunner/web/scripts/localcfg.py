## all external dependency
import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_ROOT = os.path.dirname(CUR_DIR)
PROJ_DIR = os.path.dirname(os.path.dirname(WEB_ROOT))
print PROJ_DIR
LIB_DIR = os.path.join(PROJ_DIR,"libs")
LOG_DIR = os.path.join(PROJ_DIR,"logs")

LOCAL_TMP = os.path.join(CUR_DIR,"tmp")
LOCAL_RESULT = os.path.join(CUR_DIR,"results")

## setup GNS python path
GNS_PTH =os.path.join(CUR_DIR,"gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            sys.path.append(line)

if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)
## need for local settings lookup
if WEB_ROOT not in sys.path:
    sys.path.append(WEB_ROOT)



import logging
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
            'filename': os.path.join(LOG_DIR,"autorunWebUI.log"),
            'level': 'DEBUG',
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

