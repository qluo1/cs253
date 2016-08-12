""" FIXOrder for FIX testing.


design: FIXOrder expose simple interface for testing FIX based messages i.e. order (D,G,F) and ER (8,9)

- depends on QFIXService for sending FIX orders and receive ER messages
- all FIX messages persisted into local redis db in a separated process.
    as key: (MsgType|clOrdID|origClOrdID) for both order request and execution report.

- FIXOrder object interfact

  basic interface for send order
  1) new
  2) amend
  3) cancel

  current order status as dict in low case:
    - msgType
    - ordType
    - side
    - qty
    - price
    - symbol
    - today
    - session
    - extra

  on_message callback to update order history
  - order history captured as list of dict {clOrdId: [list of ER]}
  - _process_order implemented the core process
    1) execute pre-processor to convert order data into FIX order tags
    2) send FIX order to QFIXService
    3) wait ER from QFIXService
    4) execute post-processor to validate FIX tags
    5) return (clOrdId, [list of ER)] back to caller.

"""
import os
import copy
from pprint import pprint
import logging
## setup local python path
import config.service.cfg
from conf import settings
import gevent
import zerorpc
from datetime import datetime
from utils import SeqNumber
from functools import partial
import threading
import cStringIO

log = logging.getLogger(__name__)
##########################################
##  dynamic load customized fix module
import importlib

from tests._utils import import_proc

## fix module 
try:
    _fix_mod = importlib.import_module(settings.PYFIX_MODULE)
except Exception,e:
    log.exception(e)
    raise

class FIXMsgListener(object):
    """ internal helper."""
    def __init__(self):
        """ """
        ## 
        ## 
        self.subscriber_ = zerorpc.Subscriber(methods={'on_message': self.on_message})
        self.subscriber_.connect(settings.FIX_PUB_ENDPOINT)
        log.info("Listening to FIX message at endpoint: %s" % settings.FIX_PUB_ENDPOINT)

        ## track clOrdId: callback
        self.cache_ = {}
        self.sessions_ = []
        ## 
        self.running_ = True
        self.worker_ = gevent.spawn(self.subscriber_.run)

    def register(self,session,clOrdId):

        if (session,clOrdId) not in self.cache_:
            self.cache_[(session,clOrdId)] = gevent.queue.Queue()

        ## local cache for session filtering
        if session not in self.sessions_:
            self.sessions_.append(session)

    def on_message(self,message):
        """ handle QFIXService callback on published message."""

        try:
            assert isinstance(message,dict)
            method,session,fixmsg = message['method'],message['session'],message['message']

            if session not in self.sessions_ :
                log.debug("ignore unknown session: %s" % session)
                return
            if not settings.ACK_ER_REQUEST and method == "toApp":
                log.debug("ignore FIX request: %s" % message)
                return

            msg = _fix_mod.parse(fixmsg)[0]

            assert 'ClOrdID' in msg
            clOrdId = msg['ClOrdID']

            log.debug("clOrdId: %s, cache: %s" % (clOrdId,self.cache_.keys()))
            if (session,clOrdId) in self.cache_:
                self.cache_[(session,clOrdId)].put(msg)
                log.info("received ER: %s, %s" % (clOrdId,msg))
            else:
                log.info("ignore unknown message: %s, %s" % (clOrdId,msg))

        except Exception,e:
            log.exception(e)

    def get_message(self, session = None, cl_ord_id = None, expected_num_msg = 1):
        assert session is not None
        assert cl_ord_id is not None
        assert expected_num_msg > 0
        ret = []

        for i in range(expected_num_msg):
            try:
                msg = self.cache_[(session, cl_ord_id)].get(timeout = 10)
                ret.append(msg)
            except Exception, e:
                log.exception(e)
                raise Exception('FIX message is not received')
        return ret

    def flush_cache(self):
        self.cache_ = {}

    def stop(self):
        """ stop internal listener. """

        log.info("stop message listener.")
        if self.running_:
            self.subscriber_.close()
        self.running_ == False


##  pre-process module do customize FIXOrder to FIX mapping.
_fix_procs = []
try:
    for proc in settings.FIXORDER_MAPPING_PROCESS:
        proc = import_proc(proc)
        _fix_procs.append(proc)
except Exception,e:
    log.exception(e)
    raise

### post-process module do customized ER validation.
_er_validator = []
try:
    for proc in settings.FIXER_MAPPING_VALIDTE:
        PROC = import_proc(proc)
        _er_validator.append(proc)
except Exception,e:
    log.exception(e)
    raise

## remote qfixservice endpoint
_qfix_service = zerorpc.Client(settings.FIX_API_ENDPOINT,heartbeat=30,timeout=60)

