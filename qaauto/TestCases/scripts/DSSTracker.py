"""  track DSS events for registered clOrdId(s).

- internal helper for tracking clOrdId's DSS events
- used by Order module

"""
import os
import sys
import traceback
import threading
from datetime import datetime
import cfg
import ujson as json
import zerorpc
import gevent

## local settings
import logging
log = logging.getLogger("dsstracker")

from conf import settings
from utils import ER,enrich_enum,active_wait
import collections
class DSSTracker:

    """track DSS events for registered clOrdId(s).

    - track DSS events for all clOrdId(s)
    - call back to the original order and update ER

    """
    def __init__(self):
        """ """
        ## setup subscriber for listening DSS events.
        self.subscriber_ = zerorpc.Subscriber(methods={
                                         settings.DSS_PROVIDER: self._on_Dss,
                                         settings.RF_PROVIDER: self._on_Ack,
                                         settings.IMAGELIVE_PROVIDER: self._on_imagelive,
                            })
        log.info("subscribe to :%s for :%s." % (settings.OM2_PUB_ENDPOINT,settings.DSS_PROVIDER))
        self.subscriber_.connect(settings.OM2_PUB_ENDPOINT)
        self.worker_ = gevent.spawn(self.subscriber_.run)
        ##  internal tracker for clOrdId->callback_func
        self.filter_ = {}
        ## track lastAck message
        self.lastAck_ = collections.deque([],1)
        ## filter own process
        self.pid_ = str(os.getpid())

    def track(self,clOrdId,callback):
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

        log.debug("untrack token: %s" % token)
        for clOrdId,callback in sorted(self.filter_.items()):
            if callable(token):
                if token == callback:
                    log.info("untrack clOrdId: %s by callback." % clOrdId)
                    if clOrdId in self.filter_:
                        self.filter_.pop(clOrdId)
                    else:
                        log.warn("unexpected clOrdId: %s, being removed already." % clOrdId)
            else:
                if token == clOrdId:
                    log.info("untrack clOrdId: %s." % token)
                    self.filter_.pop(clOrdId)

    def _on_Dss(self,message):
        """ callback on new dss message. """
        try:
            msg,table,msgId,posDup = message['msg'],message['table'],message['msgId'],message['posDup']
            assert isinstance(msg,dict)
            assert table == 'OrderExecutionUpdate'
            ## process incoming message
            orderInst       = msg['currentOrder']["orderInstructionData"]
            orderStatus     = msg['currentOrder']['orderStatusData']
            pendingCancel   = msg['currentOrder'].get("pendingCancel")
            pendingAmend    = msg['currentOrder'].get("pendingAmend")
            relatedEntityIndexes = msg['currentOrder'].get("relatedEntityIndexes")
            orderId = orderInst['orderId']

            refs = orderStatus['externalReferences']
            ## handle pending xref
            if pendingAmend:
                refs += pendingAmend['externalReferences']
            if pendingCancel:
                refs += pendingCancel['externalReferences']

            assert type(refs) == list
            externalRefIds = [r['tag'] for r in refs if r['externalObjectIdType'] == settings.EXTERNALOBJECTIDTYPE]
            log.info("DSS:%s, orderId: %s, refs: %s" % (orderInst['productId'],orderStatus['orderId'],externalRefIds))

            ## clean up
            if 'transactionalProduct' in msg:
                del msg['transactionalProduct']
            if 'previousOrder' in msg:
                del msg['previousOrder']

            ## enrich enum for the message
            enrich_enum(table,msg)
            log.debug("recv orderId: %s, msg: %s, filter: %s, refs: %s" % \
                    (orderId,msg['eventData'], self.filter_.keys(),refs))

            ## workaround error: dictionary changed size during iteration
            for clOrdId in self.filter_.keys():
                #log.debug("condition: %s, clOrdId: %s" (clOrdId in [r['tag'] for r in refs],clOrdId))
                if clOrdId in externalRefIds:
                    # parsing msg to er
                    er = ER(msg)
                    ## only log interested DSS
                    log.info("process %s, %s, refs: %s, clOrdId: %s, events: %s" % \
                            (orderInst['productId'],orderStatus['orderId'],externalRefIds,clOrdId,er.eventKeys))

                    ## ignore order update event, except update with relatedEntiryIndexes for child order info.
                    if not (len(set(er.eventKeys)) == 1 and er.eventKeys[0] == 'UpdateOrderStatus' and relatedEntityIndexes is None):
                        ## callback
                        self.filter_[clOrdId](clOrdId,er)

        except Exception,e:
            log.exception(e)

    def _on_Ack(self,message):
        """ """
        try:
            log.debug("callback on RF Ack: %d, %s" % (len(self.lastAck_),message))
            ## check posDupId / pid match
            msg = message['msg']
            posDupId = msg.get('posDupId')
            if posDupId and not posDupId.endswith(self.pid_):
                log.debug("ignore ack: %s" % msg)
            else:
                ## risk for unknown reponse
                self.lastAck_.append(message)

        except Exception,e:
            log.exception(e)

    def _on_imagelive(self,message):
        """TODO: capture imagelive related data? """
        try:
            log.debug(message)
        except Exception,e:
            log.exception(e)

    def lastAck(self,timeout=3):
        """ retrive last ack. """

        log.debug("get last ack: %s" % len(self.lastAck_))
        active_wait(lambda: len(self.lastAck_) > 0,timeout=timeout)
        try:

            ret =  self.lastAck_.pop()
            assert 'table' in ret and 'msg' in ret
            assert ret['table'] == "CommandResponse"
            enrich_enum(ret['table'],ret['msg'])
            log.debug("return lastAck: %s" % ret)
            return ret['msg']
        except IndexError:
            log.warn("no last ack with timeout: %s" % timeout)
        except Exception,e:
            log.exception(e)
            raise

    def close(self):
        """ """
        log.info("close subscriber.")
        self.subscriber_.close()
        self.worker_.kill()


if __name__ == "__main__":
    """ test dsstracker. """
    logging.basicConfig(filename="dsstracker_test.log",
                    level=logging.DEBUG,
                    format="%(asctime)-15s %(levelname)s %(process)d %(thread)d %(name)-8s %(lineno)s %(message)s"
                    )

    tracker = DSSTracker()

    tracker.track("junk",lambda (a,b): None)

    while True:
        try:
            ## must using gevent sleep here.
            gevent.sleep(2)
        except KeyboardInterrupt:
            break

