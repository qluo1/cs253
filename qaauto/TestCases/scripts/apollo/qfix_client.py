import os
import logging
import cfg
from conf import settings
import gevent
import zerorpc
import pyfix42
from datetime import datetime
from utils import SeqNumber


WAIT_ACK = 60

log = logging.getLogger(__name__)

class MessageListener(object):
    """ internal helper."""
    def __init__(self,client):
        """ """
        self.client_ = client
    def on_message(self,message):
        """ """
        try:
            self.client_.on_message(message)
        except Exception,e:
            log.error("on_message failed: %s" % e)
            print e

class QFIX_ClientSession():
    """ qfix session for test client.


    - send fix order.
    - recv er and store in internal registery.
    - wait for ack
    """
    api_ = zerorpc.Client(settings.QFIX_ORDER_ENDPOINT)
    ## internal cache track for interested clOrdId
    register_ = {}

    def __init__(self,session):
        """
        """
        self.session_ = session

        self.seqNum_ = SeqNumber(cfg.TMP_DIR,self.session_)

        self.trigger_ = gevent.event.Event()
        ## listener
        listener = MessageListener(self)
        self.subscriber = zerorpc.Subscriber(listener)
        self.subscriber.connect(settings.QFIX_PUBSUB_ENDPOINT)
        gevent.spawn(self.subscriber.run)

    def on_message(self,message):
        """
        """
        msg = pyfix42.parse(message['message'])[0]
        clOrdId = msg['ClOrdID']
        msgType = msg['MsgType']

        if msgType in ("ExecutionReport","OrderCancelReject"):
            if clOrdId in self.register_:
                log.info("==> clOrdId: %s, %s, %s" % (clOrdId ,msg, self.register_.keys()))
                self.register_[clOrdId].append(msg)
            else:
                log.warn("received unknown clOrdId: %s, msg:%s" % (clOrdId,msg))
            self.trigger_.set()
        elif msgType in ("NewOrderSingle","OrderCancelReplaceRequest","OrderCancelRequest"):
            log.info("<== %s, %s" %(msgType, clOrdId))
            log.debug("\t<== :%s" % msg)
        else:
            log.error("unhandled message: %s" % msg)

    def check_session(self):
        """
        """
        res = self.api_.check_session_status("APOLLO.TEST")
        assert res
        return res

    def send_apollo_order(self,order,**kw):
        """ """
        assert isinstance(order,dict)
        assert 'ClOrdID' in order
        clOrdId = order['ClOrdID']
        timeout = kw.get("timeout",WAIT_ACK)
        fix_order =pyfix42.construct(order)
        self.register_[clOrdId] = []
        res = self.api_.send_fix_order(self.session_,fix_order)
        self.trigger_.wait(timeout)
        return res

    def get_results(self,clOrdId):
        """ """
        ## reset trigger 
        if self.trigger_.isSet():
            self.trigger_.clear()
        else:
            ## triggered already, additional wait for potential more ER(s).
            gevent.sleep(0.1)

        if clOrdId in self.register_.keys():
            log.info("get result for clOrdId: %s, %s" % (clOrdId, self.register_.keys()))
            return self.register_[clOrdId]
        ## 
        raise ValueError("clOrdId not registered or already extracted: %s, %s" % (clOrdId,res))

    def reset(self):
        """ clear internal cache."""

        for k in self.register_.keys():
            self.register_.pop(k)

    @property
    def nextId(self):
        """ """
        return self.seqNum_.next

    @property
    def currentId(self):
        """ """
        return self.seqNum_.current

    @property
    def nextClOrdID(self):
        """ """
        return "%s_%d:%d" % (os.getlogin(),os.getpid(),self.nextId)

    def close(self):
        """ """
        self.api_.close()
        self.subscriber.close()
        self.register_= {}

