""" remote QFIXService configuration for local tesing session. 


"""
from common import *
import logging

TIMEZONE = "Australia/Sydney"
#######################################
## QFIXServiceend point for AU
ORDER_API_ENDPOINT = "tcp://d48965-004:6809"
PUBSUB_ENDPOINT = "tcp://d48965-004:6810"

## fix db repository
RDB_API_ENDPOINT = ":///tmp/rdb_service"

## tornado config
HOST="0.0.0.0"
PORT=5000
DEBUG=True



APP_SETTINGS = {
    'static_folder': STATIC_DIR,
    'template_folder': TEMPLATE_DIR,
}
