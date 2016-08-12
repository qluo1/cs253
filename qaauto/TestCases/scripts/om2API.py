""" om2 api
"""
import sys
import traceback
import logging
from datetime import datetime,timedelta
import time
import copy
import os
## local config
import cfg
from dateutil import parser
from utils import IvComDictHelper

log = logging.getLogger(__name__)

class IvComOrderHelper(object):

    """ helper class for generate IvCom message. """

    def getHeader(self,clOrdId,system,userId,**kwargs):
        """return ivcom message common header. """

        now = kwargs.get("now",datetime.now())
        assert isinstance(now,datetime)
        isPosDup = kwargs.get("isPosDup",True)
        systemType = kwargs.get("systemType","AlgorithmEngine")
        creatorIdType = kwargs.get("creatorIdType","External")
        header = IvComDictHelper("CommandHeader")

        header.set("posDupId",clOrdId)
        header.set("isPosDup",isPosDup)
        header.set("commandTime",int(time.mktime(now.timetuple())))
        header.set("systemName",system)
        header.set("creatorId",userId)
        header.set("creatorIdType",creatorIdType)
        header.set("systemType",systemType)
        return header

    def getAccounts(self,acct,**kwargs):
        """return account ivcom message. """

        accountRole = kwargs.get("accountRole","Primary")
        accountType = kwargs.get("accountType","Trading")
        entity = kwargs.get("entity","GSJP")

        account  = IvComDictHelper("Account")
        account_alias = IvComDictHelper("AccountAlias")
        account_alias.set("accountSynonymType","AmAccountSynonym")
        account_alias.set("accountSynonym",acct)
        account.set("accountAliases",[account_alias.msg])
        ## attrs
        account.set("accountRole",accountRole)
        account.set("accountType",accountType)
        account.set("entity",entity)
        return account

    def getTamAccounts(self,acct):
        """ return am account name"""
        account  = IvComDictHelper("Account")
        account.set("accountRole","Primary")
        account_alias = IvComDictHelper("AccountAlias")
        account_alias.set("accountSynonymType","AmAccountNumber")
        account_alias.set("accountSynonym",acct)
        account.set("accountAliases",[account_alias.msg])
        return account

    def getExternalRefs(self,clOrdId,**kwargs):
        """return externalRefs ivcom message.

        this will be used as clOrdId, DSSTracker will used for lookup related DSS message.

        """

        systemName = kwargs.get("systemName","IvComPyService")

        now = datetime.now().timetuple()
        externalRef = IvComDictHelper("ExternalReference")
        externalRef.set("systemName",systemName)
        externalRef.set("tag",clOrdId)
        externalRef.set("externalObjectIdType","FixOrderId")
        externalRef.set("tagDate",int(time.mktime(now)))
        return externalRef

    def getFlowSpec(self,xref):
        """ return AU Flowspecific ivcom message.

        this can be clOrdId, i.e. xref with random bit.
        or xref without random bit.

        """
        flowSpecAU = IvComDictHelper("FlowSpecificAustralia")
        if xref:
            flowSpecAU.set("iosAccountExchangeCrossReference",xref)
        return flowSpecAU

    def createOrderCommand(self,**kw):
        """ return CreateOrderCommand ivcom msg.

        mapping:
        asxc:
         u'orderType': u'Pegged',
         u'pegOffsetType': u'Price',
         u'pegType': u'Mid',
        asxs:
         u'routingStrategy': u'ASXC;ASXT'

        generic peg order type for CHIA/ASX:
        - orderType is Pegged
        - pegType
        - pegOffSetType

        trade report - single leg:
        exch is 'SIGA'
        isPartOfTwoSidedTradeReport True
        crossMatchingId required i.e. "FA8/S/0O:FC8/S/0P"
        australiaTradeConditionCode
        crossRequestReason (optional)
        oeid  (optional)
        startId (optional)
        account (optional)

        """
        symbol  = kw['symbol']
        symbolType = kw.get("symbolType","Ticker")
        ## clearnup symbology
        if "." in symbol and (symbol.endswith("AX") or symbol.endwith("CHA")) and symbolType == "Ticker":
               symbol = symbol.split(".")[0]

        clOrdId = kw['clOrdId']
        side    = kw['side']
        price   = kw['price']
        xref    = kw.get('xref')
        exch    = kw.get("exch","SYDE")
        ## default order type i.e. Limit
        ordType = kw.get("orderType","Limit")
        qty     = kw["qty"]
        acct    = kw.get("account")
        synthetic = kw.get("synthetic")
        ## default dma
        serviceOffering = kw.get("serviceOffering",5)
        crossConsent = kw.get("crossConsent")
        system = kw.get("system","PlutusChild_DEV")
        ## userId
        userId = kw.get("userId", os.getlogin())

        ## extra parameters for order creation
        ## it should be validated at client side
        extra = kw.get("extra",{})
        ## embedded within commandRequest
        embedded = kw.get("commandRequest",False)

        short   = False
        shortExempt = False
        if side == 'Short':
            side = 'Sell'
            short = True
        if side =='SSE':
            side = 'Sell'
            shortExempt = True

        tif       = kw.get("tif","Day")
        allOrNone = kw.get("allOrNone",False)
        ##default Principal
        capacity  = kw.get("capacity")
        sor       = kw.get("sor")
        sorParam  = kw.get("sorParam","")
        atp       = kw.get("atp",False)
        maq       = kw.get('maq')

        ## order creation time
        if "now" in kw:
            now = parser.parse(kw["now"])
        else:
            now = datetime.now()
        ## set to am account if account specified
        if acct:
            account = self.getTamAccounts(acct)
        else:
            if xref:
                account = self.getAccounts(xref)

        ## xref can be None, will be empty flowspec
        flowspec= self.getFlowSpec(xref)

        header  = self.getHeader(clOrdId,system,userId,now=now)
        external= self.getExternalRefs(clOrdId)

        order = IvComDictHelper("CreateOrderCommand")
        ## set order structure
        order.set("commandHeader",header.msg)
        order.set("externalReferences",[external.msg])
        if 'account' in locals():
            order.set("accounts",[account.msg])
        ## order type
        order.set("orderType",ordType)
        ## market order don't like price
        if ordType != "Market":
            order.set("limitPrice",price)
        order.set("buySell",side)
        if side != 'Buy':
            order.set("sellShort",short)
            order.set("sellShortExempt",shortExempt)
        order.set("allOrNone",allOrNone)
        order.set("serviceOffering",serviceOffering)
        if crossConsent:
            order.set("crossConsent",crossConsent)

        ## symbol/symbolType
        order.set("productId",symbol)
        order.set("productIdType",symbolType)
        order.set("quantity",qty)
        order.set("timeInForce",tif)

        ## set if specified
        if capacity:
            order.set("orderCapacity",capacity)
        ## mxq
        if maq:
            order.set("minExecutableQuantity",maq)

        ## execution point
        order.set("executionPointOverride",exch)
        ## single leg trade report
        if kw.get("crossMatchId"):
            matchId = kw['crossMatchId']
            agreeDate = kw.get("agreeDate")
            conditionCode = kw.get('conditionCode','NX')
            flowspec.set('australiaTradeConditionCode',conditionCode)
            reason = kw.get("crossReason","Other")

            order.set('isPartOfTwoSidedTradeReport',True)
            order.set('crossMatchingId',matchId)
            order.set('crossRequestReason',reason)
            order.set('subExecutionPointOverride',exch)
            if not agreeDate:
                order.set('tradeAgreementDate',int(time.mktime(now.timetuple())))
            else:
                order.set('tradeAgreementDate',int(agreeDate))

        ################ special case ###############
        ## ASXC
        if exch == "ASXC":
            order.set("orderType","Pegged")
            order.set("pegOffsetType","Price")
            order.set("pegType", "Mid")
            order.set("executionPointOverride","SYDE")
        ## ASXS
        elif exch == "ASXS":
            order.set('routingStrategy', 'ASXC;ASXT')
            order.set("executionPointOverride","SYDE")

        ## peg order type
        elif ordType == "Pegged" and exch in ("SYDE", "CHIA"):
            pegOffsetType = kw.get('pegoffset',"Price")
            pegType = kw['pegType']

            order.set("pegOffsetType",pegOffsetType)
            order.set("pegType",pegType)
        ## sor order
        elif sor:
            order.set("tradingAlgorithm",sor)
            order.set("tradingAlgorithmParameters",sorParam)
            order.set("destinationTraderId",os.getlogin())
            ## atp order
            if atp:
                order.set("tradeViaInternalAlgorithm",True)
                order.set("algorithmicIndicator",'Algorithmic')
            else:
                order.set("smartRouteConsent","OkToSmartRoute")

        else:
            pass
        ## of customerOeId/startId set, ignore flowSpec i.e. xref
        #if not 'customerOeId' in extra and not 'startId' in extra:
        order.set("flowSpecificAustralia",flowspec.msg)

        ##  k must be CreateOrderCommand
        for k,v in extra.iteritems():
            order.set(k,v)
        ##
        ## [{u'rejectReasonText': u'TIME IN FORCE MUST EQUAL TO IOC/PAK OR MAXFLOOR EQUALS TO 0 IF HAVING MINQTY(TAG 110)'
        ## tradingAlgorithm="CsorAuction", type=Limit, TIF=Day, tradingAlgoParameters="auctionType=3;referencePrice=CLOSE"

        if embedded:
            commandRequest = IvComDictHelper("CommandRequest")
            requestResponseCommand = IvComDictHelper("RequestResponseCommand")
            requestResponseCommand.set("createOrderCommand",order.msg)
            commandRequest.set("requestResponseCommand",requestResponseCommand.msg)

            return commandRequest.msg

        log.info("iv msg: %s" % order.msg)

        return order.msg

    def createChildOrderCommand(self,**kw):
        """ createChildOrderCommand for a parent order. no need for symbol. """

        parentOrderId = kw["parentOrderId"]
        clOrdId = kw['clOrdId']
        price   = kw['price']
        qty     = kw["qty"]
        ## side not used for childOrder, but sellShort need set
        side    = kw.get("side")

        ### optional fields
        xref    = kw.get('xref')
        acct    = kw.get("account")
        exch    = kw.get("exch","SYDE")
        ## default order type i.e. Limit
        ordType = kw.get("orderType","Limit")
        ## default dma
        serviceOffering = kw.get("serviceOffering")
        crossConsent = kw.get("crossConsent")
        user = kw.get("user") or os.getlogin()
        tif       = kw.get("tif","Day")
        allOrNone = kw.get("allOrNone",False)
        ##default Principal
        capacity  = kw.get("capacity")
        sor       = kw.get("sor")
        sorParam  = kw.get("sorParam","")
        maq       = kw.get('maq')
        system    = kw.get("system","PlutusChild_DEV")
        userId    = kw.get("userId",os.getlogin())

        ## extra parameters for order creation
        ## it should be validated at client side
        extra = kw.get("extra",{})
        ## embedded within commandRequest
        embedded = kw.get("commandRequest",False)

        ## order creation time
        if "now" in kw:
            now = parser.parse(kw["now"])
        else:
            now = datetime.now()
        ## set to am account if account specified
        header  = self.getHeader(clOrdId,system,userId,now=now)
        external= self.getExternalRefs(clOrdId)
        account = self.getAccounts(acct or xref or clOrdId)
        flowspec= self.getFlowSpec(xref)

        order = IvComDictHelper("CreateChildOrderCommand")
        order.set("commandHeader",header.msg)
        order.set("externalReferences",[external.msg])
        order.set("parentOrderGsuid",parentOrderId)
        order.set("destinationId", "SGMX")
        ## order type
        order.set("orderType",ordType)
        order.set("quantity",qty)
        order.set("timeInForce",tif)
        ## set order structure
        order.set("accounts",[account.msg])
        order.set("flowSpecificAustralia",flowspec.msg)

        ## market order don't like price
        if ordType != "Market":
            order.set("limitPrice",price)
        order.set("allOrNone",allOrNone)
        if serviceOffering:
            order.set("serviceOffering",serviceOffering)
        if crossConsent: order.set("crossConsent",crossConsent)

        ## set if specified
        if capacity: order.set("orderCapacity",capacity)
        ## mxq
        if maq: order.set("minExecutableQuantity",maq)
        ## execution point
        order.set("executionPointOverride",exch)
        ## peg order type
        if ordType == "Pegged" and exch in ("SYDE", "CHIA"):
            pegOffsetType = kw.get('pegoffset',"Price")
            pegType = kw['pegType']

            order.set("pegOffsetType",pegOffsetType)
            order.set("pegType",pegType)

        if sor:
            order.set("tradingAlgorithm",sor)
            order.set("tradingAlgorithmParameters",sorParam)
            order.set("destinationTraderId",user)
            ## atp order
            order.set("tradeViaInternalAlgorithm",True)
            order.set("algorithmicIndicator",'Algorithmic')
            order.set("smartRouteConsent","OkToSmartRoute")

        if side and side == 'Short':
            order.set("sellShort",True)

        ##  k must be CreateChildOrderCommand
        for k,v in extra.iteritems():
            order.set(k,v)

        if embedded:
            commandRequest = IvComDictHelper("CommandRequest")
            requestResponseCommand = IvComDictHelper("RequestResponseCommand")
            requestResponseCommand.set("createChildOrderCommand",order.msg)
            commandRequest.set("requestResponseCommand",requestResponseCommand.msg)

            return commandRequest.msg

        return order.msg

    def requestCorrectOrderCommand(self,**kw):
        """ return requestCorrectOrderCommand ivcom msg.

        mapping pydict to ivcom message.
        orderId is required.
        """
        ## om2 order Id
        orderId = kw['orderId']
        clOrdId = kw['clOrdId']
        ## same as newOrder
        xref    = kw.get('xref')
        price   = kw['price']
        qty     = kw["qty"]
        maq     = kw.get("maq")
        atp     = kw.get("atp",False)
        tif     = kw.get("tif",None)
        system    = kw.get("system","PlutusChild_DEV")
        userId  = kw.get("userId",os.getlogin())
        ## extra data
        extra = kw.get("extra", {})
        ## embedded within commandRequest
        embedded = kw.get("commandRequest",False)

        now = datetime.now()

        flowspec= self.getFlowSpec(xref)
        header  = self.getHeader(clOrdId,system,userId,now=now)
        external= self.getExternalRefs(clOrdId)

        order = IvComDictHelper("RequestCorrectOrderCommand")
        order.set("orderId",orderId)
        ## skip market order price amend
        if price != 0:
            order.set("limitPrice",price)
        order.set("quantity",qty)
        ## set order structure
        order.set("flowSpecificAustralia",flowspec.msg)
        order.set("commandHeader",header.msg)
        order.set("externalReferences",[external.msg])
        if maq:
            order.set("minExecutableQuantity",int(maq))
        ## atp order
        if atp:
            sor = kw['sor']
            sorParam = kw['sorParam']

            order.set("smartRouteConsent","OkToSmartRoute")
            order.set("tradingAlgorithm",sor)
            order.set("tradingAlgorithmParameters",sorParam)
            order.set("tradeViaInternalAlgorithm",True)
        ## amend tif
        if tif:
            order.set("timeInForce",tif)

        ##  k must be  catalog
        for k,v in extra.iteritems():
            ## ignore extra fields only valid for createOrderCommand.
            try:
                order.set(k,v)
            except AssertionError:
                log.warn("key: %s, val: %s can't be set for RequestCorrectOrderCommand" % (k,v))

        if embedded:
            commandRequest = IvComDictHelper("CommandRequest")
            requestResponseCommand = IvComDictHelper("RequestResponseCommand")
            requestResponseCommand.set("requestCorrectOrderCommand",order.msg)
            commandRequest.set("requestResponseCommand",requestResponseCommand.msg)

            return commandRequest.msg

        log.info("iv msg: %s" % order.msg)

        return order.msg

    def requestCancelOrderCommand(self,**kw):
        """cancel order,return requestCancelOrderCommand ivcom msg.

        map pydict to ivcom msg.
        orderId required. i.e. OM2 OrderID
        """
        ## om2 order Id
        orderId = kw['orderId']
        ## same as newOrder
        clOrdId = kw['clOrdId']
        atp     = kw.get("atp",False)
        system    = kw.get("system","PlutusChild_DEV")
        userId  = kw.get("userId",os.getlogin())
        extra   = kw.get("extra", {})
        ## embedded within commandRequest
        embedded = kw.get("commandRequest",False)

        ## order creation time
        if "now" in kw:
            now = parser.parse(kw["now"])
        else:
            now = datetime.now()

        header  = self.getHeader(clOrdId,system,userId,now=now)
        external= self.getExternalRefs(clOrdId)

        order = IvComDictHelper("RequestCancelOrderCommand")
        order.set("orderId",orderId)
        order.set("commandHeader",header.msg)
        order.set("externalReferences",[external.msg])

        ##  k must be  catalog
        for k,v in extra.iteritems():
            ## ignore extra fields only valid for createOrderCommand.
            try:
                order.set(k,v)
            except AssertionError:
                log.warn("key: %s, val: %s can't be set for RequestCorrectOrderCommand" % (k,v))

        if embedded:
            commandRequest = IvComDictHelper("CommandRequest")
            requestResponseCommand = IvComDictHelper("RequestResponseCommand")
            requestResponseCommand.set("requestCancelOrderCommand",order.msg)
            commandRequest.set("requestResponseCommand",requestResponseCommand.msg)

            return commandRequest.msg

        log.info("iv msg: %s" % order.msg)
        return order.msg

    def requestCancelExecutionCommand(self,**kw):
        """ """
        execId = kw.get('executionId')
        execRefs = kw.get("execExternalRefers")
        assert execId or execRefs

        if execRefs:
            assert isinstance(execRefs,dict)

        system    = kw.get("system","PlutusChild_DEV")
        userId  = kw.get("userId",os.getlogin())
        reason =  kw.get("reason",1)
        ## embedded within commandRequest
        embedded = kw.get("commandRequest",False)

        command_table = "RequestCancelExecutionCommand"
        ## order creation time
        if "now" in kw:
            now = parser.parse(kw["now"])
        else:
            now = datetime.now()

        clOrdId = kw.get("clOrdId") or str(now)
        header  = self.getHeader(clOrdId,system,userId,now=now)
        #external= self.getExternalRefs(execId)

        order = IvComDictHelper(command_table)
        if execId:
            order.set("executionId",execId)
        order.set("commandHeader",header.msg)
        if execRefs:
            order.set("execExternalReferences",[execRefs])
        order.set("cancelReason",reason)

        if embedded:
            commandRequest = IvComDictHelper("CommandRequest")
            requestResponseCommand = IvComDictHelper("RequestResponseCommand")
            requestResponseCommand.set("requestCancelExecutionCommand",order.msg)
            commandRequest.set("requestResponseCommand",requestResponseCommand.msg)

            return commandRequest.msg



        return order.msg

    def atpOrder(self,**kw):
        """ create atp parent order .

        input:

        """
        ## order creation time
        if "now" in kw:
            now = parser.parse(kw["now"])
        else:
            now = datetime.now()

        symbol  = kw['symbol']
        clOrdId = kw['clOrdId']
        side    = kw['side']
        price   = kw['price']
        xref    = kw['xref']
        qty     = kw["qty"]
        sor     = kw["sor"]
        userId  = kw.get("userId", os.getlogin())
        system    = kw.get("system","PlutusChild_DEV")

        sorParam = kw["sorParam"]
        ## default dma
        serviceOffering = kw.get("serviceOffering",5)
        ## common part
        header  = self.getHeader(clOrdId,system,userId,now=now)
        external= self.getExternalRefs(clOrdId)
        flowAU = self.getFlowSpec(xref)

        ## createOrderCommand
        createOrderCommand = IvComDictHelper("CreateOrderCommand")
        createOrderCommand.set("commandHeader",header.msg)

        createOrderCommand.set("orderType","Limit")
        createOrderCommand.set("timeInForce","Day")
        ## parent order params
        createOrderCommand.set("tradingAlgorithm",sor)
        createOrderCommand.set("tradingAlgorithmParameters",sorParam)
        createOrderCommand.set("tradeViaInternalAlgorithm",True)
        createOrderCommand.set("algorithmicIndicator","Algorithmic")
        createOrderCommand.set("destinationTraderId",os.getlogin())

        createOrderCommand.set("quantity",qty)
        createOrderCommand.set("limitPrice",price)
        createOrderCommand.set("buySell",side)
        createOrderCommand.set("productId",symbol)
        createOrderCommand.set("productIdType","RIC")
        ## external references
        createOrderCommand.set("externalReferences",[external.msg])
        ## flow AU
        createOrderCommand.set("flowSpecificAustralia",flowAU.msg)

        return createOrderCommand.msg

