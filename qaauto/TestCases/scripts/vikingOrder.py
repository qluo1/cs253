""" viking order.

"""
import time
import sys
import os
import random
import atexit
import copy
from datetime import datetime,timedelta,date
from pprint import pprint
import gevent
from gevent.event import Event
import logging
import zerorpc

log = logging.getLogger(__name__)

import cfg
from conf import settings

from utils import SeqNumber, IvComDictHelper
XREFS = ('Z','Y','X')

#from vikingOrderTracker import VikingOrderTracker
from vkOrderTracker import VikingOrderTracker

class VikingOrder:

    tracker_ = VikingOrderTracker(settings.VK_PUB_ENDPOINT)

    api_ = zerorpc.Client(settings.VK_ORDER_ENDPOINT,heartbeat=settings.HEARTBEAT_TIMEOUT)

    seqNum_ = SeqNumber(cfg.TMP_DIR,"VikingOrder")

    def __init__(self,**kw):
        """ """
        self._data = {}
        ## default xref
        self._xref = random.choice(XREFS)
        ##
        if kw:
            if "exch" in kw:
                self._data["vikingMarketId"] = kw["exch"]
                kw.pop("exch")
            assert self._data["vikingMarketId"] in ("SYDE","CHIA",)
            if "tif" in kw:
                self._data["timeInForce"] = kw["tif"]
                kw.pop("tif")
            if "xref" in kw:
                self._xref = kw["xref"]
                kw.pop("xref")

            self._data.update(kw)

        self._events = {}
        self._version = 0

        ## construct viking orderId
        today = datetime.now()
        self._data['orderId'] = self._next_OrdId
        ## default value
        if "orderType" not in self._data:
            self._data["orderType"] = "Limit"

        if "buySell" not in self._data:
            self._data["buySell"] = "Buy"

        if "timeInForce" not in self._data:
            self._data["timeInForce"] = "Day"

        if "vikingMarketId" not in self._data:
            self._data["vikingMarketId"] = "SYDE"

        ## track and process viking ack i.e. callback
        self.tracker_.track(self._data['orderId'],self._update_er)
        ## assiciate OrdId with ack/nak dss event
        self._events[self._data['orderId']] = Event()
        ## viking ack history
        self._acks = []

    def __str__(self):
        return "%s" % self._data

    def __repr__(self):
        return "%s" % self._data

    def _update_er(self,ordId,er):
        """ callback for update ER from dss_tracker."""
        assert ordId and er
        log.debug("ack: %s, %s" % (ordId, er))
        assert ordId == self._data["orderId"]

        assert "table" in er and "msg" in er and "msgId" in er and "posDup" in er
        self._acks.append(er)

        table = er["table"]
        msg = er["msg"]
        if table == "VikingOrderAccept":
            assert 'exchangeOrderId' in msg
            self._data['exchangeOrderId'] = msg['exchangeOrderId']
            #self._data["lastVikingId"] = msg["lastVikingId"]
            #self._data["vikingLineId"] = msg["vikingLineId"]
        ## set event
        self._events[ordId].set()

    @property
    def acks(self):
        """ """
        return [er['table'] for er in self._acks]

    @property
    def filledQty(self):
        """ """
        ## delay 1 second to wait for more ERs
        total  = 0
        fills = [er['msg'] for er in self._acks if er['table'] == 'VikingExecution']

        for fill in  fills:
            total += fill['quantity']
        return total

    def _header(self,orderId):
        """ helper for command header. """

        header = IvComDictHelper("CommandHeader")
        now = datetime.now()
        header.set("posDupId","%s" % orderId)
        header.set("isPosDup",True)
        header.set("commandTime",int(time.mktime(now.timetuple())))
        return header.msg

    def _flowAU(self):
        """ helper """
        flowSpecAU = IvComDictHelper("FlowSpecificAustralia")
        ##TODO: set based on input ?
        flowSpecAU.set("asicOriginOfOrder",1234)

        ## reverse workout orderId
        def _extract_orderId(clOrdId):
            orderId , pid = clOrdId.split("_")
            return orderId[:-8]

        flowSpecAU.set("iosAccountExchangeCrossReference","%s/%s" % (self._xref,_extract_orderId(self._data["orderId"])))
        return flowSpecAU.msg

    @property
    def _next_OrdId(self):
        """ internal helper generate next clOrdId for today."""
        today = date.today()
        nextId = self.seqNum_.next
        pid = os.getpid()

        return "%d%s_%d" % (nextId,today.strftime("%Y%m%d"),pid)


    def new(self,**kw):
        """ submit new vikingOrder. """

        assert 'symbol' in kw
        validate = kw.get("validate",True)
        ## ticker only
        if kw["symbol"].endswith(".AX") or kw["symbol"].endswith(".CHA"):
            self._data["productId"] = kw["symbol"].split(".")[0]
        else:
            self._data["productId"] = kw["symbol"]
        ## override 
        if "orderType" in kw:
            self._data["orderType"] = kw["orderType"]

        if "side" in kw:
            if kw['side'] in ("SS","Short"):
                self._data["buySell"] = "Sell"
                self._data["sellShort"] = True
            else:
                self._data["buySell"] = kw["side"]

        if "timeInForce" in kw:
            self._data["timeInForce"] = kw["timeInForce"]
        if "tif" in kw:
            self._data["timeInForce"] = kw["tif"]
        if "expirationDateTime" in kw:
            self._data["expirationDateTime"] = kw["expirationDateTime"]

        if "qty" in kw:
            self._data["quantity"] = kw["qty"]
        if "price" in kw:
            self._data["limitPrice"] = kw["price"]
        if "exch" in kw:
            self._data["vikingMarketId"] = kw["exch"]

        ## supported exchange
        assert self._data["vikingMarketId"] in ("SYDE","CHIA")

        if "allOrNone" in kw:
            self._data["allOrNone"] = kw["allOrNone"]

        if "pegType" in kw:
            self._data["pegType"] = kw["pegType"]
            ## set orderType
            if self._data["orderType"] != "Pegged":
                self._data["orderType"] = "Pegged"

        extra = kw.get("extra")

        today = datetime.now()

        order = IvComDictHelper("VikingOrder")
        orderId = self._data['orderId']
        order.set("commandHeader",self._header(orderId))
        order.set("orderId",orderId)

        order.set("orderType",self._data["orderType"])
        if "pegType" in self._data:
            order.set("pegType",self._data["pegType"])
        order.set("buySell",self._data["buySell"])
        if 'sellShort' in self._data:
            order.set("sellShort",self._data["sellShort"])
        order.set("timeInForce",self._data["timeInForce"])
        if "expirationDateTime" in self._data:
            order.set("expirationDateTime",self._data["expirationDateTime"])
        if "allOrNone" in self._data:
            order.set("allOrNone",self._data["allOrNone"])
        order.set('quantity',self._data["quantity"])
        order.set("limitPrice",self._data["limitPrice"])
        order.set("lotSize",1)
        order.set("vikingMarketId",self._data["vikingMarketId"])
        order.set("vikingMarketIdType","PrimeId")
        order.set("vikingDestinationId",self._data["vikingMarketId"])
        product = IvComDictHelper("ProductSynonym")
        product.set("productId",self._data["productId"])
        product.set("productIdType","Ticker")
        order.set("productSynonyms",[product.msg])
        order.set("productInstrumentType","Equity")

        if self._data["vikingMarketId"] in ('SYDE',"CHIA"):
            order.set("flowSpecificAustralia",self._flowAU())

        order.set("orderCapacity","Agency")
        self._version += 1
        order.set("orderVersion",self._version)
        ## set extra attrs
        if extra:
            for k,v in extra.iteritems():
                order.set(k,v)

        log.info("new viking order:%s, %s" % (orderId, order.msg))
        ## SYDE or CXA order
        if self._data["vikingMarketId"] == "SYDE":
            ack = self.api_.enqueue_message(settings.VK_ASX_PROVIDER ,"VikingOrder",order.msg)
        elif self._data["vikingMarketId"] == "CHIA":
            ack = self.api_.enqueue_message(settings.VK_CXA_PROVIDER ,"VikingOrder",order.msg)
        else:
            raise ValueError("unsupported exchange: %s, only support (SYDE/CHIA)" % self._data["vikingMarketId"])

        gevent.sleep(0)
        assert ack and ack['ack'] == 'ok'

        if validate:
            self._events[orderId].wait(settings.DSS_ACK_WAIT)

            ret = False
            if self.acks[0] == "VikingOrderAccept":
                ret = True
            ## reset event
            self._events[orderId].clear()
            return ret

        return ack

    def amend(self,**kw):
        """ submit viking order amend. """

        assert "qty" in kw or "price" in kw
        validate = kw.get("validate",True)

        deltaQuantity = 0
        if 'qty' in kw:
            deltaQuantity = kw['qty'] - self._data["quantity"]
            quantityRemaining = kw['qty']
        deltaPrice = 0
        if 'price' in kw:
            deltaPrice = kw['price'] - self._data["limitPrice"]
        assert deltaQuantity > 0 or deltaPrice > 0

        today = datetime.now()
        order = IvComDictHelper("VikingAmendOrder")
        orderId = self._data['orderId']
        header = IvComDictHelper("CommandHeader")
        header.set("isPosDup",True)
        header.set("commandTime",int(time.mktime(today.timetuple())))
        order.set("commandHeader",header.msg)
        order.set("orderId",orderId)

        order.set("orderType",self._data["orderType"])
        if "pegType" in self._data:
            order.set("pegType",self._data["pegType"])
        order.set("buySell",self._data["buySell"])
        if 'sellShort' in self._data:
            order.set("sellShort",self._data["sellShort"])
        order.set("timeInForce",self._data["timeInForce"])
        if "expirationDateTime" in self._data:
            order.set("expirationDateTime",self._data["expirationDateTime"])

        order.set('quantity',self._data["quantity"])
        if deltaQuantity:
            order.set("deltaQuantity",deltaQuantity)
            order.set("quantityRemaining",quantityRemaining)

        order.set("limitPrice",self._data["limitPrice"])
        if deltaPrice:
            order.set("deltaPrice",deltaPrice)
        order.set("lotSize",1)
        order.set("vikingMarketId",self._data["vikingMarketId"])
        order.set("vikingDestinationId",self._data["vikingMarketId"])
        order.set("vikingMarketIdType","PrimeId")

        product = IvComDictHelper("ProductSynonym")
        product.set("productId",self._data["productId"])
        product.set("productIdType","Ticker")
        order.set("productSynonyms",[product.msg])
        order.set("productInstrumentType","Equity")

        order.set("flowSpecificAustralia",self._flowAU())
        order.set("orderCapacity","Agency")
        self._version += 1
        order.set("orderVersion",self._version)

        log.info("amend viking order:%s, %s" % (orderId, order.msg))

        ## SYDE or CXA order
        if self._data["vikingMarketId"] == "SYDE":
            ack = self.api_.enqueue_message(settings.VK_ASX_PROVIDER,"VikingAmendOrder",order.msg)
        elif self._data["vikingMarketId"] == "CHIA":
            ack = self.api_.enqueue_message(settings.VK_CXA_PROVIDER ,"VikingAmendOrder",order.msg)
        else:
            raise ValueError("unsupported exchange: %s, only support (SYDE/CHIA)" % self._data["vikingMarketId"])

        assert ack and ack['ack'] == 'ok'

        gevent.sleep(0)
        if validate:
            self._events[orderId].wait(settings.DSS_ACK_WAIT)
            ret = False
            ## handle Reject
            if  self.acks[-1] == "VikingAcceptCorrectionRequest":
                ret = True
            ## reset event
            self._events[orderId].clear()

            ## reset quantity and limitPrice for the order
            if deltaQuantity:
                self._data['quantity'] = self._data['quantity'] + deltaQuantity
            if deltaPrice:
                self._data['limitPrice'] = self._data['limitPrice'] + deltaPrice

            return ret

        return ack

    def cancel(self):
        """ """
        ret = False
        if len(self.acks) > 0:
            today = datetime.now()
            order = IvComDictHelper("VikingCancelOrder")
            orderId = self._data['orderId']

            header = IvComDictHelper("CommandHeader")
            now = datetime.now()
            header.set("isPosDup",True)
            header.set("commandTime",int(time.mktime(now.timetuple())))
            order.set("commandHeader",header.msg)
            order.set("orderId",orderId)

            #order.set("orderType",self._data["orderType"])
            order.set("buySell",self._data["buySell"])
            order.set("vikingMarketId",self._data["vikingMarketId"])
            order.set("vikingMarketIdType","PrimeId")
            order.set("vikingDestinationId",self._data["vikingMarketId"])

            product = IvComDictHelper("ProductSynonym")
            product.set("productId",self._data["productId"])
            product.set("productIdType","Ticker")
            order.set("productSynonyms",[product.msg])
            order.set("productInstrumentType","Equity")
            self._version += 1
            order.set("orderVersion",self._version)

            log.info("cancel viking order:%s, %s" % (orderId, order.msg))

            ## SYDE or CXA order
            if self._data["vikingMarketId"] == "SYDE":
                ack = self.api_.enqueue_message(settings.VK_ASX_PROVIDER ,"VikingCancelOrder",order.msg)
            else:
                ack = self.api_.enqueue_message(settings.VK_CXA_PROVIDER,"VikingCancelOrder",order.msg)

            assert ack and ack['ack'] == 'ok'
            self._events[orderId].wait(settings.DSS_ACK_WAIT)
            ## handle Reject
            if  self.acks[-1] == "VikingAcceptCancelRequest":
                ret = True
            ## reset event
            self._events[orderId].clear()

            self.tracker_.untrack(self._update_er)
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
        timeout = kw.get("timeout",settings.DSS_ACK_WAIT)
        wait    = kw.get("wait")

        if wait:
            gevent.sleep(float(wait))

        start = datetime.now()
        delta = timedelta(seconds=timeout)

        while True:
            try:
                if negate:
                    if expect in self.acks:
                        raise ValueError("%s found for %s" % (expect, self.acks))
                    else:
                        break
                else:
                    if expect not in self.acks:
                        raise ValueError("%s not found for %s" % (expect, self.acks))
                    else:
                        break
            except ValueError,e:
                end = datetime.now()
                if end > start + delta:
                    raise(e)
                gevent.sleep(0)


if __name__ == "__main__":
    """ unit tests. """

    logging.basicConfig(filename="vikingOrdertracker.log",
                    level=logging.DEBUG,
                    format="%(asctime)-15s %(levelname)s %(process)d %(thread)d %(name)-8s %(lineno)s %(message)s"
                    )

    for exch in ("SYDE","CHIA"):
        for i in range(3):
            try:
                order = VikingOrder(exch=exch)
                order.new(symbol="NAB",price=25.4,qty=109)
            except IndexError:
                pass
            order = VikingOrder(exch=exch)
            order.new(symbol="NAB",price=21.4,qty=109)
            pprint(order._acks)
            print "---------------"
            print "amend"
            order.amend(price=22.6,qty=119)
            pprint(order._acks)
            print "----------------"

            print "cancel"
            assert order.cancel() == True
            pprint(order._acks)
            print "----------------"


            order = VikingOrder(exch=exch)
            order.new(symbol="NAB",price=23.4,qty=100,tif="ImmediateOrCancel",allOrNone=False)
            print "cancel"
            assert order.cancel() == False
            print order.acks
            pprint(order._acks)



