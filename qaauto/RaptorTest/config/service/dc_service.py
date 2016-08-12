## setup local python path
import cfg

import quickfix
import zerorpc
import gevent
import os
import sys
import threading
import traceback
import logging
import logging.config
import Queue

from conf import settings
from singleton import SingleInstance
from myapp import Application
from Queue import PriorityQueue
from utils import Priority

logging.config.dictConfig(settings.LOG_CFG)
log = logging.getLogger(__name__)

class DCServer(object):
    def __init__(self):
        self.queue_ = Queue.Queue()
        
        log.info('DC config file: %s' % settings.DC_CFG)
        dc_settings = quickfix.SessionSettings(settings.DC_CFG)
        dc_store = quickfix.FileStoreFactory(dc_settings)
        dc_log_factory = quickfix.FileLogFactory(dc_settings)

        dc_app = Application()
        dc_app.init(self.queue_)

        self.acceptor_ = quickfix.SocketAcceptor(dc_app, dc_store, dc_settings, dc_log_factory)
        self.acceptor_.start()
        log.info('DC Acceptor started')

        self.publisher_running_ = True
        self.publisher_ = threading.Thread(name = 'DC_publisher', target = self.run)
        self.publisher_.setDaemon(True)
        self.publisher_.start()

    def run(self):
        log.info('DC Publisher started at %s...' % settings.DC_PUB_ENDPOINT)
        _publisher = zerorpc.Publisher()
        _publisher.bind(settings.DC_PUB_ENDPOINT)
        _lookup_session = dict([(v,k) for (k,v) in settings.SESSION_MAPS.iteritems()])
        
        while self.publisher_running_:
            try:
                category, order = self.queue_.get(timeout=0.1)

                order['session'] = _lookup_session[order['session']]
                if category == Priority.order:
                    raise Exception('DC session should not be sending order')
                else:
                    log.info('received DC ER <- [%s], %s' % (order['session'], order['message']))
                method = getattr(_publisher,settings.DC_PUB_METHOD_NAME)
                method(order)
            except Queue.Empty:
                gevent.sleep(0)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error = "failed on processing outgoing order: %s, tb: %s" % (e,traceback.extract_tb(exc_traceback))
                log.error(error)

        log.info('DC Publisher stopped')

        

    def shutdown(self):
        log.info('Shutting down dc_server')
        self.acceptor_.stop()
        self.publisher_running_ = False
        if self.publisher_.isAlive():
            self.publisher_.join(10)

        assert not self.publisher_.isAlive()
        log.info('dc_server is stopped...')


def run_as_service():
    import signal
    single_instance_lock = SingleInstance('dc_service')
    dc_service = DCServer()

    def trigger_shutdown():
        log.info('SIGINT received, stopping dc_service...')
        dc_service.shutdown()
        sys.exit(0)
    
    log.info('setup signal for SIGINT')
    gevent.signal(signal.SIGINT, trigger_shutdown)
    log.info('running [%s]...' % os.getenv('SETTINGS_MODULE'))
    
    while True:
        gevent.sleep(1)

if __name__ == '__main__':
    BASE_DIR = os.getenv('BASE_DIR')
    os.chdir(BASE_DIR)
    run_as_service()
