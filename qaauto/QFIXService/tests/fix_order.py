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
import cfg
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

from _utils import active_wait,import_proc

## fix module 
try:
    _fix_mod = importlib.import_module(settings.PYFIX_MODULE)
except Exception,e:
    log.exception(e)
    raise

class MessageListener(object):
    """ internal helper."""
    def __init__(self):
        """ """
        ## 
        ## 
        self.subscriber_ = zerorpc.Subscriber(methods={'on_message': self.on_message})
        self.subscriber_.connect(settings.PUBSUB_ENDPOINT)
        log.info("listening: %s" % settings.PUBSUB_ENDPOINT)
        ## track clOrdId: callback
        self.cache_ = {}
        self.sessions_ = []
        ## 
        self.running_ = True
        self.worker_ = gevent.spawn(self.subscriber_.run)

    def register(self,session,clOrdId,func):
        """ register a clOrdId and callback. """

        assert callable(func)

        if (session,clOrdId) not in self.cache_:
            self.cache_[(session,clOrdId)] = func
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
            clOrdId = msg['ClOrdID']
            msgType = msg['MsgType']

            log.debug("clOrdId: %s, cache: %s" % (clOrdId,self.cache_.keys()))
            if (session,clOrdId) in self.cache_:
                self.cache_[(session,clOrdId)](session,clOrdId,msg)
                log.info("received ER: %s, %s" % (clOrdId,msg))
            else:
                log.info("ignore unknown message: %s, %s" % (clOrdId,msg))

        except Exception,e:
            log.exception(e)

    def stop(self):
        """ stop internal listener. """

        log.info("stop message listener.")
        if self.running_:
            self.subscriber_.close()
        self.running_ == False


## remote qfixservice endpoint
_qfix_service = zerorpc.Client(settings.ORDER_API_ENDPOINT,heartbeat=30,timeout=60)

## helper
_next_clOrdId = lambda nextId: "%s_%d:%d" % (os.getlogin(),os.getpid(),nextId)

class NoAck(Exception):
    """ not ER ack."""

