""" quickfix server.
"""
## setup local python path
import os
from Queue import PriorityQueue
import cfg
import quickfix
import gevent
import logging
import logging.config
## setup logging
from conf import settings
logging.config.dictConfig(settings.LOG_CFG)
log = logging.getLogger("qfixserver")
from singleton import SingleInstance
## fix callback applicaiton
from myapp import Application
## worker for handle request, publish fix outgoing message.
from worker import Worker

class FIXService(object):

    def __init__(self,appSettings):
        """ """
        self.work_queue_ = PriorityQueue()
        try:
            log.info("config file: %s" % appSettings.QUICKFIX_CFG)
            qfix_settings = quickfix.SessionSettings(appSettings.QUICKFIX_CFG)
            app = Application()
            app.init(self.work_queue_)
            store = quickfix.FileStoreFactory(qfix_settings)
            logFactory = quickfix.FileLogFactory(qfix_settings)
            self.client_ = quickfix.SocketInitiator(app,store,qfix_settings,logFactory)
            self.client_.start()
            log.info("client started")
            self.worker_ = Worker(self.work_queue_,appSettings)
            log.info("publisher started")
        except Exception,e:
            log.error("unexpected: %s" %e)
            print e
            raise


    def shutdown(self):
        """ """
        self.worker_.stop()
        self.client_.stop()

def run_as_service():
    """ """
    import signal
    ## instance settings
    SingleInstance("qfixserver")
    fix_service = FIXService(settings)

    def trigger_shutdown():
        """ shutdown event loop."""
        log.info("signal INT received, stop event loop.")
        fix_service.shutdown()
        log.info("QFIX server stopped")

    log.info("setup signal for INT/QUIT")
    ## register signal INT/QUIT for proper shutdown
    gevent.signal(signal.SIGINT,trigger_shutdown)
    print "running [%s]..." % os.environ['SETTINGS_MODULE']

    fix_service.worker_.start()
    log.info("qfixservice stopped cleanly")

if __name__ == "__main__":
    """ """
    run_as_service()
