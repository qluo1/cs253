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
from genericServer import GenericServer, loadServerConf
from handlerServerRequestInterface import HandlerServerRequestInterface

SERVER_LOG = 'utestServer'
REQ_CLIENT = 'sample-requests'

class TestHandler(HandlerServerRequestInterface):
    def onWork(self, table, msg, msgId, posDup):
        pass

class GenericServerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.reqServer = GenericServer(loadServerConf(), SERVER_LOG)


    def test_retrieveRequestProviders(self):
        providers = self.reqServer.getRequestClients()
        setProviders = set(providers)

        expected = set(['sample-requests'])
        self.assertEquals(setProviders.intersection(expected), expected)

    def test_setInvalidRequestHandler(self):
        self.assertRaises(TypeError, self.reqServer.setRequestHandler, 'sample-requests', None)

    def test_setInvalidRequestHandlerClass(self):
        class DummyClass:
            pass

        self.assertRaises(TypeError, self.reqServer.setRequestHandler, 'sample-requests', DummyClass)

    def test_setValidHandlerClass(self):
        self.reqServer.setRequestHandler('sample-requests', TestHandler)

    def test_setInvalidProviderName(self):
        self.assertRaises(ValueError, self.reqServer.setRequestHandler, 'invalid-requests', TestHandler)

    def test_setEmptyProviderName(self):
        self.assertRaises(ValueError, self.reqServer.setRequestHandler, '', TestHandler)

    def test_runAndStop(self):
        self.reqServer.run()
        time.sleep(2)
        # server was running, should stop
        self.assertTrue(self.reqServer.stop())
        # server already stopped, should return false (no stop)
        self.assertFalse(self.reqServer.stop())


if __name__ == '__main__':
    unittest.main()
