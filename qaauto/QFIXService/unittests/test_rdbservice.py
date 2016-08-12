from pprint import pprint
from conf import settings
import gevent
import zerorpc
import pyfix42
from datetime import datetime
from utils import SeqNumber

api = zerorpc.Client(settings.RDB_API_ENDPOINT)

def test_list_today_msg():
    """ """
    for item in api.gen_messages():
        print item

def test_list_today_filter():
    """ """
    print " --- D ---- "
    for item in api.gen_messages(match="D:*"):
        print item
    print " --- 8 ---"
    for item in api.gen_messages(match="8:*"):
        print item
    print " --- G --- "
    for item in api.gen_messages(match="G:*"):
        print item

    print " --- test_2 --- "
    for item in api.gen_messages(match="*:test_9:*"):
        print item
    print " ---D:test_2 --"
    for item in api.gen_messages(match="D:test_9:*"):
        print item

def test_list_summary():
    """ """
    summary = api.list_summary()
    print summary
