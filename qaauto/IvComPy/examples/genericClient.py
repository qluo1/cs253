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
PARENT_DIR = os.path.dirname(CUR_DIR)

LOG_DIR = os.path.join(CUR_DIR, "logs")
LOG_CONF = os.path.join(CFG_DIR, 'logConfig.gslog')
LOG_NAME = 'genericClientLog'

# timeout for joinning the IvComManager thread. If it is joined too soon
# after its creation, it MAY cause the client to deadlock.
TIMEOUT = 5

# adding IvComPy path to sys
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# registering config script to import it 
if CFG_DIR not in sys.path:
    sys.path.append(CFG_DIR)

from IvComPy import *
from handlerClientRequest import HandlerClientRequest 
from handlerClientRequestInterface import HandlerClientRequestInterface 
from handlerBidirectionalDSS import HandlerBidirectionalDSS
from client import configure


class GenericClient:
    '''
        An IvComPy client that can work both on request and datastream mode.
        While the request mode allows the user to specify which RequestHandler will be
        used, the DatastreamMode uses a specified handler.
    '''

    def __init__(self, clients, logName, logConf=LOG_CONF, logPath=LOG_DIR):
        '''
            Registers log file (if a it already exists, the file is appended.  
            Following creates a manager object, load clients configuration from the 
            [clients] parameter, finally it registers the proper callback functions to listen
            to server events.

            @param clients (String) JSON object containning the clients configuration data. 
            @param logName (String) The log filename. If it already exists, then it's appended.
            @param logConf (String) Path to the .gslog file configuring the log output.
            @param logPath (String) Folder where the log is going to be created. 
            @throws EnvironmentError if configuring either the log or IvComPy fails.
        '''

        self.manager = IvComPyManager()
        # configure log dumping file
        if not self.manager.setuplog(logConf, logName, logPath):
            raise EnvironmentError('Failed to initialize the log file.')

        # load client data
        if not self.manager.initJson(clients):
            raise EnvironmentError('Failed to load clients configuration data.')

        # checking if datastreams are paired
        self.inboundDSS = self.manager.dssNames
        self.outboundDSS = self.manager.serverDatastreamNames

        if len(self.inboundDSS) != len(self.outboundDSS):
            raise EnvironmentError('The amount of ddatastream clients and servers must be the same.')

        for name in self.inboundDSS:
            inHandler = self.manager.getDss(name)
            outHandler = self.manager.getServerDatastreamClient(name)

            if outHandler == None:
                raise EnvironmentError('The datastream client [%s] has no corresponding server (outbound interface).' \
                    % name)

        # initially there are no registered client handlers
        self.datastreamHandlers = {}
        self.requestHandlers = {}

        self.__running = False


    def setupDSSConnections(self):
        """
            Allows the client to send and receive messages using the datastream mode. To do so, the initial 
            configuration parameters must specify both a datastream client and server interfaces with the same name.
            The client interface is used to receive messages, while the server interface is employed to send them.
            @raises EnvironmentException: if either there's no datastream client/server on the initial configuration
                or if there are unpaired datastream client/servers.
            @raises RuntimeError: if this function is invoked while the client is running.
        """

        if self.__running:
            raise RuntimeError('Can\'t setup DS connections with the client running')

        # the last conditions check for empty set, as intersect(x, 0) = 0
        if len(self.inboundDSS) == 0:
            raise EnvironmentError('This server has no configured datastred interface.')

        for name in self.inboundDSS:
            inHandler = self.manager.getDss(name)
            outHandler = self.manager.getServerDatastreamClient(name)

            if outHandler == None:
                raise EnvironmentError('The datastream client [%s] has no corresponding server (outbound interface).' % name)

            self.datastreamHandlers[name] = HandlerBidirectionalDSS(name, inHandler, outHandler)


    def sendDSSMessage(self, streamName, tableName, msgData, msgId, posDup):
        '''
            Enqueues a message to be sent by the datastream handler
            @param streamName (String): the name of the dsstream to send the message
            @param tableName (String): Name of the table containning the message
            @param msgId (int): The id of the message, it must be a unique number
            @param msgData (dict): Mapping of the table fields to values
            @param posDup (bool): ?
            @raises KeyError: if @streamName does not exist
            @raises RuntimeError: if an attempt to send a DS message with the client stoped is made
        '''
        
        if not self.__running:
            raise RuntimeError('The client must be running in order to send a message.')

        if not streamName in self.datastreamHandlers:
            raise KeyError('Stream [%s] does not exist.' % streamName)

        self.datastreamHandlers[streamName].sendMessage(tableName, msgData, msgId, posDup)


    def getDSSMessage(self, streamName, timeout=None):
        '''
            Gets a message received by the datastream interface, if any.
            @param timeout (int): if supplied, thid method blocks for at most @timeout seconds waiting for a 
                message. In this case, if no message is received, a Queue.Empty error is raised. By default
                this method waits indefinitely.
            @returns dict: the dictionary containning the message, None if
            there are no new messages.
            @raises KeyError: if @streamName does not exist
            @raises RuntimeError: if an attempt to retrieve a DS message with the client stopped is made.
        '''

        if not self.__running:
            raise RuntimeError('The client must be running in order to retrieve a message.')

        if not streamName in self.datastreamHandlers:
            raise KeyError('Stream [%s] does not exist.' % streamName)

        return self.datastreamHandlers[streamName].getMessage(timeout)


    def setRequestHandler(self, providerName, handlerClass):
        '''
            Installs a handler to communicate and listen to server events.
            @param providerName (String): the name of the request server, present on the configuration parameters.
            @param handlerClass (Class): a class that implements HandlerClientRequestInterface.
            @raises ValueError: if the provided @providerName does not exist.
            @raises RuntimeError: if this method is invoked while the client is executing
        '''

        if self.__running:
            raise RuntimeError('Can\'t change configurations while the client is executing.')

        if not inspect.isclass(handlerClass):
            raise TypeError('The handlerClass parameter must be a class (not an object)')

        if not issubclass(handlerClass, HandlerClientRequestInterface):
            raise TypeError('The handlerClass parameter must implement HandlerClientRequestInterface')

        clientR = self.manager.getClientRequest(providerName)
        if clientR == None:
            raise ValueError('The provider %s does not exist.')

        self.requestHandlers[providerName] = handlerClass(providerName, clientR)

    
    def getRequestConnectionNames(self):
        '''
            Returns the name of the available request providers
            @returns (list) a list of request server names
        '''
        return self.manager.clientRequestNames


    def getDSSConnectionNames(self):
        '''
            Returns the name of the registere dDSS providers.
            @returns (list) a list of DSS server names
        '''
        return self.manager.dssNames

    
    def sendRequestMessage(self, server, tableName, messageDict):
        '''
            Sends a request message to the server.
            @param server (String): the name of the request server
            @oaram tableName (String): the table name described on the loaded catalog
            @param messagDict (dict): a dictionary with the mapping message field -> value
            @returns (bool): True of false indicating if the message was successfully
            @throws LookupError: if @server isn't registered.
        '''
        assert messageDict and type(messageDict) == dict

        if not self.__running:
            raise RuntimeError('The client must be running in order to send a message.')

        if not server in self.requestHandlers:
            raise LookupExpection("Server not registered.")

        return self.requestHandlers[server].sendMessage(tableName, messageDict)


    def run(self):
        """
            Creates a new thread to run the IvComManager process.
            @throws RuntimeError if it fails to spawn the client thread.
        """

        # starting the manager
        self.clientThread = Thread(target=self.manager.run)
        self.clientThread.start()
        if not self.clientThread.isAlive():
            raise RuntimeError("Failed to create client thread.")

        self.__running = True


    def stop(self):
        '''
            Tries to terminate the client thread. This method may fail if its invoked
            too soon after initializing the IvCom manager thread (aka. invoking the run() metod).
            This function waits TIMEOUT seconds for the child thread to join. In case of
            timeout the application has to be forcely terminated, as Python waits for all threads
            to finish before leaving.

            @returns bool: True if the client thread stopped successfully. False otherwise.
        '''

        if self.manager:
            self.manager.stop()

            #for handler in self.requestHandlers:
            #    print 'Stopping to listen to %s' % handler
            #    self.requestHandlers[handler].unregister()

            # joinning the manager 
            if self.__running:
                self.clientThread.join(TIMEOUT)
                self.__isRunning = self.clientThread.isAlive()

                return not self.clientThread.isAlive()
            else:
                return True
        return False