class FIXOrder(object):
    """

    """

    ## shared  for all test order.
    _tracker = MessageListener()

    def __init__(self,session,data):
        """ """
        ## session id generator
        self.session_ = session
        self.seqNum_ = SeqNumber(settings.TMP_DIR,self.session_)

        self._data = {}
        assert isinstance(data,dict)
        assert 'symbol' in data and \
               'price' in data and \
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
        ## track order history
        self.hist_ = {}
        ## wait for order ack.
        self.trigger_ = {}
        ################################################
        ## check if should override for the test session.
        self._fix_procs = []
        try:
            if self.session_ in settings.FIXORDER_MAPPING_PROCESS:
                ## reset fix process
                for proc in settings.FIXORDER_MAPPING_PROCESS[self.session_]:
                    proc = import_proc(proc)
                    self._fix_procs.append(proc)
            else:
                ##  pre-process module do customize FIXOrder to FIX mapping.
                for proc in settings.FIXORDER_MAPPING_PROCESS['default']:
                    proc = import_proc(proc)
                    self._fix_procs.append(proc)
        except Exception,e:
            log.exception(e)
            raise

        ### post-process module do customized ER validation.
        self._er_validator = []
        try:
            if self.session_ in settings.FIXER_MAPPING_VALIDTE:
                for proc in settings.FIXER_MAPPING_VALIDTE[self.session_]:
                    PROC = import_proc(proc)
                    self._er_validator.append(proc)

            else:
                for proc in settings.FIXER_MAPPING_VALIDTE['default']:
                    PROC = import_proc(proc)
                    self._er_validator.append(proc)
        except Exception,e:
            log.exception(e)
            raise

    @property
    def session_status(self):
        """
        """
        assert self.session_
        res = _qfix_service.check_session_status(self.session_)
        assert res
        return res

    @property
    def nextId(self):
        """ """
        return self.seqNum_.next

    @property
    def currentId(self):
        """ """
        return self.seqNum_.current

    def _update(self,session,clOrdId,message):
        """
        callback from MessageListener i.e. tracker.
        - update order history

        """
        assert session == self.session_
        if  clOrdId in self.hist_:
            self.hist_[clOrdId].append(message)
            self.trigger_[clOrdId].set()

    def new(self,**kw):
        """
         input:
        - timeout optional with default
        - expected_num_msg with default 1
        - it is possible specify other fix tag,passed in as key=value
        """
        if "timeout" in kw:
            timeout = kw.pop("timeout")
        else:
            timeout = settings.WAIT_ACK

        if "expected_num_msg" in kw:
            expected_num_msg = kw.pop("expected_num_msg")
        else:
            expected_num_msg = 1

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
        self.hist_[clOrdId] = []
        return self._process_order(clOrdId,timeout,expected_num_msg)

    def amend(self,**kw):
        """ amend qty/price

        input:
        - qty/price
        - timeout optional with default
        - expected_num_msg with default 1
        - it is possible to amend other fix tag,passed in as key=value
        """

        if "timeout" in kw:
            timeout = kw.pop("timeout")
        else:
            timeout = settings.WAIT_ACK

        if "expected_num_msg" in kw:
            expected_num_msg = kw.pop("expected_num_msg")
        else:
            expected_num_msg = 1

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
        assert clOrdId not in self.hist_
        self.hist_[clOrdId] = []
        ## 
        return self._process_order(clOrdId,timeout,expected_num_msg)

    def cancel(self,**kw):
        """ cancel the order.
        input:
        - timeout optional with default
        - expected_num_msg with default 1
        - it is possible to amend other fix tag,passed in as key=value
        """

        if "timeout" in kw:
            timeout = kw.pop("timeout")
        else:
            timeout = settings.WAIT_ACK

        if "expected_num_msg" in kw:
            expected_num_msg = kw.pop("expected_num_msg")
        else:
            expected_num_msg = 1

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
        assert clOrdId not in self.hist_
        self.hist_[clOrdId] = []

        return self._process_order(clOrdId,timeout,expected_num_msg)

    def _process_order(self,clOrdId,timeout,expected_num_msg):
        """ process order.
        - convert internal _data into request i.e. fix order request.
        - submit fix order to qfixservice.
        - wait ack
        - do validation based on configured validator
        """

        request = copy.copy(self._data)
        for proc in self._fix_procs:
            if callable(proc):
                proc(request)
        ## processed request/input 
        log.info("FIX request: %s" % request)
        print " ---- fix request ----"
        pprint(request)
        ## construct / validate fix tags
        fix_order = _fix_mod.construct(request)
        ########################################
        ## register clOrdId, then submit fix order
        self._tracker.register(self.session_,clOrdId,self._update)

        self.trigger_[clOrdId] = gevent.event.Event()
        log.info("submit order: %s" % fix_order)
        res = _qfix_service.send_fix_order(self.session_,fix_order)
        self.trigger_[clOrdId].wait(timeout)

        ## validate ack received.
        if  len(self.hist_[clOrdId]) <= 0:
            raise NoAck()
        ## wait more than one message
        active_wait(lambda: len(self.hist_[clOrdId]) == expected_num_msg,timeout=timeout)
        ## validate er
        for proc in self._er_validator:
            for er in self.hist_[clOrdId]:
                p = import_proc(proc)
                if callable(p):
                    p(er)
        print " --- ER: %s ---" % clOrdId
        pprint(self.hist_[clOrdId])
        ## return clOrdId, ER history
        return clOrdId,self.hist_[clOrdId]


    def __str__(self):
        """ return formated order."""
        buffer = cStringIO.StringIO()
        pprint("--- data ---",buffer)
        pprint(self._data,buffer)
        pprint("--- hist ---", buffer)
        pprint(self.hist_,buffer)

        return buffer.getvalue()


