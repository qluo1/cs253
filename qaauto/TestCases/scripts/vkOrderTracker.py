import sys
import traceback
import logging
import cfg
import zerorpc
import gevent

log = logging.getLogger(__name__)

from conf import settings

class VikingOrderTracker:

    def __init__(self,endpoint):
        """ """
        subscriber_ = zerorpc.Subscriber(methods={
                                         settings.VK_CXA_RESP: self.on_vkCXA,
                                         settings.VK_ASX_RESP: self.on_vkASX,
                                         settings.VK_ASX_PROVIDER: self.on_vkASX_ack,
                                         settings.VK_CXA_PROVIDER: self.on_vkCXA_ack,
                                         })
        log.info("subscribe to :%s." % endpoint)
        subscriber_.connect(endpoint)
        self.worker_ = gevent.spawn(subscriber_.run)
        ## 
        self.filter_ = {}

    def on_vkCXA(self,message):
        """ cxa callback. """
        log.info("on viking cxa message")
        if not isinstance(message,dict):
            log.error("invalid message, expect dict: %s" % message)
            return
        message['source'] = settings.VK_CXA_PROVIDER
        self.dispatch(message)

    def on_vkASX(self,message):
        """ asx callback. """
        log.info("on_vking_asx message")
        if not  isinstance(message,dict):
            log.error("invalid message, expect dict: %s" % message)
            return
        message['source'] = settings.VK_ASX_PROVIDER
        self.dispatch(message)

    def on_vkASX_ack(self,ack):
        """ """
        log.info(ack)

    def on_vkCXA_ack(self,ack):
        """ """
        log.info(ack)

    def dispatch(self,data):
        """ callback on viking message."""

        try:
            #print data
            table,msg,msgId,posDup,source=data['table'],data['msg'],data['msgId'],data['posDup'],data['source']
            log.info("recived table: %s, msgId: %s, posDup: %s, source: %s" % (table,msgId,posDup,source))
            ## revert to original orderId
            clOrdId = data['msg']['orderId']
            #log.debug("msg orderId: %s, keys: %s, %s" % (clOrdId,self.filter_.keys(), clOrdId in self.filter_.keys()))
            if clOrdId in self.filter_.keys():
                self.filter_[clOrdId](clOrdId,data)
        except Exception,e:
            log.error("unexpected: %s" % e)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = "error: %s,%s,%s, %s" % (e,data,self.filter_,traceback.extract_tb(exc_traceback))
            log.error(err)

    def track(self, clOrdId,callback):
        """track DSS event for specified clOrdId.

        input:
            - clOrdId for tracking DSS event related to this clOrdId
            - callback for receiving ER

        """

        assert callable(callback), "callback isn't a function"
        log.info("track: %s, running: %s" % (clOrdId,self.worker_.started))
        self.filter_[clOrdId] = callback

    def untrack(self,token):
        """ untrack a clOrdId or a callback when order completed.  """

        for clOrdId,callback in self.filter_.items():
            if callable(token):
                if token == callback:
                    log.info("untrack: %s" % clOrdId)
                    self.filter_.pop(clOrdId)
            else:
                if token == clOrdId:
                    log.info("untrack: %s" % token)
                    self.filter_.pop(clOrdId)


if __name__ == "__main__":
    """ """
    ## forward to public/publish endpint.
    logging.basicConfig(filename="vkOrdertracker.log",
                    level=logging.INFO,
                    format="%(asctime)-15s %(levelname)s %(process)d %(threadName)s %(name)-8s %(lineno)s %(message)s"
                    )

    vk = VikingOrdTracker(settings.ORDER_API_URL)
    gevent.joinall([vk.worker_])

