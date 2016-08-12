""" IvComPy handler helper. 

depend on redis for server-datastream enqueue order to track message sequence.

"""
import logging
from cfg import IvComPyClient, IvComPyDssClient, IvComPySvrDSClient,IvComPyImgLiveClient
## redis
#from cfg import rdb
# publisher 
from Publisher import OMPublisher

from utils import convert,enrich_enum

log = logging.getLogger(__name__)


__all__ = [
           'RFHandler',
           'RFHandlerSync',
           'DSSHandler',
           'ServerDatastreamHandler',
           'ImgLiveHandler',
           ]
import ctypes
import mmap
import time
import os
import struct
from datetime import date
#from gevent.queue import Queue,Empty
## gevent 1.0.2 has bug on queue.get timeout event item exist.
from Queue import Queue,Empty

from conf import settings

from utils import SeqNumber

class RFHandler(object):

    """ simple wrapper for IvComPy Request Forward handler.  """

    def __init__(self,handle,publisher,endpoint):
        """ """
        assert isinstance(handle,IvComPyClient)
        assert isinstance(publisher,OMPublisher)
        self.handle_= handle
        self.name_ = handle.requestName
        ## setup publisher
        self.publisher_ = publisher
        self.publisher_.register(self.name_,endpoint)
        ## register callback
        self.handle_.setupCallback("onMessage", self)

    def send(self,tableName,order):
        """ """
        log.info("%s: %s" % (tableName,order))
        assert order and type(order) == dict
        if self.handle_.sendClientRequestDict(tableName,convert(order)):
            return True
        err ="%s failed on sending IvCom Request [%s]" % (tableName,order)
        log.error(err)
        raise ValueError(err)

    def onMessage(self, table, msg):
        """   """
        try:
            log.debug("onMessage for %s called: %s, %s" % (self.name_, table, msg))
            self.publisher_.publish(self.name_,dict(table=table,msg=msg))
        except Exception,e:
            log.exception(e)

    def __str__(self):
        return "%s, %s" % (self.name_, self.handle_.status)

    @property
    def status(self):
        return self.handle_.status

    @property
    def name(self):
        return self.name_

from concurrent import futures
from concurrent.futures import Future

class RFHandlerSync(object):

    """ handle rf in sync fashion, no publishing need."""

    def __init__(self,handle):
        """ """
        self.results_ = Queue()
        assert isinstance(handle,IvComPyClient)
        self.handle_= handle
        self.name_ = handle.requestName
        ## register callback
        self.handle_.setupCallback("onMessage", self)

    def onMessage(self, table, msg):
        """
            can't block this thread, the same thread will be used for DSS processing
            shift responsibility of save order and lookup ER back to client!!
        """
        log.info("OM2RFHandle onMessage for %s called: %s, %s, %d" % (self.name_,table,msg, self.results_.qsize()))
        try:
            assert type(msg) == dict
            enrich_enum("CommandResponse",msg)
            ## add timeout 200ms in case ack arrived before sendOrder completed.
            deferred = self.results_.get(timeout=settings.RF_ACK_WAIT)
            deferred['future'].set_result(msg)
        except Empty, e:
            log.error("no deferred found, qsize: %d. acked: %s, ex: %s" % (self.results_.qsize(),msg, e))

    def send(self,tableName,order):
        """
        """
        log.info("%s: %s" % (tableName,order))
        assert order and type(order) == dict
        if  self.handle_.sendClientRequestDict(tableName,convert(order)):
            future = Future()
            self.results_.put(dict(order=order,future=future))
            log.debug("wait for result")
            ## raise timeout exception if no ack return
            res =  future.result(timeout=settings.RF_ACK_WAIT + 3)
            log.debug("got rsult: %s" % res)
            return res
        err ="%s failed on sending IvCom request [%s]." % (tableName,order)
        log.error(err)
        raise ValueError(err)

    def __str__(self):
        return "%s, %s" % (self.name_, self.handle_.status)

    @property
    def status(self):
        return self.handle_.status

    @property
    def name(self):
        return self.name_

