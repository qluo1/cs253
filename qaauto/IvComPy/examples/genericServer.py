'''
    Author: Luiz Ribeiro (Melbourne Technology Division)
    December, 2015
'''

import os
import sys
import inspect
from threading import Thread

# getting paths
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_DIR = os.path.join(CUR_DIR,"config")

LOG_DIR = os.path.join(CUR_DIR, "logs")
LOG_CONF = os.path.join(CFG_DIR, 'logConfig.gslog')
LOG_NAME = 'genericServer'
SERVER_CONF = os.path.join(CFG_DIR, 'server.py')

PARENT_DIR = os.path.dirname(CUR_DIR)

TIMEOUT = 5 # seconds

print SERVER_CONF, LOG_CONF
# adding IvComPy path to sys
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# registering config scripts to import them
if CFG_DIR not in sys.path:
    sys.path.append(CFG_DIR)

from IvComPy import *
from handlerServerRequestInterface import HandlerServerRequestInterface
from handlerServerRequest import HandlerServerRequest
from handlerBidirectionalDSS import HandlerBidirectionalDSS 
from server import configure

class GenericServer:
    '''
        Simple IvComPy >request< server 
    '''

    def __init__(self, serverConf, logName, logConf=LOG_CONF, logPath=LOG_DIR):
        '''
            Registers log file (if a it already exists, the file is appended.  
            Following creates a manager object and loads this server configuration from config/ 

            @param logConf (String) Path to the .gslog file configuring the log output.
            @param logPath (String) Folder where the log is going to be created. If a file already
                exists,en it is overwritten
            @param logName (String) The log filename. If it already exists, then it's appended.
            @param serverConf (String) Path to the Python script that contains this server's config

            @throws EnvironmentError if configuring either the log of IvComPy fails.
        '''

        self.manager = IvComPyManager()

        # configure log dumping file
        if not self.manager.setuplog(logConf, logName, logPath):
            raise EnvironmentError('Failed to initialize the log file.')

        # load clients data
        if not self.manager.initJson(serverConf):
            raise EnvironmentError('Failed to configure this server.')

        # getting the list of request clients that this server is going to communicate with
        self.requestorNames = self.manager.requestServerNames

        # getting list of dss clients
        self.dssNames = self.manager.dssNames

        self.requestors = {}
        self.dssHandlers = {}
        self.__running = False


    def run(self):
        '''
            Creates a thread for the server to run.
        '''

        self.serverThread = Thread(target=self.manager.run)
        self.serverThread.start()
        if not self.serverThread.isAlive():
            print 'ERROR: failed to create server thread'
            exit(1)

        self.__running = True


    def getRequestClients(self):  
        '''
            Returns a list with the names of the request servers specified on the initial config
            @returns list(String)
        '''
        return self.requestorNames


    def getDSSClients(self):
        '''
            Returns a list with the names of the dss servers specified on the initial config
            @returns list(String)
        '''
        return self.dssNames


    def setRequestHandler(self, providerName, handlerClass):
        '''
            Installs a specific handler to listen to a certain service
            @param providerName (String): the name of the service to listen to
            @param handlerClass (Class): the handler class, it must implement the HandlerServerRequestInterface interface
            @raises ValueError: if the @providerName does not exist.
        '''
        if not inspect.isclass(handlerClass):
            raise TypeError('The handlerClass parameter must be a class (not an object)')

        if not issubclass(handlerClass, HandlerServerRequestInterface):
            raise TypeError('The handlerClass parameter must implement HandlerServerRequestInterface')

        handler = self.manager.getRequestServer(providerName)
        if handler == None:
            raise ValueError('The provider %s does not exist.')

        self.requestors[providerName] = handlerClass(providerName, handler)


    def setupDSSConnections(self):
        """
            Allows the server to send and receive messages using the datastream mode. To do so, the initial 
            configuration parameters must specify both a datastream client and server interfaces with the same name.
            The client interface is used to receive messages, while the server interface is employed to send them.
            @raises EnvironmentException: if either there's no datastream client/server on the initial configuration
                or if there are unpaired datastream client/servers.
        """

        # registers the bidirectional DSS handler for every described datastream connection
        inboundDSS = self.manager.dssNames
        outboundDSS = self.manager.serverDatastreamNames

        # checking if for every DSS client (inbound) there's a DSS server (outbound)
        setIn = set(inboundDSS)
        setOut = set(outboundDSS)

        # the last conditions check for empty set, as intersect(x, 0) = 0
        if len(inboundDSS) == 0:
            raise EnvironmentError('There is no datastream client (inbound interface) present on the configuration file.')

        for name in inboundDSS:
            inHandler = self.manager.getDss(name)
            outHandler = self.manager.getServerDatastreamClient(name)

            if outHandler == None:
                raise EnvironmentError('The datastream client [%s] has no corresponding server (outbound interface).' % name)

            self.dssHandlers[name] = HandlerBidirectionalDSS(name, inHandler, outHandler)


    def sendDSSMessage(self, streamName, tableName, msgData, msgId, posDup):
        '''
            Enqueues a message to be sent by the datastream handler
            @param streamName (String): the name of the dsstream to send the message
            @param tableName (String): Name of the table containning the message
            @param msgId (int): The id of the message, it must be a unique number
            @param msgData (dict): Mapping of the table fields to values
            @param posDup (bool): ?
            @raises KeyError: if @streamName does not exist
        '''

        if not streamName in self.dssHandlers:
            raise KeyError('Stream [%s] does not exist.' % streamName)

        self.dssHandlers[streamName].sendMessage(tableName, msgData, msgId, posDup)


    def getDSSMessage(self, streamName, timeout=None):
        '''
            Gets a message received by the datastream interface, if any.
            @param timeout (int): if supplied, thid method blocks for at most @timeout seconds waiting for a 
                message. In this case, if no message is received, a Queue.Empty error is raised. By default
                this method waits indefinitely.
            @returns dict: the dictionary containning the message, None if
            there are no new messages.
            @raises KeyError: if @streamName does not exist
        '''

        if not streamName in self.dssHandlers:
            raise KeyError('Stream [%s] does not exist.' % streamName)

        return self.dssHandlers[streamName].getMessage(timeout)


    def stop(self):
        '''
            Unregister all listening callbacks and tries to stop the server thread. This later
            operation MAY fail if its invoked shortly after run().

            @returns bool: True if the server thread was successfully stopped. False otherwise.
        '''

        if self.manager:
            self.manager.stop()
            for handler in self.requestors:
                print 'Stopping to listen to %s' % handler
                self.requestors[handler].unregister()

            # joinning the server thread
            if self.__running:
                self.serverThread.join(TIMEOUT)
                self.__running = False
                return not self.serverThread.isAlive()

            return False

        return False



def loadServerConf():
    '''
        Loads client configuration from script (py dict) and returns as a JSON (string)
    '''

    import json
    return json.dumps(configure())


if __name__ == '__main__':
    server = GenericServer(loadServerConf(), LOG_NAME, LOG_CONF, LOG_DIR)
    server.setRequestHandler('sample-requests', HandlerServerRequest)
    server.setupDSSConnections()
    server.run()


    import time
    time.sleep(1)

    print 'Server: Server running. Waiting for the client to send a DS message'
    msg = server.getDSSMessage('sample-datastream')

    print 'Server: Received a server datastream message'
    print msg
    print 'Server: Responding back'

    response = {
        'text': 'Ok, I am sending another message soon'
    }
    server.sendDSSMessage('sample-datastream', 'TextMessage', response, 1, False)

    response['text'] = 'Are you still there? Send me request messages now.'
    server.sendDSSMessage('sample-datastream', 'TextMessage', response, 2, False)

    print 'Server: Entering in reactive mode. Will respond to request messages, to finish the server hit CTRL+C'

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    if not server.stop():
        print 'Server failed to stop'

