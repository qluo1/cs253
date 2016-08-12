"""
"""
import sys
import os
import time
import logging
import Queue
import threading
import signal
## setup local env
import localcfg
from conf import settings
import gevent
import zerorpc

import logging.config
##
logging.config.dictConfig(settings.LOG_CFG)
log = logging.getLogger("omaservice")


import OmaClientPy as OmaPy
## setup gslog
if not OmaPy.setuplog(settings.GSLOGCFG,"omaservice",settings.LOG_DIR):
    raise EnvironmentError("failed to setup gslog")

class OmaPyClient(object):

    """ a python wrapper for underlying oma session.

    underlying oma session has a running thread to manage the session.

    the c++ thread shall callback for any nvp message in raw format..

    """

    def __init__(self,oma_cfg,work_queue):
        """ init a oma client session. """
        assert isinstance(oma_cfg,dict)
        assert 'host' in oma_cfg and 'service' in oma_cfg
        assert 'user' in oma_cfg and 'pwd' in oma_cfg
        assert 'view' in oma_cfg and 'seqfile' in oma_cfg

        self.work_queue_ = work_queue

        self.session_ = OmaPy.OmaClientManager(oma_cfg['seqfile'])

        self.session_.registerCallback("callback",self)

        res = self.session_.logon(
                oma_cfg['host'],
                oma_cfg['service'],
                oma_cfg['user'],
                oma_cfg['pwd'],
                oma_cfg['view']
                )
        self.running_ = True
        self.name_ = oma_cfg['service']

        if res:
            log.info("connected oma: %s" % oma_cfg)
        else:
            raise ValueError("failed to connect oma: %s" % oma_cfg)

    def callback(self,data):
        """ """
        try:
            log.debug("callback: %s" % data)
            self.work_queue_.put(data)
        except Exception,e:
            log.exception(e)

    @property
    def name(self):
        return self.name_
    @property
    def running(self):
        return self.running_

    def stop(self):
        if self.running_:
            self.session_.stop()
            del self.session_
            log.info("stopped oma.client.py: %s" % self.name)
            self.running_ = False

    def send_transaction(self,msg,**kw):
        """ send nvp direct."""
        ### TODO:internal validation
        return self.session_.send(msg)


class OmaPyServices(object):
    """ manager all configured oma sessions.

    internal  thread publishing all subscribed oma/nvp messages to zerorpc.
    """

    def __init__(self,settings):
        """ """
        self.clients_ = []

        self.queue_ = Queue.Queue()
        assert isinstance(settings.OMA_SVRS,dict)
        for k,cfg in settings.OMA_SVRS.iteritems():
            if cfg['active'] == True:
                try:
                    print("process oma: [%s]" % k)
                    client = OmaPyClient(cfg,self.queue_)
                    self.clients_.append(client)
                    print("connected to [%s]" % k )
                except Exception,e:
                    print("connect oma: [%s] failed: %s" % (k,e))
                    log.exception(e)

        self.settings_ = settings
        self.running_ = False
        self.worker_ = threading.Thread(target=self._run)

    def start(self):
        """ """
        assert self.running_ ==  False
        self.running_ = True
        ## kick off running worker
        self.worker_.start()

    def _run(self):
        """ internal worker. publish out nvp as raw data via zerorpc."""

        publisher = zerorpc.Publisher()
        publisher.bind(self.settings_.PUB_ENDPOINT)
        log.info("publising nvp data to : %s" % self.settings_.PUB_ENDPOINT)
        while self.running_:
            try:
                data = self.queue_.get(timeout=1)

                session = data["serverName"]
                nvp = data["nvp"]
                opType = data["opType"]
                tag = data["tag"]
                method = data["method"]

                log.info("got data for session: %s, size: %d, tag: %s" % (session,self.queue_.qsize(), tag))
                ###############################
                ## publish message out
                method = getattr(publisher,session)
                method(data)
            except Queue.Empty:
                pass
            except Exception,e:
                log.exception(e)

        publisher.close()
        log.info("worker exit on stop: %s" % self.running_)

    def stop(self):
        """ """

        for client in self.clients_:
            if client.running:
                log.info("stop session: %s" % client.name)
                client.stop()
                ## wait for oma internal thread shutdown cleanly.
                #gevent.sleep(50)

        ##
        log.info("stop internal worker")
        self.running_ = False
        ## wait for runner to stop
        self.worker_.join()
        log.info("shutdown completed")

    def send_nvp(self,session, msg):
        """ """
        if session not in [c.name for c in self.clients_]:
            raise ValueError("session [%s] not found in %s" % (session, [c.name for c in self.clients_]))

        client = [c for c in self.clients_ if c.name == session][0]
        return client.send_transaction(msg)

from omaTracker import NVPTracker
from omaGraph import OmaRegister
from singleton import SingleInstance
def run_as_service():

    me = SingleInstance("omaPyService")
    ## in-memory oma order graph
    register = OmaRegister()
    ## load current database snapshot
    log.info("loading in-memory snapshot from rdb")
    register._load_from_redis()
    ## setup listener for nvp
    tracker = NVPTracker(settings,localcfg.rdb,register)
    ## set subscription for active oma
    methods = {}
    for name,item in settings.OMA_SVRS.iteritems():
        if item['active']:
            methods[name] = tracker._on_nvp
    _subscriber = zerorpc.Subscriber(methods=methods)
    _subscriber.connect(settings.PUB_ENDPOINT)
    gevent.spawn(_subscriber.run)
    gevent.sleep(1)
    ## start oma live feed
    service = OmaPyServices(settings)
    service.start()
    log.info("oma nvp live/subscription started")

    try:
        ## send_nvp
        rpc_methods = {'send_nvp': service.send_nvp,}
        ## graph rpc method
        graph_methods = {k: getattr(register,k) for k in dir(register) if not k.startswith("_") and callable(getattr(register,k))}
        rpc_methods.update(graph_methods)
        ## setup OMA API service
        s = zerorpc.Server(methods=rpc_methods)
        log.info("start OmaRegister at: %s " % settings.OMA_API_URL)
        s.bind(settings.OMA_API_URL)

        print "oma/nvp service started."
        def trigger_shutdown():
            """ shutdown event loop."""
            print "shutdown called."
            log.info("signal INT received, stop event loop.")
            service.stop()
            _subscriber.stop()

            log.info("oma service ended")
            sys.exit(0)

        log.info("setup signal for INT/QUIT")
        ## register signal INT/QUIT for proper shutdown
        gevent.signal(signal.SIGINT,trigger_shutdown)
        s.run()

    except Exception,e:
        log.exception(e)

if __name__ == "__main__":
    run_as_service()
