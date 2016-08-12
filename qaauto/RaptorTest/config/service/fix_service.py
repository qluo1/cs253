""" quickfix server.
"""
## setup local python path
import cfg
import os
import Queue
import quickfix
import gevent
import logging
import logging.config

## setup logging
from conf import settings
from singleton import SingleInstance
## fix callback applicaiton
from myapp import Application
## worker for handle request, publish fix outgoing message.
from worker import Worker

logging.config.dictConfig(settings.LOG_CFG)
log = logging.getLogger(__name__)

class FIXServer(object):

    def __init__(self,appSettings):
        """ """
        self.work_queue_ = Queue.Queue()
        try:
            ## Initizlize FIX session
            log.info("config file: %s" % appSettings.FIX_CFG)

            fix_settings = quickfix.SessionSettings(appSettings.FIX_CFG)
            fix_app = Application()
            fix_app.init(self.work_queue_)
            fix_store = quickfix.FileStoreFactory(fix_settings)
            fix_logFactory = quickfix.FileLogFactory(fix_settings)
            self.client_ = quickfix.SocketInitiator(fix_app,fix_store,fix_settings,fix_logFactory)
            self.client_.start()

            ## Start worker
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
    single_instance_lock = SingleInstance("fix_service")
    fix_service = FIXServer(settings)

    def trigger_shutdown():
        """ shutdown event loop."""
        log.info("signal INT received, stop event loop.")
        fix_service.shutdown()
        log.info("QFIX server stopped")

    log.info("setup signal for INT/QUIT")
    ## register signal INT/QUIT for proper shutdown
    gevent.signal(signal.SIGINT,trigger_shutdown)
    log.info("running [%s]..." % os.environ['SETTINGS_MODULE'])

    fix_service.worker_.start()
    log.info("qfixservice stopped cleanly")

if __name__ == "__main__":
    """ """
    import os
    BASE_DIR = os.getenv("BASE_DIR")
    os.chdir(BASE_DIR)
    run_as_service()
