""" For testing DC Session

"""

import logging
## setup local python path
import config.service.cfg
from conf import settings
import gevent
import zerorpc
from time import sleep

log = logging.getLogger(__name__)
##########################################
##  dynamic load customized fix module
import importlib

from tests._utils import active_wait,import_proc

## fix module 
try:
    _fix_mod = importlib.import_module(settings.PYFIX_MODULE)
except Exception,e:
    log.exception(e)
    raise

class DCMsgListener(object):
    """ internal helper."""
    def __init__(self, session):
        """ """
        self.subscriber_ = zerorpc.Subscriber(methods={'on_dc_message': self.on_dc_message})
        self.subscriber_.connect(settings.DC_PUB_ENDPOINT)
        log.info("listening: %s" % settings.DC_PUB_ENDPOINT)

        self.session_ = session
        self.running_ = True
        self.cache_ = {}
        self.worker_ = gevent.spawn(self.subscriber_.run)

    def on_dc_message(self,message):
        """ handle QFIXService callback on published message."""

        try:
            assert isinstance(message,dict)
            method,session,fixmsg = message['method'],message['session'],message['message']

            if self.session_ is not None and session != self.session_ :
                log.debug("ignore unknown session: %s" % session)
                return
            if not settings.ACK_ER_REQUEST and method == "toApp":
                log.debug("ignore FIX request: %s" % message)
                return

            msg = _fix_mod.parse(fixmsg)[0]

            assert 'ClOrdID' in msg
            if msg['ClOrdID'] not in self.cache_:
                self.cache_[msg['ClOrdID']] = gevent.queue.Queue()
            self.cache_[msg['ClOrdID']].put(msg)
            log.info("received DC ER %s: %s" % (msg['ClOrdID'], msg))

        except Exception,e:
            log.exception(e)

    def get_dc_message(self, cl_ord_id=None, expected_num_msg=1):
        assert cl_ord_id is not None
        assert expected_num_msg > 0
        ret = []

        for i in range(expected_num_msg):
            try:
                msg = self.cache_[cl_ord_id].get(timeout=10)
                ret.append(msg)
            except Exception,e:
                log.exception(e)
                raise Exception('DC message is not received!')
        return ret

    def register(self, cl_ord_id):
        if cl_ord_id not in self.cache_:
            self.cache_[cl_ord_id] = gevent.queue.Queue()

    def flush_cache(self):
        self.cache_ = {} 

    def stop(self):
        """ stop internal listener. """

        log.info("stop message listener.")
        if self.running_:
            self.subscriber_.close()
        self.running_ == False