class DSSHandler:

    """ DSS handler.  """

    def __init__(self,handle,publisher,endpoint):
        """ init.  """
        assert isinstance(handle,IvComPyDssClient)
        assert isinstance(publisher,OMPublisher)
        self.handle_ = handle
        self.name_ = handle.dssName
        ## internal publisher
        self.publisher_ = publisher
        self.publisher_.register(self.name_,endpoint)
        ## register callback
        self.handle_.setupCallback("onMessage", self)

    def onMessage(self, table, msg, msgId, posDup):
        """ process ivcom message, callback from PyIvComPy c++ code.  """
        ## never block this thread
        try:
            log.debug("IvCom callback table: %s, msgId: %s, posDup: %s" % (table, msgId,posDup))
            ## 
            self.publisher_.publish(self.name_,dict(table=table,msg=msg,msgId=msgId,posDup=posDup))
        except Exception,e:
            log.error("error onMessage: %s" %e)

    def __str__(self):
        return "%s, %s" % (self.name_, self.handle_.status)

    @property
    def status(self):
        return self.handle_.status

    @property
    def name(self):
        return self.name_

class ServerDatastreamHandler:

    def __init__(self,handle,publisher,endpoint):
        assert isinstance(handle, IvComPySvrDSClient)
        assert isinstance(publisher,OMPublisher)
        self.handle_ = handle
        self.name_ = handle.datastreamName
        ## internal publisher
        self.publisher_ = publisher
        self.publisher_.register(self.name_,endpoint)
        ## register calalback
        handle.setupCallback("onAck",self)

        self.seqNum_ = SeqNumber(settings.TMP_DIR,self.name_)

    def onAck(self,data):
        """ """
        try:
            log.info("%s acked data: %s" % (self.name_,data))
            assert type(data) == dict
            self.publisher_.publish(self.name_,dict(data=data))
            log.info("ack published")
        except Exception,e:
            log.error("unexpected error: %s" % e)

    @property
    def status(self):
        assert self.handle_
        return self.handle_.status

    @property
    def name(self):
        return self.name_

    def enqueuOrder(self,table,order):
        """ """
        ## remove unicode string
        order = convert(order)

        ## TODO: validating table name, order is valid 
        messageId = self.seqNum_.next
        #messageId = rdb.incr(self.name_)
        #if messageId == 1:
        #    ## a new key expiry it in 10 hours
        #    rdb.expire(self.name_,10*60*60)
        log.info("enqueue msgId: %d" % messageId)
        if self.handle_.enqueue(table,messageId,order,False):
            return messageId
        return -1

class ImgLiveHandler:

    '''
        Register and holds the callbacks needed to communicate with ImageLive implementation properly
        @author: Luiz Ribeiro (Melbourne Technology)
        @when: January, 2016
    '''

    def __init__(self,handler,publisher,endpoint):
        '''
            Creates a handler
            @param imgLiveName (string): the client's name.
            @param handler (IvComPyImgLiveClient): the underlying object created by IvComPy.
        '''

        assert isinstance(handler,IvComPyImgLiveClient)
        assert isinstance(publisher,OMPublisher)
        self.handler_ = handler
        self.name_ = handler.clientName()
        self.received = 0
        self.publisher_ = publisher
        ## test register method/endpoint
        self.publisher_.register(self.name_,endpoint)
        ## register ivcom callback.
        handler.registerCallbacks(self, "onNotify", "onEvent")

    def requestViewCreation(self, viewName, filtersList):
        '''
            Creates a new view on the corrseponding client.
            @param viewName (string): the identifying name of this view.
            @param filtersList (dict(string -> list(string))) the filter rules.
            @returns bool: True if the request was successfully sent.
        '''
        assert type(filtersList) == list
        return self.handler_.requestViewCreation(viewName, filtersList)

    def requestViewCancel(self, viewName):
        '''
            Submits to the server a request to cancel a view named @viewName.
            Notice that it may take a while until the server processes this request, thus new messages
            may arrive after sending this request.
            @param viewName (string): the name of the view to be cancelled.
            @returns bool: True if the request was successfully sent.
        '''
        return self.handler_.requestViewCancel(viewName)

    def requestViewUpdate(self, viewName, filtersList):
        '''
            Submits to the server a request to update a given view. The update procedure
            may vary from server to server. Notice that it may take a while until the server
            processes this request, thus new messages may arrive after sending this request.
            @param viewName (string): the name of the view to be updated.
            @param filtersList (dict(string -> list(string))) a list of updates (this filter
                may replace the previous one).
            @returns bool: True if the request was successfully sent.
        '''
        assert isinstance(filtersList,list)
        return self.handler_.requestViewUpdate(viewName, filtersList)

    def onNotify(self, args):
        log.debug('onNotify invoked -> %s' % args)
        self.publisher_.publish(self.name_,args)

    def onEvent(self, args):
        log.debug('onEvent invoked -> %s' % args)
        self.publisher_.publish(self.name_,args)

    @property
    def status(self):
        assert self.handler_
        return self.handler_.status

    @property
    def name(self):
        return self.name_

