""" remote QFIXService configuration for local tesing session. 


"""
from common import *
import logging

TIMEZONE = "Australia/Sydney"
#######################################
## zmq publish end point
#ORDER_API_ENDPOINT = "ipc:///tmp/fix_order_request"
#PUBSUB_ENDPOINT = "ipc:///tmp/fix_er_sub"
ORDER_API_ENDPOINT = "tcp://10.152.138.253:6809"
PUBSUB_ENDPOINT = "tcp://10.152.138.253:6810"

## fix db repository
RDB_API_ENDPOINT = "ipc:///tmp/rdb_service"

## FIX session name
TEST_SESSION = "RONINDO"

PYFIX_MODULE = "pyfix42"

## mapping  from FIXOrder to FIX
FIXORDER_MAPPING_PROCESS = (
    'tests.processor.Base_Processor',
    'tests.processor.NewOrderSingle',
    'tests.processor.OrderCancelReplaceRequest',
    'tests.processor.OrderCancelRequest',
)

FIXER_MAPPING_VALIDTE = (
    'tests.validator.Generic_Validator',
)
#########################################
## return FIX Order as well as FIX ER
ACK_ER_REQUEST = False

DEFAULT_CURRENCY = "HKD"
DEFAULT_SECURITY_EXT = ".HK"

#####################################
## default timeout for ER ack
WAIT_ACK = 2 * 60