############## api interface ################
class InvalidArguments(Exception):
    pass

class Om2InternalError(Exception):
    pass

import zerorpc
from conf import settings
## convert unicode to str
from utils import convert,SeqNumber

import atexit

class OM2API(object):

    """ OM2 API via rpc call.

    """
    service_ = zerorpc.Client(settings.ORDER_API_URL)

    def __init__(self):
        """ initialize"""

        self.seqNum_herme_ = SeqNumber(cfg.TMP_DIR,settings.RDS_REQ)
    def list_sessions(self):
        """ """
        return self.servcie_.list_sessions()

    def handle_status(self):
        """  """
        return self.services.handle_status()

    def new_order(self,**kw):
        """ submit a new order to ivcom via CreateOrderCommand,return ivcom response.

        input:
            - symbol
            - side
            - price
            - qty
            - clOrdId
            - xref
            - serviceOffering

        output: IvCom response, enriched with om2OrderId via db lookup.

        """
        log.info("OM2API create new order: %s" % kw)

        if 'symbol' not in kw or \
            'side' not in kw or \
            'price' not in kw or \
            'qty' not in kw or \
            'clOrdId' not in kw:
            log.error("invalid args: %s" % kw)
            raise InvalidArguments("symbol/side/price/qty/clOrdId required")

        assert kw['side'] in ('Buy','Sell','Short','SSE')

        msg = IvComOrderHelper().createOrderCommand(**kw)

        ## submit order
        if 'requestResponseCommand' in msg:
            ack = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",msg)
        else:
            ack = self.service_.send_rf_request(settings.RF_PROVIDER,"CreateOrderCommand",msg)

        assert isinstance(ack, dict ) or isinstance(ack,bool)
        log.info("ack: %s" % ack)
        return ack

    def new_childOrder(self,**kw):
        """ submit new childOrder to ivcom via CreateChildOrderCommand. """

        log.info("OM2API create new child order: %s" % kw)
        if 'symbol' not in kw or \
            'side' not in kw or \
            'price' not in kw or \
            'qty' not in kw or \
            'clOrdId' not in kw or \
            'parentOrderId' not in kw:
            log.error("invalid args: %s" % kw)
            raise InvalidArguments("symbol/side/price/qty/clOrdId/parentOrderId required")

        assert kw['side'] in ('Buy','Sell','Short','SSE')

        msg = IvComOrderHelper().createChildOrderCommand(**kw)
        ## submit order
        if 'requestResponseCommand' in msg:
            ack = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",msg)
        else:
            ack = self.service_.send_rf_request(settings.RF_PROVIDER,"CreateChildOrderCommand",msg)
        assert isinstance(ack, dict ) or isinstance(ack,bool)
        log.info("ack: %s" % ack)
        return ack

    def amend_order(self,**kw):
        """ submit amend order request to ivcom via RequestCorrectOrderCommand, return ivcom response.

        input:
            - orderId i.e. OM2 orderId
            - price or qty
            - clOrdId
            TODO: TestOrder shall enrich other fields.

        output:
            return ivcom response.
        """

        log.info("API amend order: %s" % kw)
        if 'orderId' not in kw or 'clOrdId' not in kw:
            raise InvalidArguments("orderId/clOrdId required")
        if 'price' not in kw and 'qty' not in kw:
            raise InvalidArguments("price or qty required")

        ## om2 not happy with amend with maq = -1
        if 'maq' in kw and kw['maq'] == -1:
            kw.pop('maq')
        ## validation for atp
        if 'atp' in kw and kw['atp'] == True:
            assert 'sor' in kw
            assert 'sorParam' in kw

        msg = IvComOrderHelper().requestCorrectOrderCommand(**kw)
        log.debug("amend order ivmsg: %s" % msg)

        if 'requestResponseCommand' in msg:
            res = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",msg)
        else:
            res = self.service_.send_rf_request(settings.RF_PROVIDER,"RequestCorrectOrderCommand",msg)
        return res

    def cancel_order(self,**kw):
        """ submit cancel order request to ivcom via RequestCancelOrderCommand, return ivcom response.

        innput:
            - orderId i.e. OM2 orderId
            - clOrdId
            TODO: TestOrder enrich other fields.
        output:
            return ivcom response.
        """
        log.info("API cancel order: %s" % kw)
        if 'orderId' not in kw or \
           'clOrdId' not in kw:
            raise InvalidArguments("orderId/clOrdId required")

        msg = IvComOrderHelper().requestCancelOrderCommand(**kw)

        if 'requestResponseCommand' in msg:
            res = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",msg)
        else:
            res = self.service_.send_rf_request(settings.RF_PROVIDER,"RequestCancelOrderCommand",msg)

        return res

    def requestOrderImage(self,orderId):
        """
        helper for query orderImage
        """
        order = IvComDictHelper("CommandRequest")
        requestOrderImageCommand = IvComDictHelper("RequestOrderImageCommand")
        requestOrderImageCommand.set("orderId",orderId)

        ## need wrapper
        requestRespCmd = IvComDictHelper("RequestResponseCommand")
        requestRespCmd.set("requestOrderImageCommand",requestOrderImageCommand.msg)
        order.set("requestResponseCommand",requestRespCmd.msg)
        order.set("responseVerbosity","Full")

        res = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",order.msg)
        return res

    def requestExecutionImage(self,executionId):
        """
        helper for query executionImage
        """
        order = IvComDictHelper("CommandRequest")
        requestImageCommand = IvComDictHelper("RequestExecutionImageCommand")
        requestImageCommand.set("executionId",executionId)

        ## need wrapper
        requestRespCmd = IvComDictHelper("RequestResponseCommand")
        requestRespCmd.set("requestExecutionImageCommand",requestImageCommand.msg)
        order.set("requestResponseCommand",requestRespCmd.msg)
        order.set("responseVerbosity","Full")

        res = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",order.msg)
        return res

    def cancel_execution(self,**kw):
        """ cancel execution based executionId.

        extra: for externalReferences need to be supplied.
        """
        log.info("API cancel execution: %s" % kw)
        if 'executionId' not in kw and 'execExternalReferences' not in kw:
            raise InvalidArguments("executionId or execExternalReferences required")

        msg = IvComOrderHelper().requestCancelExecutionCommand(**kw)

        if 'requestResponseCommand' in msg:
            res = self.service_.send_rf_request(settings.RF_PROVIDER,"CommandRequest",msg)
        else:
            res = self.service_.send_rf_request(settings.RF_PROVIDER,"RequestCancelExecutionCommand",msg)
        return res
        assert order and type(order) == dict

    def send_herme(self,session,order,**kw):
        """ """
        hermes_base = {
                'requestManager': session,
                'args': '',
                'guiId':  -1,
                'cmdId':  self.seqNum_herme_.next,
                'userId': os.getlogin(),
        }
        order.update(hermes_base)
        #print order
        assert session in  self.service_.list_sessions()
        res = self.service_.send_rf_request(session,"HermesCommand",convert(order))
        log.debug("rds hermes resp: :%s" % res)
        return res

    def new_atp_order(self,**kw):
        """ """
        log.info("OM2API create new atp order: %s" % kw)

        if 'symbol' not in kw or \
            'side' not in kw or \
            'price' not in kw or \
            'qty' not in kw or \
            'clOrdId' not in kw or \
            'xref' not in kw:
            log.error("invalid args: %s" % kw)
            raise InvalidArguments("symbol/side/price/qty/clOrdId/xref required")

        assert kw['side'] in ('Buy','Sell','Short','SSE')

        msg = IvComOrderHelper().atpOrder(**kw)
        om2Handler = self.service_.getRFHandler(settings.RF_REQUEST_MANAGER)
        assert om2Handler
        ## check handle status is in available before send order
        if om2Handler.status != 'Available':
            raise ValueError("om2 session [%s] not Available [%s]" % ( settings.RF_REQUEST_MANAGER,om2Handler.status))

        ## submit order
        future = om2Handler.sendOrderCommand("CreateOrderCommand",msg)
        ack =  future.result()
        assert type(ack) == dict
        log.info("ack: %s" % ack)

        if ack and 'eventIdWrapper' in ack:
            eventId = ack['eventIdWrapper']['eventId']
            ## query db for om2OrderId
            orderId = lookup_om_orderId(eventId)
            if orderId:
                ack['orderId'] = orderId
            else:
                log.error("OM2 orderId not found: %s, within timeout: %d seconds" % (ack,settings.OM2_RESP_TIMEOUT))

            ## save new order to db
            #_orders.save(dict(action="new",clOrdId=kw['clOrdId'],orderId=orderId,order=kw,timestamp=datetime.now()))
            save_order(dict(action="new",clOrdId=kw['clOrdId'],orderId=orderId,order=kw,timestamp=datetime.now()))
            return ack
        else:
            err = "CreateOrderCommand failed without eventId%s for %s" % (ack,kw)
            log.error(err)
            ## return ack or internal exception
            if ack:
                return ack
            else:
                raise Om2InternalError(err)

    def send_rf_msg(self,table,message):
        """ submit new childOrder to ivcom via CreateChildOrderCommand.

        """
        log.info("OM2API send direct rf message: table: %s, message: %s" % (table, message))

        assert isinstance(message,dict)

        command = IvComDictHelper(table)

        for k,v in message.iteritems():
            command.set(k,v)

        ack = self.service_.send_rf_request(settings.RF_PROVIDER,table,convert(command.msg))
        log.info("send rf [%s] ack: %s" % (table,ack))
        return ack



atexit.register(OM2API.service_.close)
