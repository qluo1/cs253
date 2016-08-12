import os
import signal
import logging
import ahd
from ahd_client import getApp

import zerorpc
import gevent
import Queue

log = logging.getLogger("ahdservice")

from conf import settings

def run_as_service():
    """ """
    queue = Queue.Queue()
    def cb_notify(**kw):
        """ """
        try:
            name = kw["name"]
            msg = kw["msg"]
            queue.put(dict(name=name,msg=msg))
        except Exception,e:
            log.exception(e)

    app = getApp(settings.CFG,settings.LOG_DIR,cb_notify)
    if not app.start():
        log.error("ahd client start failed")
        return

    methods = {k : getattr(app,k) for k in dir(app) if callable(getattr(app,k)) and not k.startswith("_") and k != "stop" }

    server = zerorpc.Server(methods=methods)
    server.bind(settings.AHD_API_ENDPOINT)

    publisher = zerorpc.Publisher()
    publisher.bind(settings.AHD_PUB_ENDPOINT)


    def trigger_shutdown():
        """ shutdown event loop."""
        log.info("signal INT received, stop event loop.")

        publisher.close()
        queue.put({'exit': True})
        server.close()
        log.info("API server stopped")

        app.stop()
        log.info("ahd client stopped")


    log.info("setup signal for INT/QUIT")
    ## register signal INT/QUIT for proper shutdown
    gevent.signal(signal.SIGINT,trigger_shutdown)
    print "running [%s]..." % os.environ['SETTINGS_MODULE']

    gevent.spawn(server.run)
    while True:
        try:
            method = getattr(publisher,settings.AHD_PUB_METHOD_NAME)
            data = queue.get_nowait()
            log.info("got message: %s" % data)
            if 'exit' in data:
                break
            else:
                method(data)
        except Queue.Empty:
            gevent.sleep(0.1)

    log.info("ahdservice end normally")


if __name__ == "__main__":
    run_as_service()
