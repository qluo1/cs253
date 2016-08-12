'''
    Author: Luiz Ribeiro (Melbourne Technology Division)
    December, 2015
'''

# adding import path
import os
import sys

UPDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if UPDIR not in sys.path:
    sys.path.append(UPDIR)

import unittest
import time
from genericClient import GenericClient, loadClientConf # use the same configs as the demo example
from handlerClientRequest import HandlerClientRequest

CLIENT_LOG = 'utestClient'
REQ_PROVIDER = 'sample-requests'

class RequestClientTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        ''' Creating a client but doesn't set it to run '''

        cls.client = GenericClient(clients=loadClientConf(), logName=CLIENT_LOG)
        cls.client.setRequestHandler('sample-requests', HandlerClientRequest)

    def test_getDSSConnections(self):
        registeredDSSs = self.client.getDSSConnectionNames()
        expectedDSS = ['sample-datastream']

        setDSS = set(registeredDSSs)
        expectedDSS = set(['sample-datastream'])
        self.assertEquals(setDSS.intersection(expectedDSS), expectedDSS)

    def test_getRequestConnections(self):
        registeredReqs = self.client.getRequestConnectionNames()
        expected = set(['sample-requests'])

        setReqs = set(registeredReqs)
        self.assertEquals(setReqs.intersection(expected), expected)

    def test_registerInvalidReqServer(self):
        self.assertRaises(ValueError,self.client.setRequestHandler, 'invalid-name', HandlerClientRequest)

    def test_registerInvalidEmptyReqServer(self):
        self.assertRaises(ValueError, self.client.setRequestHandler, '', HandlerClientRequest)

    def test_registerInvalidHandlerClassParameter(self):
        self.assertRaises(TypeError, self.client.setRequestHandler, 'sample-requests', [10, 20, 30])

    def test_registerInvalidHandlerClass(self):
        class DummyClass:
            pass

        self.assertRaises(TypeError, self.client.setRequestHandler, 'sample-requests', DummyClass)

    def test_setupDSSConnections(self):
        self.client.setupDSSConnections()
        

if __name__ == '__main__':
    print 'NOTICE: the test output was redirected to the log file'
    unittest.main()

