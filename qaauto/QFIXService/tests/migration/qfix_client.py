import logging
import cfg
from conf import settings
import gevent
import zerorpc
import pyfix42
from datetime import datetime
from utils import SeqNumber
from functools import partial

## up to 5 mins
WAIT_ACK = 5 * 60

log = logging.getLogger(__name__)

def active_wait(predicate,**kw):
    """ """
    assert callable(predicate)
    timeout = kw.get("timeout",5)
    raise_timeout = kw.get("raise_timeout",False)

    start = datetime.now()
    while True:
        if predicate():
            break
        else:
            now = datetime.now()
            if (now - start).total_seconds() < timeout:
                gevent.sleep(0.01)
            else:
                if raise_timeout:
                    raise TimeoutError("timeout: %d for %s" % (timeout,predicate()))
                return predicate()

    return True
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
            print e

class QFIX_ClientSession():
    """ qfix session for test client.


    - send fix order.
    - recv er and store in internal registery.
    - wait for ack
    """
    log.info("order_request: %s" % settings.ORDER_API_ENDPOINT)
    api_ = zerorpc.Client(settings.ORDER_API_ENDPOINT,heartbeat=30,timeout=60)
    ## internal cache track for interested clOrdId
    register_ = {}
    trigger_ = {}

    def __init__(self,session):
        """
        """
        self.session_ = session

        self.seqNum_ = SeqNumber(settings.TMP_DIR,self.session_)

        ## listener
        listener = MessageListener(self)
        self.subscriber = zerorpc.Subscriber(listener)
        self.subscriber.connect(settings.PUBSUB_ENDPOINT)
        log.info("listening: %s" % settings.PUBSUB_ENDPOINT)
        gevent.spawn(self.subscriber.run)

    def on_message(self,message):
        """ callback from remote publisher."""
        try:

            msg = pyfix42.parse(message['message'])[0]
            clOrdId = msg['ClOrdID']
            msgType = msg['MsgType']

            if msgType in ("ExecutionReport","OrderCancelReject"):
                if clOrdId in self.register_:
                    log.info("==> clOrdId: %s, %s, %s" % (clOrdId ,msg, len(self.register_.keys())))
                    self.register_[clOrdId].append(msg)
                    self.trigger_[clOrdId].set()
                else:
                    log.debug("received unknown clOrdId: %s, msg:%s" % (clOrdId,msg))

            elif msgType in ("NewOrderSingle","OrderCancelReplaceRequest","OrderCancelRequest"):
                log.info("<== %s, %s" %(msgType, clOrdId))
                log.debug("\t<== :%s" % msg)
            else:
                log.error("unhandled message: %s" % msg)

        except Exception,e:
            log.exception(e)

    def check_session(self):
        """
        """
        res = self.api_.check_session_status(self.session_)
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
        self.trigger_[clOrdId] = gevent.event.Event()
        #import pdb;pdb.set_trace()
        res = self.api_.send_fix_order(self.session_,fix_order)
        self.trigger_[clOrdId].wait(timeout)
        assert res

    def get_results(self,clOrdId,**kw):
        """ """
        ## how many ER expected, default 1
        expected = kw.get("expected",1)
        timeout = kw.get("timeout",WAIT_ACK)

        ## reset trigger 
        if self.trigger_[clOrdId].isSet():
            self.trigger_[clOrdId].clear()

        test_received = lambda cid, num: len(self.register_[cid]) == num

        if clOrdId in self.register_.keys():

            log.info("get result for clOrdId: %s, %d" % (clOrdId, len(self.register_.keys())))

            if not active_wait(partial(test_received,clOrdId,expected),timeout=timeout) :
                log.warn("timeout for clOrdId: %s, expected: %d, actual: %d" %(clOrdId, expected, len(self.register_[clOrdId])))

            return self.register_[clOrdId]

        else:
            ## 
            raise ValueError("clOrdId not registered or already extracted: %s, %s" % (clOrdId,res))

    def reset(self):
        """ clear internal cache."""

        for k in self.register_.keys():
            self.register_.pop(k)
            self.trigger_.pop(k)

    @property
    def nextId(self):
        """ """
        return self.seqNum_.next

    @property
    def currentId(self):
        """ """
        return self.seqNum_.current

    def close(self):
        """ """
        self.api_.close()
        self.subscriber.close()
        self.register_= {}
        self.trigger_= {}

