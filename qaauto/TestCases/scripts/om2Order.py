""" test order template.

order common pattern for handle submit order request and DSS callback
- sync order request with DSS callback.

"""
import sys
import os
import copy
import time
from itertools import chain
from datetime import datetime, timedelta,date
import traceback
import atexit
##
import cfg
from conf import settings

from om2API import OM2API
import gevent
from gevent.event import Event

from DSSTracker import DSSTracker
import logging
log = logging.getLogger(__name__)

from utils import translateOrderType, SeqNumber, AckFailed, valid_rf_ack, active_wait


class Order(object):

    """ OM2 test order template.

    OM2 test order for sending new/amend/cancel, all new/amend/cancel will return DSS as ER history.

    internally handle async callback, and basic validaiton.

    """
    ## internal static instance shared for all orders
    _dss = DSSTracker()
    ## interlal static instance for rpc call
    _api = OM2API()
    ## clOrdId generator.
    _seq_num = SeqNumber(cfg.TMP_DIR,"order")

    def __init__(self,dss=None,**kw):
        """ initialize order with order details. """
        ## if specified, override default
        if dss:
            self._dss = kw.pop('dss')

        if kw:
            self._data = copy.deepcopy(kw)
        else:
            self._data = {}
        ####################################################################
        ## list of tuple (clOrdId, []) i.e. clOrdId -> dss callback history
        ## it is the entire order history in list of (clOrdId: DSS(s)).
        self._clOrdIds = []
        self._orderId = None
        ## waiting clOrdId being ack/nak
        self._events =  {}
        ## track child orderIds
        self._childs = []

    def __str__(self):
        return "%s" % self._data

    def __repr__(self):
        return "%s" % self._data

    @property
    def _next_OrdId(self):
        """ internal helper generate next clOrdId for today."""
        today = date.today()
        nextId = Order._seq_num.next
        pid = os.getpid()

        return "%d%s_%d" % (nextId,today.strftime("%Y%m%d"),pid)

    def new(self,validate=True,**kw):
        """new order, return ER ack. """

        log.debug("new order: %s" % kw)
        if kw:
            self._data.update(kw)

        assert "symbol" in self._data
        assert "side" in self._data
        assert "price" in self._data
        assert "qty" in self._data
        assert "sor" in self._data
        assert "exch" in self._data

        if 'clOrdId' in kw:
            clOrdId = kw['clOrdId']
        else:
            clOrdId = self._next_OrdId

        ## update
        self._data['clOrdId'] = clOrdId

        self._clOrdIds.append((clOrdId,[]))
        self._dss.track(clOrdId,self._update_er)
        ## assiciate clOrdId with ack/nak dss event
        self._events[clOrdId] = Event()

        if 'parentOrderId' in self._data:
            ack = Order._api.new_childOrder(**self._data)
        else:
            ack = Order._api.new_order(**self._data)
        ## 
        valid_rf_ack(ack)

        if validate:
            self._events[clOrdId].wait(settings.DSS_ACK_WAIT)
            self.expect("OrderAccept",clOrdId=clOrdId)
            ## callback has completed and om2 orderId has been set.
            assert 'orderId' in self._data
            assert self.orderId

        ## active wait for dss update orderId
        if not active_wait(lambda: hasattr(self,'orderId'), timeout=settings.DSS_ACK_WAIT):
            log.error("Timeout on waiting for DSS set orderId")

        log.info("new %s hist: %s" % (clOrdId,self.events(clOrdId)))
        return self._clOrdIds[0]

    def amend(self,validate=True,**kw):
        """ amend order, return amend order ER. """

        log.debug("amend order: %s" % kw)
        assert  kw
        self._data.update(kw)
        ## generate new clOrdId
        clOrdId = self._next_OrdId
        self._data['clOrdId'] = clOrdId
        ## assert OM2 order exist
        assert 'orderId' in self._data, "missing OM2 OrderId from new ack"

        self._clOrdIds.append((clOrdId,[]))
        self._dss.track(clOrdId,self._update_er)
        ## associate  clOrdId with ack/nak dss event
        self._events[clOrdId] = Event()
        #ack = server.api.amend_order(**self._data)
        ack = Order._api.amend_order(**self._data)
        valid_rf_ack(ack)
        ## waiting for ack/nak
        self._events[clOrdId].wait(settings.DSS_ACK_WAIT)

        ret = None
        for clOrd,hist in self._clOrdIds:
            if clOrdId == clOrd:
                ret = (clOrd,hist)
                break
        ##
        if validate:
            self.expect("AcceptOrderCorrect",clOrdId=clOrdId)

        log.info("amend %s hist: %s" % (clOrdId,self.events(clOrdId)))
        return ret

    def cancel(self,validate=True,**kw):
        """ cancel order, return cancel order ER. """

        log.debug("cancel order: %s" % kw)
        if kw:
            self._data.update(kw)

        clOrdId = self._next_OrdId
        self._data['clOrdId'] = clOrdId

        assert 'orderId' in self._data, "missing OM2 OrderId from new ack"

        cleanup = False
        ret = None

        try:
            self._clOrdIds.append((clOrdId,[]))
            self._dss.track(clOrdId,self._update_er)
            ## associate clOrdId with ack/nak dss event
            self._events[clOrdId] = Event()

            ack = Order._api.cancel_order(**self._data)

            ## check return ack
            if validate:
                valid_rf_ack(ack)
            else:
                gevent.sleep(0)
            ## wait for ack/nak
            self._events[clOrdId].wait(settings.DSS_ACK_WAIT)

            ## no ack event for this clOrdId
            _ack = self._events[clOrdId].is_set()
            if not _ack:
                ## using previous HIST from previous clOrdId
                clOrdId = self._clOrdIds[-2][0]

            if validate:
                self.expect("AcceptOrderCancel",clOrdId=clOrdId)
        except Exception,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = "error: %s,%s" % (e,traceback.extract_tb(exc_traceback))
            log.error(err)
        finally:
            ## need wait for market data feed complete. otherwise, next test case will got incorrect market depth.
            ## wait??
            ## clean up here
            ret = None
            for clOrd,hist in reversed(self._clOrdIds):
                if clOrdId == clOrd:
                    #print "found %s, %s" % (clOrd, hist)
                    ret = (clOrd,hist)
                    break
            ## untrack orderId if completed
            if active_wait(lambda: self.orderStatus.primaryStatus == "Complete", timeout=settings.CANCEL_DELAY):
                self._dss.untrack(self._update_er)
            else:
                log.error("order not completed: %s" % self.events())

        log.info("clOrdId: %s hist: %s" % (clOrdId,self.events(clOrdId)))
        return ret

    def untrack(self, force=False):
        """ untrack for completed order, return True/False. """
        log.debug("untrack :%s" % force)
        done = False
        if self.orderStatus.primaryStatus == "Complete":
            self._dss.untrack(self._update_er)
            done = True
        ## if force to do so
        if not done and force:
            log.info("force untrack working order ref")
            self._dss.untrack(self._update_er)
            done = True

        return done

    def _update_er(self,clOrdId,er):
        """ callback for update ER from dss_tracker."""

        log.debug("_update_er called:%s" % clOrdId)
        assert clOrdId and er
        ## set order 1st for current order.
        if 'orderId' not in self._data:
            orderId = er.order.orderId
            self._data['orderId'] = orderId
            self.orderId = orderId
        ## ack/nak event
        events = set(['OrderAccept','AcceptOrderCorrect','AcceptOrderCancel',
                      'OrderReject','RejectOrderCorrect','RejectOrderCancel',
                      'ForceCancel','DoneForDay',
                      ## order receiver
                      'RequestOrderCancel','RequestOrderCancelFailure',
                      ])
        for clOrd,hist in reversed(self._clOrdIds):
            if clOrd == clOrdId:
                hist.append(er)
                ## collect all child orders into test_order
                if er.childOrders:
                    for o in er.childOrders:
                        if o not in self._childs:
                            self._childs.append(o)
                ## fix dss event arrive out of sequence sorted by transactionCommitId
                hist.sort(key=lambda x: long(x.eventData.transactionCommitId))
                ## check if trigger event found i.e. ack/nak dss event
                if len(events.intersection(set(er.eventKeys))) > 0 and not self._events[clOrd].isSet():
                    log.info("trigger for %s : %s" % (clOrd,er.eventKeys))
                    self._events[clOrd].set()
                    break

    def hist(self,clOrdId=None,last=True):
        """ helper return order dss history.

        input:
            - clOrdId, if specified, it will search specific dss history for the clientOrder
            - if not clOrdId specified, it will return LAST "acked" dss history for all clOrdIds
            - if last == False, it will return all dss history for ALL dss history for all clOrdIds

        """
        assert len(self._clOrdIds) > 0

        if clOrdId:
            self._clOrdIds[clOrdId].wait(settings.DSS_ACK_WAIT)

        ## return specified dss history
        if clOrdId:
            for clOrd,hist in self._clOrdIds:
                if clOrdId == clOrd:
                    return hist

        #import pytest;pytest.set_trace()
        if last:
            for clOrd,hist in reversed(self._clOrdIds):
                if self._events[clOrd].is_set():
                    return hist
            #return self._clOrdIds[-1][1]

        ## return whole dss history here
        hists = []
        for clOrd,hist in self._clOrdIds:
            if len(hist) > 0:
                hists.append(hist)

        return list(chain(*hists))

    def events(self,clOrdId=None):
        """ return event summary in list.

        input:
            - if clOrdId, return dss eventKeys for clientOrder
            - if not specified, return dss eventKeys for all clientOrders

        """
