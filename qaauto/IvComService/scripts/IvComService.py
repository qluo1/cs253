""" IvComPyServer expose IvCom as zerorpc API .


"""
import os
import sys
from datetime import datetime
import traceback
import time
import imp
#import logging.config
from threading import Thread
import itertools
##
from cfg import IvComPyManager
from cfg import json
from utils import lookup_enum, convert, enrich_enum
## local project settings
from cfg import settings
## run service
import zerorpc
import gevent
import signal
## setup logging
import logging
import logging.config
## setup logging
logging.config.dictConfig(settings.LOGGING)
log = logging.getLogger(__file__)

from Forwarder import run_forward, stop_forward
from Publisher import OMPublisher

from IvComPyHandler import *

class IvComService:
    """
        IvComServer handle both dss and RF(s)
    """

    def __init__(self):
        """
        """
        log.info('Using config log file @ %s' % settings.GSLOGCFG)
        log.info('Using config nodes file @ %s' % settings.IVPYCFG)
        log.info('Logging @ %s/%s' % (settings.LOG_DIR, settings.GSLOGNAME))
        self.mgr_ = IvComPyManager()

        config_file = settings.IVPYCFG
        config_module = config_file.split(os.path.sep)[-1].split(".")[0]

        config_mod = imp.load_source(config_module,config_file)
        config_data = config_mod.configure()

        if not self.mgr_.setuplog(settings.GSLOGCFG, settings.GSLOGNAME, settings.LOG_DIR):
            raise EnvironmentError("setup gslog failed")

        if not self.mgr_.initJson(str(config_data)):
            raise EnvironmentError("init ivcommanager failed for :%s" % settings.IVPYCFG)

        ## run fowrard
        run_forward(settings.PRIVATE_SUB_ENDPOINT, settings.PUBLIC_PUB_ENDPOINT)
        ## setup om publisher
        self.publisher_ = OMPublisher()
        self.publisher_.start()

        endpoint_map = settings.PUB_ENDPOINT_MAP
        #####################################################
        ### client request
        self.rfHandlers = {}
        if 'client-request-managers' in config_data:
            ## setup client
            requestNames = self.mgr_.clientRequestNames
            if len(requestNames) == 0: raise EnvironmentError("No request configured")

            log.info("setup rf handlers")
            for name in requestNames:
                client = self.mgr_.getClientRequest(name)
                if name in endpoint_map:
                    log.info("rf registering %s as ASYNC." % name)
                    self.rfHandlers[name] = RFHandler(client,
                                                      self.publisher_,
                                                      endpoint_map[name])
                else:
                    log.info("rf registering :%s as SYNC." % name)
                    self.rfHandlers[name] = RFHandlerSync(client)

                assert self.rfHandlers[name].name == name

        #######################################################
        ### client-datastream
        self.dssHandlers = {}
        if 'client-datastreams' in config_data:
            # get client datastreams
            dssNames = self.mgr_.dssNames
            if len(dssNames) == 0: raise EnvironmentError("No dss configured")

            log.info("setup dss handlers")
            for name in dssNames:
                if name in endpoint_map:
                    log.info("dss registering %s" % name)
                    client = self.mgr_.getDss(name)
                    self.dssHandlers[name] = DSSHandler(client,
                                                        self.publisher_,
                                                        endpoint_map[name])
                    assert self.dssHandlers[name].name == name

        ########################################################
        ### server-datastream
        self.datastreamServers = {}
        if 'server-datastreams' in config_data:
            ## setup server datastream client
            serverDatastreamNames = self.mgr_.serverDatastreamNames
            if len(serverDatastreamNames) > 0 :
                for name in serverDatastreamNames:
                    if name in endpoint_map:
                        self.datastreamServers[name] = ServerDatastreamHandler(self.mgr_.getServerDatastreamClient(name),
                                                                               self.publisher_,
                                                                               endpoint_map[name])
                        assert self.datastreamServers[name].name == name

        #########################################################
        ### image-live-client
        self.imgLiveHandlers = {}
        if 'image-live-clients' in config_data:
            # get imgLive names
            imgLiveNames = self.mgr_.ImageLiveClientNames
            if len(imgLiveNames) == 0: raise EnvironmentError("No image live clients configured.")

            log.info("setup image live client handlers")
            for name in imgLiveNames:
                if name in endpoint_map:
                    log.info("registering imgLive client %s." % name)
                    client = self.mgr_.getImageLiveClient(name)
                    self.imgLiveHandlers[name] = ImgLiveHandler(client,
                                                                self.publisher_,
                                                                endpoint_map[name])
                    assert self.imgLiveHandlers[name].name == name


        ## kick off manager
        self.runner_ = Thread(target=self.mgr_.run)
        self.runner_.start()
        if not self.runner_.isAlive():
            log.error("run IvComPyManager failed, check ivcom log")
            exit(1)
        self.running_ = True
        # wait for become available
        log.info("IvComManager started")

    def shutdown(self):
        """
        """
        log.info("shutdown called")
        if self.mgr_ and self.running_:
            self.running_ = False
            self.mgr_.stop()
            ## wait internal thread finish
            self.runner_.join()
            log.info("IvComManager finished")
        ## shutdown publisher
        if self.publisher_.isAlive():
            self.publisher_.stop()
            log.info("publisher stopped")
        ## stop forward process
        stop_forward()

    def list_sessions(self):
        """ list session names."""
        return [i for i in itertools.chain(self.rfHandlers, self.dssHandlers, self.datastreamServers, self.imgLiveHandlers)]

    def handle_status(self):
        """
        """
        return [{'session': k, 'status' : v.status} for (k, v) in itertools.chain(
                                             self.rfHandlers.items(),
                                             self.dssHandlers.items(),
                                             self.datastreamServers.items(),
                                             self.imgLiveHandlers.items(),
                                             )]

    def getRFHandler(self, name):
        """
        """
        if name in self.rfHandlers.keys():
            return self.rfHandlers[name]

    def getSvrDatastreamClient(self,name):
        """
        """
        if name in self.datastreamServers.keys():
            return self.datastreamServers[name]

    def getImgLiveHandler(self,name):
        """
        """
        if name in self.imgLiveHandlers.keys():
            return self.imgLiveHandlers[name]

