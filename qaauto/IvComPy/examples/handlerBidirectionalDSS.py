'''
    Author: Luiz Ribeiro (Melbourne Technology Division)
    December, 2015
'''

from IvComPy import IvComPyDssClient, IvComPySvrDSClient
from utils import convert
import Queue


QUEUE_SIZE = 100

class HandlerBidirectionalDSS:
    '''
        This class allows either a client or a server to send and receive messages using the datastream
        communication mode. In order to do so, the service that uses this handler must specify on its
        configuration file BOTH a datasctream client AND server, since the client is used for incoming
        messages and the server for outbound messages.
    '''
    
    def __init__(self, streamName, inboundHandler, outboundHandler):
        '''
            Creates a bidirectional datastream handler to send and receive messages.
            @param streamName (String): the name of the stream
            @param inboundHandler (IvComPyDssClient): the internal IvComPy object created to interface with DSS clients
            @param outboundHandler (IVComPySvrDSClient): the internal IvComPy obj created to interface with DSS servers
        '''
        assert type(inboundHandler) == IvComPyDssClient
        assert type(outboundHandler) == IvComPySvrDSClient

        self.inbound = inboundHandler
        self.outbound = outboundHandler

        # this queue holds received messages
        self.messages = Queue.Queue(QUEUE_SIZE)

        # registering for incoming message
        self.inbound.setupCallback('onMessage', self)

        # triggered when the recipient receives the message, we are ignoring this
        self.outbound.setupCallback('onAck', self)

    
    def onAck(self, data):
        pass

    
    def onMessage(self, table, msg, msgId, posDup):
        '''
            Callback function triggered with a message is received. Stores the received message internally.
            @param table (String): Table name
            @param msg (dict): dictionary with mapping table_fields -> values.
            @param msgId (int): the message sequential number
            @param posDup (bool): ?
        '''

        try:
            receivedMsg = {
                'table': table,
                'msgId': msgId,
                'msg': msg,
                'posDup': posDup
            }
            self.messages.put(receivedMsg)
        except Queue.Full:
            print 'WARNING: message queue is full, could not store incoming message.'


    def getMessage(self, timeout=None):
        '''
            Fetches a received message, if any
            @param timeout (int) If supplied (default is None) this method will block for at most @timeout seconds, 
                if the Queue is empty. By default, this method blocks until a message becomes available
            @returns (Dict) a dictionary with the fields table (name), msgId, msg (the message fields and data)
                and posDup. This method returns None if either there's no message to be retrieved or if retrieving
                data reaches the TIMEOUT limit.
            @raises Queue.Empty: if it's not possible to retrieve a message at most after TIMEOUT seconds. This is
                caused probably because there's no message to retrieve.
        '''
        return self.messages.get(True, timeout)


    def sendMessage(self, table, msg, msgId, posDup):
        '''
            Signalizes IvCom that there's a new message to be sent. Invoking this function doesn't bring
            any guarentee that the message is sent, only that IvCom will send it when possible
            @param table (String): Table name
            @param msg (dict): dictionary with mapping table_fields -> values.
            @param msgId (int): the message sequential number
            @param posDup (bool): ?
            @raises Exception: if there's a problem dispatching the message
        '''
        self.outbound.enqueue(str(table), int(msgId), convert(msg), posDup)


    def inboundStatus(self):
        '''Returns the status of the inbound handler'''
        return self.inbound.status


    def outboundStatus(self):
        '''Returns the status of the outbound handler'''
        return self.outbound.status


    def __str__(self):
        return self.name

