import os
import logging
import random
## all setting must be upper case
##
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CUR_DIR)

## logging dir
LOG_DIR = os.path.join(PROJ_DIR,"logs")

## GS logging cfg
LOGCFG = os.path.join(CUR_DIR,"log.cfg")
##########################################
## random internal socket publish MDT raw data
INTERNAL_PUB_ENDPOINT = "ipc:///tmp/MarketDataFeed_{0}.sock".format(str(random.random())[2:])

##################################
## publich method for publish
MARKET_PUBLISH_METHOD ="on_market_data"
#############################################
## common service 
### query prime symbol from remote rpc srevice
ivcomservice_host_remote = "d48965-004.dc.gs.com"
########################################
### sybase db service.
#OM2DBSERVICE_URL = "tcp://%s:39010" % ivcomservice_host_remote
OM2DBSERVICE_URL = "tcp://%s:62001" % ivcomservice_host_remote

## default
IGNORE_SYMBOLS = []