#        if not clOrdId:
#            import pdb;pdb.set_trace()
        ret = []
        for clOrd,hist in self._clOrdIds:
            if clOrdId:
                if clOrdId == clOrd:
                    [ret.append(e.eventKeys) for e in hist]
                    break
            else:
                if len(hist) > 0 :
                    [ret.append(e.eventKeys) for e in hist]

        ## if list of list need unpack
        if len(ret) > 0 and type(ret[0]) == list:
            return list(chain(*ret))

        return ret

    def expect(self,expect, **kw):
        """ validate order in expect status.

        input:
            - expect, expected eveneKey i.e. AttachedExecution or OrderAccept, etc
            - clOrdId,for specified clOrdId, if None, search all
            - timeout, repeat search until timeout

        """
        negate  = kw.get("negate",False)
        clOrdId = kw.get("clOrdId")
        timeout = kw.get("timeout",settings.EXPECT_STATUS_WAIT)
        wait    = kw.get("wait")

        start = datetime.now()

        if wait:
            gevent.sleep(float(wait))

        delta = timedelta(seconds=timeout)

        while True:
            try:
                if clOrdId and self._events[clOrdId].is_set():
                        if negate:
                            if expect in self.events(clOrdId):
                                raise ValueError("%s found for %s, %s, %s" % (expect, clOrdId, self.events(clOrdId), self.orderStatus))
                            else:
                                break
                        else:
                            if expect not in self.events(clOrdId):
                                raise ValueError("%s not found for %s, %s, %s" % (expect, clOrdId, self.events(clOrdId),self.orderStatus))
                            else:
                                break
                else:
                    ## timeout or no clOrdId specified, search all events
                    if negate:
                        if expect in self.events():
                            raise ValueError("%s found for %s, %s, %s" % (expect,self.orderId,self.events(),self.orderStatus))
                        else:
                            break

                    else:
                        if expect not in self.events():
                            raise ValueError("%s not found for %s, %s, %s" % (expect,self.orderId,self.events(),self.orderStatus))
                        else:
                            break

            except ValueError,e:
                end = datetime.now()
                if end > start + delta:
                    duration = (end-start).total_seconds()
                    raise ValueError("duration: %s duration, e: %s" %(duration,e))
                gevent.sleep(0.01)

    def expect_ok(self,**kw):
        """ check order is live without error.  """

        clOrdId = kw.get("clOrdId")
        filled = kw.get("filled",False)

        if self.orderStatus.primaryStatus == 'Complete' and not filled:
            raise ValueError("the order has completed, %s, %s" % (self.events(),self.orderStatus))

        ## live order expect fills
        if filled and self.orderStatus.primaryStatus == "Working" and len(self.fills()) == 0:
                raise ValueError("the order not filled: %s" % (self.orderStatus,self.events(clOrdId)))

        errors = set(['DoneForDay','ForceCancel','RejectOrderCorrect','RejectOrderCancel'])

        if errors.intersection(set(self.events(clOrdId))):
            raise ValueError("unexpected event for %s, %s" % (clOrdId,self.events(clOrdId)))

    @property
    def orderStatus(self):
        """ current order status. return order status in dict.

        orderStatus is based on LAST acked DSS event for all available clOrdIds.

        """

        assert len(self._clOrdIds) > 0, "no filter and dss events, no track called."
        ## get last acked DSS history and return last orderStatus for this ER.
        hist = self.hist(last=True)
        if len(hist) > 0:
            return hist[-1].orderStatus

        log.warn("no dss events captured for order:%s" % self._clOrdIds)

    @property
    def currentOrder(self):
        """ current order. return order in dict.

        currentOrder based on LAST acked DSS event for all available clOrdIds.

        """
        assert len(self._clOrdIds) > 0, "no filter and dss events, no track called."

        ## get last acked DSS history and return last orderStatus for this ER.
        hist = self.hist(last=True)
        assert len(hist) > 0, "no dss events captured"
        return hist[-1].orderStatus

    @property
    def orderInst(self):
        """ current order. return order in dict.

        currentOrder based on LAST acked DSS event for all available clOrdIds.

        """
        assert len(self._clOrdIds) > 0, "no filter and dss events, no track called."

        ## get last acked DSS history and return last orderStatus for this ER.
        hist = self.hist(last=True)
        assert len(hist) > 0, "no dss events captured"
        return hist[-1].order


    @property
    def fills(self):
        """ return list of all fills. """

        assert len(self._clOrdIds) > 0, "no filter and dss events, no track called."
        fills = []
        ## get whole DSS history, find the last one for order info
        hist = self.hist(last=False)
        for dss in hist:
            if hasattr(dss,'execution'):
                fills.append(dss.execution)

        return fills

    @property
    def orderType(self):
        """ translate order type.
            - ASX
            - CHIA
            - ASXCP
            - ASXS
            - tradeReport
            - or SOR
        """
        inst = self.orderInst
        return translateOrderType(inst)

    def requestOrderImage(self,orderId):
        """ helper query order image"""
        log.info("requestOrderImage: %s" % orderId)
        ret = self._api.requestOrderImage(orderId)
        if isinstance(ret,bool) and ret == True:
            ret = self.getLastAck()
            log.info("1st ack: %s" % ret)
            assert isinstance(ret,dict)
            ## 1st ack , sometime return on first ack
            if ret.get('wasCommandSuccessful') == 1 and 'orderStatusData' not in ret:
                ret = self.getLastAck(10)
        return ret

    def requestExecutionImage(self,execId):
        """ helper query execution"""
        ret =  self._api.requestExecutionImage(execId)
        if isinstance(ret,bool) and ret == True:
            gevent.sleep(0.1)
            ret = self.getLastAck()
        return ret

    def requestCancelExecution(self,**kw):
        """ helper cancel execution."""
        ret = self._api.cancel_execution(**kw)
        if isinstance(ret,bool) and ret == True:
            ret = self.getLastAck()
        ## 
        valid_rf_ack(ret)
        return ret

    @classmethod
    def sendRdsHermes(self,order):
        """ helper send hermes to RDS."""
        assert isinstance(order,dict)
        ret =  self._api.send_herme(settings.RDS_REQ,order)
        if isinstance(ret,bool) and ret == True:
            ret = self.getLastAck()
        return ret

    @classmethod
    def sendRF(self,table,message,**kw):
        """ helper send rf directly. """
        wait = kw.get("wait",True)

        assert isinstance(message,dict)
        ret = self._api.send_rf_msg(table,message)
        if isinstance(ret,bool) and ret == True:
            if wait:
                ret = self.getLastAck()
        return ret

    @classmethod
    def getLastAck(self,timeout=3):
        return self._dss.lastAck(timeout)

    def query_child_orders(self):
        """ helper for query child orders."""
        gevent.sleep(2)
        child_orders = []
        for child in self._childs:
            child_order = self.requestOrderImage(child)
            assert child_order
            child_orders.append(child_order)
        return child_orders

atexit.register(Order._dss.close)
