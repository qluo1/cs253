""" implement ZMQ device forwarder for OM publisher.

1) expose all publishing service as a single endpoint.
2) running device in separate process.

"""
import zmq
from multiprocessing import Process
import logging
log = logging.getLogger(__name__)

def __forward(sub_endpont, pub_endpoint):
    """ internal forward function, will be blocked."""

    try:
        context = zmq.Context(1)
        private_end = context.socket(zmq.SUB)
        log.info("binding private endpoint: %s" % sub_endpont)
        private_end.bind(sub_endpont)
        private_end.setsockopt(zmq.SUBSCRIBE,"")

        public_end = context.socket(zmq.PUB)
        log.info("binding public endpoint: %s" % pub_endpoint)
        public_end.bind(pub_endpoint)

        ## froward message from private side to public side.
        zmq.device(zmq.FORWARDER,private_end,public_end)
    except Exception,e:
        print  e
        log.error("exception on forward, forward has stopped! reason: [%s]" % e)
    finally:
        private_end.close()
        public_end.close()
        context.term()
        log.info("finally closed/termed forward.")

_worker = None

def run_forward(sub_endpont,pub_endpoint):
    """ """
    global _worker
    _worker = Process(target=__forward,args=(sub_endpont,pub_endpoint))
    _worker.daemon = True
    _worker.start()
    log.info("forward worker started: %s" % _worker.pid)

def stop_forward():
    global _worker
    if _worker:
        _worker.terminate()
        log.info("forwrd worker terminated: %s"% _worker.is_alive())
    _worker = None


if __name__ == "__main__":
    """ local unit test. """

    run_forward("tcp://0.0.0.0:29009","tcp://0.0.0.0:29010")

