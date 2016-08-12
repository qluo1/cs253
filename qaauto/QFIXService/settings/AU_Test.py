""" remote QFIXService configuration for local tesing session. 


"""
from common import *
import logging

TIMEZONE = "Australia/Sydney"
#######################################
## zmq publish end point
#ORDER_API_ENDPOINT = "ipc:///tmp/fix_order_request"
#PUBSUB_ENDPOINT = "ipc:///tmp/fix_er_sub"
ORDER_API_ENDPOINT = "tcp://d48965-004:6809"
PUBSUB_ENDPOINT = "tcp://d48965-004:6810"

## fix db repository
RDB_API_ENDPOINT = "ipc:///tmp/rdb_service"

## FIX session name
TEST_SESSION = "APOLLO.TEST"

PYFIX_MODULE = "pyfix42"

## mapping  from FIXOrder to FIX
FIXORDER_MAPPING_PROCESS = {

    'default':
    (
        'tests.processor.Base_Processor',
        'tests.processor.NewOrderSingle',
        'tests.processor.OrderCancelReplaceRequest',
        'tests.processor.OrderCancelRequest',
    ),
    ## session specific override default
    'PTIRESS':
    (
        'tests.processor.Base_Processor',
        'tests.processor.NewOrderSingle',
        'tests.processor.OrderCancelReplaceRequest',
        'tests.processor.OrderCancelRequest',
    ),
    ## session specific override default
    'BBRTEST':
    (
        'tests.processor.Base_Processor',
        'tests.processor.NewOrderSingle',
        'tests.processor.OrderCancelReplaceRequest',
        'tests.processor.OrderCancelRequest',
        'tests.processor.BBRTEST_currency',
   ),

}


FIXER_MAPPING_VALIDTE = {

    'default':
    (
        'tests.validator.Generic_Validator',
    ),
}

#########################################
## return FIX Order as well as FIX ER
ACK_ER_REQUEST = False

DEFAULT_CURRENCY = "AUD"
DEFAULT_SECURITY_EXT = ".AX"

#####################################
## default timeout for ER ack
WAIT_ACK = 5 * 6