def loadClientConf():
    '''
        Loads client configuration from script (py dict) and returns as a JSON (string)
    '''

    import json
    return json.dumps(configure())


if __name__ == '__main__':
    import time

    client = GenericClient(loadClientConf(), LOG_NAME, LOG_CONF, LOG_DIR)
    client.setupDSSConnections()
    client.setRequestHandler('sample-requests', HandlerClientRequest)

    client.run()
    time.sleep(3)

    import Queue

    print 'Client: DSS message exchange demonstration'
    print 'Client: Sending a DSS message to the server'

    msg = {
        'text': 'I am available to receive DSS messages.'
    }
    client.sendDSSMessage('sample-datastream', 'TextMessage', msg, 1, False)

    print 'Client: Waiting for the server to send a DSS response'
    msg = client.getDSSMessage('sample-datastream')

    print '\nReceived:'
    print msg

    print 'Client: Waiting 3 seconds for a new DSS message'
    msg = None
    try:
        msg = client.getDSSMessage('sample-datastream', 3)
    except Queue.Empty:
        print 'Client: The message did not arrive (unexpected behavior)'

    print 'Client: Received message:'
    print msg

    print 'Client: Waiting 1 second for another DSS message'
    try:
        msg = client.getDSSMessage('sample-datastream', 1)
    except Queue.Empty:
        print 'Client: Didn\'t receive a message. Ok, this was expected'

    print 'Client: Sending 10 request messages now'

    textMessage = {
        'text' : 'some message goes here.',
        'text1' : 'follows a number',
        'int1' : 1
    }

    for i in range(10):
        print 'Client: sending message #%d.' % (i+1)
        newDict = dict(textMessage)
        newDict['int1'] = i + 1
        if client.sendRequestMessage('sample-requests', 'TextMessage', newDict):
            print 'Client: Server received request successfully.'
        else:
            print 'Client: Message wasn\'t received.'

    print 'Client: Entering in reactive mode. Will print the received request responses. Hit CTRL+C to finish the client.'

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    if not client.stop():
        print 'Client: Client failed to stop'

