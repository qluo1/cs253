from common import *
import logging
import os

TIMEZONE = "Asia/Hong_Kong"
INSTANCE = 'JP_RAW'

## DC session setup
DC_CFG = os.path.join(ROOT,"config","JP.RAW.DC.fix.config")

## fix session map
SESSION_MAPS = {
    'DC_RAPTOR': 'FIX.4.2:GSETQADC->RaptorRaw',
}

## AHD related settings
CFG = {
    'clientID': 'COLOC01',
    'securityCSV'    : os.path.join(REF_DATA,'security.csv'),
    'restrictionCSV' : os.path.join(REF_DATA,'restrictions.csv'),
    'limitsCSV'      : os.path.join(REF_DATA,'clientLimits.csv'),
    'tickSizeCSV'    : os.path.join(REF_DATA,'tickSize.csv'),
    'logLevel': 'INFO',
    'prefix' : 'COLOC01',
    'opStart': 'True',

# Connecting to relay script on gset-tse-q01.tk.eq.gs.com (10.100.193.36)
    'VS0030':  {
        'remoteIp':'10.100.193.36',
        'remotePort': 40350,
        'localIp':'10.100.193.40',
        'localPort': 11030,
        'vsNum': 'VS0030',
        'hbtInterval': 10,
        'hbtTimeout': 60,
        'participantCode': '11560',
        'logLevel': logging.INFO,
        'bindWaitTime':60,},
    }

# Used by relay script
RELAY_CFG = {
    'tse' : {
        'incoming_binding': ('', 40350),
        'outgoing_binding': ('2.2.2.2', 11030),
        'outgoing_connecting': ('3.3.3.1', 9445)
    },
    'jnx' : {
        'incoming_binding': ('5.5.5.2', 40350),
        'outgoing_connecting': ('10.100.193.40', 9446)
    }
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
            'class':'logging.handlers.RotatingFileHandler',
            'mode': 'a',
            'filename': os.path.join(LOG_DIR,"JP_RAW_Raptor.log"),
            'level': 'INFO',
            'backupCount': 5,
            'delay': True,
            'formatter': 'verbose',
        },
# By default console log will be printed to stderr, then collected by pytest as report
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

