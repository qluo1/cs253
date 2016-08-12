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
from threading import Event
from genericClient import GenericClient, loadClientConf # use the same configs as the demo example
from genericServer import GenericServer, loadServerConf  
from handlerClientRequestInterface import HandlerClientRequestInterface
from handlerServerRequestInterface import HandlerServerRequestInterface

CLIENT_LOG = 'commTestClient'
SERVER_LOG = 'commTestServer'
REQ_PROVIDER = 'sample-requests'

# amount of time that the test unit waits for the request server to respond
TIMEOUT = 3 # seconds
K = 10 # amount of messages that the server has to receive
_msgsServer = 0 # amount of messages received by the server

# used to notify the test unit that the client has received a response
_globalFlag = Event()
_serverReachedK = Event()


class ClientHandlerTest(HandlerClientRequestInterface):
    ''' Class to check if a simgle message has arrived. '''

    def onResponse(self, table, msg):
        _globalFlag.set()    #awakens the waiting thread
        
    def unregister(self):
        return


class ServerHandlerTest(HandlerServerRequestInterface):
    ''' Class to check if the server has received K messages'''
    
    def onWork(self, table, msg, msgId, posDup):
        global _msgsServer
        _msgsServer += 1

        if _msgsServer == K:
            _serverReachedK.set() #awakens the unittest thread

        response = { 'text' : 'Server test msg' }
        return ('TextMessage', response)


class TestRequestCommunication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ''' Creating a client and setting it to run '''

        cls.client = GenericClient(clients=loadClientConf(), logName=CLIENT_LOG)
        cls.client.setRequestHandler('sample-requests', ClientHandlerTest)
        cls.client.run()

        cls.server = GenericServer(loadServerConf(), CLIENT_LOG)
        cls.server.setRequestHandler('sample-requests', ServerHandlerTest)
        cls.server.run()
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        '''Shuts down the client. '''

        time.sleep(2)    # ensures that the server is never killed right before its startup
        cls.server.stop()
        cls.client.stop()


    def test_sendMessageAndWaitResponse(self):
        # assumes that the client is configured to send messages in TextMessage tables
        testMessage = {
            'text' : 'This is a test message',
            'int1' : 42
        }
        sent = self.client.sendRequestMessage('sample-requests', 'TextMessage', testMessage)
        self.assertTrue(sent)

        # wait for a response
        _globalFlag.wait(TIMEOUT)
        if not _globalFlag.isSet():
            self.fail()


    def test_burstCommunication(self):
        ''' Asserts thet client and server can exchange an indefinite amount of messages'''
        testMessage = {
            'text' : 'This is a test message',
            'int1' : 42
        }

        for i in range(K):
            sent = self.client.sendRequestMessage('sample-requests', 'TextMessage', testMessage)
            self.assertTrue(sent)

        _serverReachedK.wait(TIMEOUT)
        if not _serverReachedK .isSet():
            self.fail()


if __name__ == '__main__':
    print 'NOTICE: the test output was redirected to the log file'
    unittest.main()

