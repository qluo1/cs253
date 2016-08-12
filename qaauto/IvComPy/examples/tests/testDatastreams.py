'''
    Author: Luiz Ribeiro (Melbourne Technology Division)
    December, 2015
'''

'''
Since the datastream handler is bidirectional, client and server use the same code.
Because of this, unit testing one side is already enough
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
from genericServer import GenericServer, loadServerConf
from handlerClientRequest import HandlerClientRequest

import json
from utils import convert
from Queue import Empty

CLIENT_LOG = 'utestDSClient'
SERVER_LOG = 'utestDSServer'
REQ_PROVIDER = 'sample-requests'

#some dict keys
DS_SERVER = 'server-datastreams'
DS_CLIENT = 'client-datastreams'

#default message table parameters
STREAM_NAME = 'sample-datastream'
INVALID_STREAM = 'invalid-stream'
TABLE_NAME = 'TextMessage'
MSG_DATA = { 'text': 'testing message sending' }
TIMEOUT = 1 #second


class MockServer:
    ''' Utility DS singleton server for testing '''

    __instance = None

    def __init__(self):
        if MockServer.__instance == None:
            MockServer.__instance = GenericServer(loadServerConf(), SERVER_LOG)
            MockServer.__instance.setupDSSConnections()
            MockServer.__instance.run()
            time.sleep(1)

    def get(self):
        return MockServer.__instance


class DatastreamClientTest(unittest.TestCase):
    '''
        This unittests focus mostly on configuring the IvComPy client datastream mode incorrectly
    '''

    @classmethod
    def setUpClass(cls):
        # the loaded configuration comes as a string. Converting the string back to JSON causes it to
        # be encoded as unicode, we undo this by using the convert() utility. 
        # cls.cfg is kept is memory because many tests consist in trying to create a server with invalid
        # datastream configurations
        cls.cfg = convert(json.loads(loadClientConf()))

    def __removeDS(self, fields):
        ''' Helper method that returns the configuration string withtout the specified parameter '''
        toReturn = dict(self.cfg)

        if type(fields) != list:
            fields = [fields]

        for field in fields:
            del toReturn[field]

        return str(toReturn)


    def test_createClientWithNoDSServer(self):
        self.assertRaises(EnvironmentError, GenericClient, self.__removeDS(DS_SERVER), CLIENT_LOG)

    def test_createClientWithNoDSClient(self):
        self.assertRaises(EnvironmentError, GenericClient, self.__removeDS(DS_CLIENT), CLIENT_LOG)

    def test_setupDSWithNoInterface(self):
        client = GenericClient(self.__removeDS([DS_CLIENT, DS_SERVER]), CLIENT_LOG) 
        self.assertRaises(EnvironmentError, client.setupDSSConnections)

    def test_sendDSMessageInvalidProvider(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        client.setupDSSConnections()
        client.run()
        self.assertRaises(KeyError, client.sendDSSMessage, INVALID_STREAM, TABLE_NAME, MSG_DATA, 1, False)
        client.stop()

    def test_getDSMessageInvalidProvider(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        client.setupDSSConnections()
        client.run()
        self.assertRaises(KeyError, client.getDSSMessage, INVALID_STREAM, TIMEOUT)
        time.sleep(1)
        client.stop()

    def test_getDSMessageEmptyQueue(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        client.setupDSSConnections()
        client.run()
        self.assertRaises(Empty, client.getDSSMessage, STREAM_NAME, TIMEOUT)
        time.sleep(1)
        client.stop()

    def test_sendReceiveDSMessageTimeout(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        server = MockServer().get()

        client.setupDSSConnections()
        client.run()
        time.sleep(1)
        client.sendDSSMessage(STREAM_NAME, TABLE_NAME, MSG_DATA, 1, False)

        try:
            msg = server.getDSSMessage(STREAM_NAME, TIMEOUT * 4)
            self.assertEquals(msg['msg'], MSG_DATA)
        except Empty:
            client.stop()
            server.stop()
            self.fail('The server should have received a message')

        client.stop()
        server.stop()

    def test_setDSConnectionsWithServerRunning(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        client.run()
        self.assertRaises(RuntimeError, client.setupDSSConnections)
        client.stop()

    def test_sendDSMessageWithServerStopped(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        self.assertRaises(RuntimeError, client.sendDSSMessage, STREAM_NAME, TABLE_NAME, MSG_DATA, 1, False)

    def test_getDSMessageWithServerStopped(self):
        client = GenericClient(loadClientConf(), CLIENT_LOG)
        self.assertRaises(RuntimeError, client.getDSSMessage, STREAM_NAME)


if __name__ == '__main__':
    print 'NOTICE: the test output was redirected to the log file'
    unittest.main()

