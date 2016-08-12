"""
"""
from common import *
import logging

RULE_ENDPOINT = "tcp://0.0.0.0:49010"

## rds snapshot folder
RDSDATA = os.path.join(PROJ_ROOT,"rdsdata")

GENRATED_SNAPSHOTS = os.path.join(PROJ_ROOT,"snapshots")

## om2 location
OM2_PATHS = {
        'QAE': "/home/eqtdata/runtime/qa/asia/auce/qaeaucea/om2-primary",
        'PPE': "/home/eqtdata/runtime/preprod/asia/auce/ppeaucea/om2-primary",
        'PME': "/home/eqtdata/runtime/preprod/asia/auce/pmeaucea/om2-primary",
        'QAE_RDS': "/home/eqtdata/runtime/qa/asia/aucesmf/d48965-004.dc.gs.com/prodver",
        "PPE_RDS": "/home/eqtdata/runtime/preprod/asia/aucesmf/d48965-004.dc.gs.com/preprod",
        "PME_RDS": "/home/eqtdata/runtime/preprod/asia/aucesmf/d48965-004.dc.gs.com/prodmirror",
        }

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
            'filename': os.path.join(LOG_DIR,"ruleService.log"),
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

