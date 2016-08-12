import sys
import os
import pytest
## check which environment
import localcfg
import zerorpc
from conf import settings
JAVA_OMA_API_URL = "ipc:///tmp/oma_graph"

#client = zerorpc.Client(JAVA_OMA_API_URL)

client = zerorpc.Client(settings.OMA_API_URL)
system = "ppe_XDMa"
#@pytest.mark.skip
def test_locate_order():
    #print client.get_order("ppe_XDMa2420160726")
    print client.get_order("qa_ADCb222520160728")
    print client.get_order("qa_ADCb222520160728",nvp=True,version=2)
    #print client.get_order("qa_ADCb222620160728")

def test_list_order():
    for order in client.list_orders(system):
        print " ======== %s ==========" % order
        print client.get_order(order)

def test_list_system():
    print client.list_system()

def test_cleanup_system():
    print client.cleanup_registery()

def test_list_parent_order():

    orders = []
    for order in client.list_orders("ppe_XPXz",parentOnly=True):
        orders.append(order)
    print orders
    for order in orders:
        ret = client.get_order(order)
        assert 'parent' in ret and ret['parent'] == None

def test_list_child():

    orders = []
    for order in client.list_orders(system,childOnly=True):
        orders.append(order)
    print orders
    for order in orders:
        ret = client.get_order(order)
        assert 'parent' in ret and ret['parent'] == None


def test_list_parent_filled_order():
    orders = []
    for order in client.list_orders(system,parentOnly=True,fillOnly=True):
        orders.append(order)
    for order in orders:
        ret = client.get_order(order)
        assert 'parent' in ret and ret['parent'] == None
        assert 'versions' in ret
        assert True in [v[-1] for v in ret['versions']]


def test_list_parent_fill_order_nvp_raw():
    orders = []
    for order in client.list_orders(system,parentOnly=True,fillOnly=True):
        orders.append(order)
    for order in orders:
        ret = client.get_order(order)
        assert 'parent' in ret and ret['parent'] == None
        assert 'versions' in ret
        assert True in [v[-1] for v in ret['versions']]
        versions = ret['versions']
        raw = client.get_order(order,nvp=True,version=versions[0][0],raw=True)
        print raw
        print client.get_order(order,nvp=True,version=versions[0][0])
