'''
	Author: Luiz Ribeiro (Melbourne Technology Division)
	17/12/2015	
'''

import abc
from IvComPy import IvComPyServer

class HandlerServerRequestInterface:
    '''
        An interface that must be implemented by classes that are going to handle events produced by
        IvComPy's request server (currently just OnWork). This interface grants to the server that the
        provided class has the necessary methods withouth performing duck type checking
    '''

    __metaclass__ = abc.ABCMeta

    def __init__(self, providerName, handler):
        '''
            Registers the abstract onWork method to be triggered by IvComMessage, thus processing
            the received message and returning a response to the requesting client
            @param providerName (String): the name of the provider
            @param handler (IvComPyServer): the handler object created internally by IvComPy
        '''
        assert type(handler) == IvComPyServer

        self.name = providerName
        self.handler = handler
        self.handler.setupCallback('onWork', self)

    @abc.abstractmethod
    def onWork(self, table, msg, msgId, posDup):
        '''
            This function is automatically invoked when the server receives a request.
            The requestor client waits for a server response, which is sent only after this
            function is terminated. 

            WARNING:
            Still, if this functoin takes a long time to execute, it locks the server thread.

            @param table (String) the table name
            @param msg (dict) a Python dictionary containning the IvComMessage
            @param msgId (int) the message id
            @param posDup (bool) -
            @returns tuple(String, dict) a tuple containning the returning message table name and a dict with the
            message itself.
        '''
        return

    def unregister(self):
        return 0

    def __str__(self):
        return self.name