## helper
_next_clOrdId = lambda nextId: "%s_%d:%d" % (os.getlogin(),os.getpid(),nextId)

class NoAck(Exception):
    """ not ER ack."""

class FIXOrder(object):
    """

    """
    def __init__(self, session, data, fix_listener = None, dc_listener = None):
        """ """
        assert fix_listener is not None
        self.fix_listener_ = fix_listener
        self.dc_listener_ = dc_listener
        ## session id generator
        self.session_ = session
        self.seqNum_ = SeqNumber(settings.TMP_DIR,self.session_)

        self._data = {}
        assert isinstance(data,dict)
        assert 'symbol' in data and \
               'qty' in data and \
               'side' in data

        self._data.update(data)
        if 'extra' in self._data:
            extra = self._data.pop("extra")
            assert isinstance(extra, dict)
            self._data.update(extra)

        if 'ordType' not in self._data:
            self._data['ordType'] = "Limit"

        if 'tif' not in self._data:
            self._data['tif'] = 'Day'

    @property
    def nextId(self):
        """ """
        return self.seqNum_.next

    @property
    def currentId(self):
        """ """
        return self.seqNum_.current

    def new(self,**kw):
        """
         input:
        - timeout optional with default
        - it is possible specify other fix tag,passed in as key=value
        """
        if "timeout" in kw:
            timeout = kw.pop("timeout")
        else:
            timeout = settings.WAIT_ACK

        ## additional fix tag
        if kw:
            self._data.update(kw)


        ## set clOrdId for current order
        if 'clOrdId' not in self._data:
           self._data['clOrdId'] = _next_clOrdId(self.nextId)
        ## timestamp
        self._data['transTime'] = datetime.utcnow()
        self._data['msgType'] = "NewOrderSingle"

        clOrdId = self._data['clOrdId']
        return self._process_order(clOrdId,timeout)

    def amend(self,**kw):
        """ amend qty/price

        input:
        - qty/price
        - timeout optional with default
        - it is possible to amend other fix tag,passed in as key=value
        """

        if "timeout" in kw:
            timeout = kw.pop("timeout")
        else:
            timeout = settings.WAIT_ACK

        ## amend price or qty
        assert 'qty' in kw  or 'price' in kw
        ## additional fix tag
        if kw:
            self._data.update(kw)

        self._data['msgType'] = "OrderCancelReplaceRequest"
        ###################################
        ## set new origClOrdId as previous clOrdId
        ## set new clOrdId for current order
        assert 'clOrdId' in self._data
        self._data['origClOrdId'] = self._data['clOrdId']
        self._data['clOrdId'] = _next_clOrdId(self.nextId)

        ## timestamp
        self._data['transTime'] = datetime.utcnow()

        clOrdId = self._data['clOrdId']
        ## 
        return self._process_order(clOrdId,timeout)

    def cancel(self,**kw):
        """ cancel the order.
        input:
        - timeout optional with default
        - it is possible to amend other fix tag,passed in as key=value
        """

        if "timeout" in kw:
            timeout = kw.pop("timeout")
        else:
            timeout = settings.WAIT_ACK

        ## set extra tags here
        if kw:
            self._data.update(kw)

        self._data['msgType'] = "OrderCancelRequest"
        ###################################
        ## set new origClOrdId as previous clOrdId
        ## set new clOrdId for current order
        assert 'clOrdId' in self._data
        self._data['origClOrdId'] = self._data['clOrdId']
        self._data['clOrdId'] = _next_clOrdId(self.nextId)

        ## timestamp
        self._data['transTime'] = datetime.utcnow()

        clOrdId = self._data['clOrdId']

        return self._process_order(clOrdId,timeout)

    def _process_order(self,clOrdId,timeout):
        """ process order.
        - convert internal _data into request i.e. fix order request.
        - submit fix order to qfixservice.
        - wait ack
        - do validation based on configured validator
        """

        request = copy.copy(self._data)
        for proc in _fix_procs:
            if callable(proc):
                proc(request)
        ## processed request/input 
        print " ---- fix request ----"
        pprint(request)
        ## construct / validate fix tags
        fix_order = _fix_mod.construct(request)
        ########################################
        ## register clOrdId, then submit fix order
        self.fix_listener_.register(self.session_,clOrdId)
        if self.dc_listener_ is not None:
            self.dc_listener_.register(clOrdId)

        log.info("submit order: %s" % fix_order)
        res = _qfix_service.send_fix_order(self.session_,fix_order)

        return clOrdId

    def __str__(self):
        """ return formated order."""
        buffer = cStringIO.StringIO()
        pprint("--- data ---",buffer)
        pprint(self._data,buffer)

        return buffer.getvalue()