class APIServer(object):

    """ RPC API via rpc call.
    each call register a server object reference
    - list sessions
    - handle_status
    - new order
    """

    def __init__(self,service):
        """ initialize with a MyIvComServer instance """
        assert isinstance(service, IvComService)
        self.service_ = service

    def list_sessions(self):
        """ return internal server handlers. """
        return self.service_.list_sessions()

    def handle_status(self):
        """ return internal server handlers status. """
        return self.service_.handle_status()

    def send_rf_request(self,session,table,message):
        """ sending raw rf request.

        direct sending ivcom message via rf without store internal order state.
        input: tableName, pydict message
        """
        log.info("API send raw rf request for %s, msg: %s, %s" % (table,message,type(message)))
        assert isinstance(message,dict)
        assert session in self.service_.list_sessions(), "%s, %s" % (session, self.service_.list_sessions())

        rfHandler = self.service_.getRFHandler(session)
        assert rfHandler
        return rfHandler.send(table,message)

    def enqueue_message(self,session,table,msg):
        """ sending order via serverDatastreamClient session. return ack.
        """
        log.info("API enqueue message %s, %s" % (table,msg))
        handler = self.service_.getSvrDatastreamClient(session)
        if not handler:
            raise ValueError("session name not valid: %s" % session)
        if handler.status != "Servicing":
            raise ValueError("session %s not in right status:%s, expect Servicing." % ( session, handler.status))
        messageId = handler.enqueuOrder(table,msg)
        if messageId != -1:
            return {'ack': 'ok', 'messageId': messageId}
        else:
            err = "enqueue enqueue message failed"
            log.error(err)
            ## return ack or internal exception
            raise ValueError(err)

    ## expose imagelive
    def createImgLiveView(self, providerName, viewName, listFilters):
        '''
            Sends a request to create a Image Live view.
            @param clientName (string): the name of the provider
            @param viewName (string): the name of the view to be created
            @param listFilters (dict(string -> list(string))): set of filters that when fulfilled trigger this view
            @returns bool: True if the request was sent successfully
            @raises ValueError: if this provider doesn't exist
            @author: Luiz Ribeiro (Melbourne Technology)
        '''
        imgLiveHandler = None

        log.info( 'received create %s - %s - %s' % (providerName, viewName, listFilters))

        try:
            imgLiveHandler = self.service_.imgLiveHandlers[providerName]
        except:
            raise ValueError('Client not registered: %s, handlers: %s' % (providerName, self.service_.imgLiveHandlers))

        return imgLiveHandler.requestViewCreation(viewName, listFilters)


    def updateImgLiveView(self, providerName, viewName, listFilters):
        '''
            Sends a request to update a given a Image Live view. Notice that how
            updating works may change from server to server. It may take a while for changes take effect
            @param clientName (string): the name of the provider
            @param viewName (string): the name of the view to be created
            @param listFilters (dict(string -> list(string))): set of filters to update the current view definition
            @returns bool: True if the request was sent successfully
            @raises ValueError: if this provider doesn't exist
            @author: Luiz Ribeiro (Melbourne Technology)
        '''
        imgLiveHandler = None

        log.info( 'received update %s - %s - %s' % (providerName, viewName, listFilters))

        try:
            imgLiveHandler = self.server_.imgLiveHandlers[providerName]
        except:
            raise ValueError('Client not registered: %s' % providerName)

        log.info('sent update request')
        result = imgLiveHandler.requestViewUpdate(viewName, listFilters)
        return result


    def cancelImgLiveView(self, providerName, viewName):
        '''
            Sends a request to remove a given view from the server. It may take a while for changes take effect
            @param clientName (string): the name of the provider
            @param viewName (string): the name of the view to be created
            @param listFilters (dict(string -> list(string))): set of filters to update the current view definition
            @returns bool: True if the request was sent successfully
            @raises ValueError: if this provider doesn't exist
            @author: Luiz Ribeiro (Melbourne Technology)
        '''
        imgLiveHandler = None

        log.info("received cancel imageLiveView %s - %s " % (providerName,viewName))

        try:
            imgLiveHandler = self.service_.imgLiveHandlers[providerName]
        except:
            raise ValueError('Client not registered :%s' % providerName)

        return imgLiveHandler.requestViewCancel(viewName)

def run_as_service():
    """ """

    try:
        from singleton import SingleInstance
        me = SingleInstance(os.environ['SETTINGS_MODULE'])
        server = IvComService()
        log.info("IvComService initialised.")
        s = zerorpc.Server(APIServer(server))
        log.info("start OM2API at: %s " % settings.ORDER_API_URL)
        s.bind(settings.ORDER_API_URL)
        def trigger_shutdown():
            """ shutdown event loop."""
            log.info("signal INT received, stop event loop.")
            s.stop()
            log.info("RPC server stopped")
            server.shutdown()
            log.info("api service stopped")

        log.info("setup signal for INT/QUIT")
        ## register signal INT/QUIT for proper shutdown
        gevent.signal(signal.SIGINT,trigger_shutdown)
        print "running"
        s.run()
        log.info("finished cleanly.")
    except Exception,e:
        error = "run failed on exception: %s" % e
        print error
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error("%s, tb: %s" % (error, traceback.extract_tb(exc_traceback)))

if __name__ == "__main__":
    """ """
    run_as_service()

