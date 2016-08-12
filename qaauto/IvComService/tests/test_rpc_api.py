from datetime import datetime
import time
import os
import zerorpc

from utils import IvComDictHelper


env = os.environ['SETTINGS_MODULE'].split(".")[-1]

HOSTNAME = "d127601-081"
HOSTNAME_OM2 = "qaeaucea-1.qa.om2.services.gs.com"

ENDPOINTS = {'QAEAUEA':"tcp://%s:29011" % HOSTNAME_OM2,
             'PPEAUEA':"tcp://%s:29021" % HOSTNAME_OM2,
             'PMEAUEA':"tcp://%s:29031" % HOSTNAME_OM2,
             }



def test_handle_status():
    """
    """
    for k,url in ENDPOINTS.iteritems():
        api = zerorpc.Client(url)

        res =  api.handle_status()
        assert res
        print res
