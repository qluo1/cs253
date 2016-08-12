""" test cases for JIM.

"""
from datetime import datetime
import time
import random
from pprint import pprint
import pytest

from utils import (
              valid_rf_ack,
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              AckFailed,
              )
from om2Order import Order
from utils import DepthStyle,SeqNumber, active_wait
from conf import settings
import gevent

#symbol = 'JBH.AX'

class Test_Price_Conversion:
    """
    Make a trade happen between an account setup for dollar translation against one setup for cent translation.
    If the adapter translator is not working correctly, not all of these would trade because the prices will be out
    by a factor of 100. Then we assert that the price on the execution is the price we first thought of.

    Sadly could not find a way to link to the resulting trade report. Plutus does not give us the OM2 ("exchange")
    order ID back over FIX.

    The two test styles are: Trade on 'new' and trade on 'amend'. We have no way of knowing what price Plutus is holding
    internally so we test amend by amending into trade with all combinations of dollar and cent translation.

    XRef TTD - Account name = TEST_DOLLARS - this has been setup as an EDGE client
    XRef TTC - Account name = TEST_CENTS - has been setup as an IOS+ client

    Both accounts are in the Default set of dark pools so are expected to trade.
    """


    """
    CHIAONLY or CHIAASX will not cause Plutus to trade.

    As exchange will reject the trade report -- Trade report with price outside the current spread.

    need maual to check trade report reject to confirm ok.
    """
    depth_styles = (
              #DepthStyle.ASXCHIA,
              DepthStyle.ASXONLY,
              #DepthStyle.CHIAASX,
              #DepthStyle.CHIAONLY,
            )

    scenarios = []

    for testStyle in ['new', 'amend']:
        for dStyle in depth_styles:
            scenarios.append(dict(sellXRef = 'TTC', buyXRef = 'TTD', testStyle = testStyle, dStyle=dStyle))
            scenarios.append(dict(sellXRef = 'TTD', buyXRef = 'TTD', testStyle = testStyle, dStyle=dStyle))
            scenarios.append(dict(sellXRef = 'TTC', buyXRef = 'TTC', testStyle = testStyle, dStyle=dStyle))
            scenarios.append(dict(sellXRef = 'TTD', buyXRef = 'TTC', testStyle = testStyle, dStyle=dStyle))

    @pytest.mark.test_price_conversion
    @pytest.mark.spanner
    @pytest.mark.trousers
    def test_price_conversion(self, sellXRef, buyXRef, testStyle, dStyle,symbol_depth):
        """ """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,with_mxq=True,style=dStyle)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        assert "MINEXECUTABLEQTY" in attrs
        mxq = int(attrs["MINEXECUTABLEQTY"])

        pprint(quote)

        # XXX clear_depth() does not clear PSGMX, it clears the exchanges. This is required
        # so that PSGMX can see the depth we build which will then cause orders inside it it to trade

        orders = []
        for side in ['Buy', 'Sell']:
            print (" ========== PLUTUSSGMX " + side + " order =============")
            psgmxTemplate = { 'symbol' : symbol, 'side' : side, 'qty' : 5 }

            psgmxTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
            if side == "Buy":
                psgmxTemplate['xref'] = buyXRef
            else:
                psgmxTemplate['xref'] = sellXRef

            if testStyle == 'amend':
                # Place orders which won't match
                if side == "Buy":
                    psgmxTemplate['price'] = last - 0.01
                else:
                    psgmxTemplate['price'] = last + 0.01
            else:
                # 'new' - straight for the throat
                psgmxTemplate['price'] = last

            psgmxOrder = Order(**psgmxTemplate)
            psgmxOrder.new()
            gevent.sleep(0.1)
            print(psgmxOrder)
            if testStyle == "amend" or side == "Buy":
                # If it trades immediately (new/Sell), expect_ok won't necessarily work because the order closes out
                psgmxOrder.expect_ok()

            childId = psgmxOrder._childs[0]
            childOrder = psgmxOrder.requestOrderImage(childId)
            print (" ========== PLUTUSSGMX " + side + " Child order =============")
            pprint(childOrder)

            if testStyle == "amend":
                psgmxOrder.amend(price = last)

            orders.append(psgmxOrder)

        try:
            for order in orders:
                order.expect("AttachExecution",timeout=60)
                print (" ========== Execution(s) =============")
                pprint(order.fills)

                executionPrice = order.fills[0].executionData['executionPrice']
                assert executionPrice-last < 0.001

                assert order.fills[0].executionData['executionPoint'] == "SYDE"
                execRefs = order.fills[0].executionData['execExternalReferences']
                tsnumber = [t['tag'] for t in execRefs if t['externalObjectIdType'] ==  "ExchangeId"]
                assert len(tsnumber) == 1
                print "tsnumber: ", int(tsnumber[0])

                tradeConditionCode = order.fills[0].executionData['execFlowSpecificAustralia']["australiaTradeConditionCode"]
                print "tradeConditionCode [" + tradeConditionCode + "]"
                ## trade condition code being preserved and pass back
                assert(tradeConditionCode == "BPXT" or tradeConditionCode == "NXXT")

        finally:
            for order in orders:
                if order.orderStatus.primaryStatus == "Working":
                    order.cancel()


class Test_AUDH1:
    """
    AUDH1 is the Delta Hedger account which has a fake XRef setup in the Order Receiver Spring config file.
    Delta Hedger is on an ancient OMA which is incapable of sending AustraliaSpecific cruft
    """
    @pytest.mark.fish_eeees
    def test_audh1(self,  symbol_depth):
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY", 100))

        pprint(quote)

        order_t = dict(symbol  = symbol,
                        side   = "Buy",
                        price  = last,
                        qty    = 10,
                        xref   = '',
                        )

        noXRefTemplate = order_t.copy()
        noXRefTemplate['extra'] = {"accounts": [{"accountAliases": [{"accountSynonymType": 3, "accountSynonym": "AUDH1"}], "accountRole": 1}]}
        noXRefTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
        noXRefOrder = Order(**noXRefTemplate)
        noXRefOrder.new()

        print (" ========== Plutus Sigma-X order without xref buy order =============")
        pprint(noXRefOrder)
        noXRefOrder.expect_ok()

        # Amend it
        noXRefOrder.amend(qty = 11)

        # Cancel it
        noXRefOrder.cancel()
        print "Order was successfully amended and canceled"

ETFS = ['IKO.AX',]
class Test_Amend_Count:
    """
    AUCEL is configured to only hold 50 external references per order. The Plutus Order Receiver adapter
    has been changed to keep 10 or less references per order to keep the FIX protocol happy. This test 
    will amend an order 100 times. Previously the last stored reference would be ~#95 rather than ~#200

    extend the test cases to cover market order type for OPEN/PRE_OPEN/PRE_CSPA.
    """
    scenarios = []

    for orderType in (
            "Limit",
            "Market",):
        for marketState in (
                        'OPEN',
                        'PRE_OPEN',
                        'PRE_CSPA',):
            scenarios.append(dict(orderType=orderType,marketState=marketState))

    def test_amend_count(self,orderType, marketState,symbol_depth):
        try:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(state=marketState,top200=True,blacklist=ETFS)
            bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
            mxq = int(attrs.get("MINEXECUTABLEQTY",100))
            pprint(quote)
        except Exception,e:
            if e.msg.startswith("no test symbols available"):
                pytest.skip(e)

        order_t = dict(symbol  = symbol,
                        side   = "Buy",
                        price  = last,
                        qty    = 1,
                        xref   = 'FC2',
                        orderType = orderType,
                        #extra= {'businessUnit': 'DMA'},
                        )

        if orderType == "Market":
            order_t['price'] = 0
        psgmxBuyTemplate = order_t.copy()
        psgmxBuyTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
        psgmxBuyOrder = Order(**psgmxBuyTemplate)
        psgmxBuyOrder.new()
        print (" ========== PLUTUSSGMX buy order =============")
        print(psgmxBuyOrder)
        psgmxBuyOrder.expect_ok()

        # Perform 100 amends, then check the external references
        for new_qty in range(2,102):
            psgmxBuyOrder.amend(qty = new_qty)

        childId = psgmxBuyOrder._childs[0]
        childOrder = psgmxBuyOrder.requestOrderImage(childId)
        print (" ========== PLUTUSSGMX child order =============")
        pprint(childOrder)

        # Colt version tags in the adapter increment by 2 per amend. If the 50 limit is hit
        # the version will be stuck around 95-100.  We need to ensure it's close to 200 in this
        # case.
        latestColtVersionTag = childOrder['orderStatusData']['externalReferences'][-1]['tag']
        if "-" in latestColtVersionTag:
            coltVersionInteger = int(latestColtVersionTag.split('-')[1])
            print "FIX order version: ", coltVersionInteger
            coltTagCount = 0
            for extRef in childOrder['orderStatusData']['externalReferences']:
                if extRef['systemName'] == 'PlutusSGMX-Colt':
                    coltTagCount = coltTagCount + 1

            print "[" + str(coltTagCount) + "] 'PlutusSGMX-Colt' tags"
            assert(coltVersionInteger >= 199)
            assert(coltTagCount >= 3 and coltTagCount <= 12)
        else:
            ## this is X3
            print latestColtVersionTag

        psgmxBuyOrder.cancel()

class Test_GSET_DMA_XREF_Override:
    """
    system not like 'Plutus%'
    and businessUnit = "DMA"
    and missing xref from order request.

    xref will be override to GSV (for agency)  or GPR (for principal)
    """
    scenarios = [
                {'capacity': 'Agency'},
                {'capacity': 'Principal'},
            ]
    def test_order(self, capacity, symbol_depth):

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY",100))

        pprint(quote)

        order_t = dict(symbol  = symbol,
                        side   = "Buy",
                        price  = last,
                        qty    = 1,
                        extra = {"businessUnit":"DMA","serviceOffering":"GSAT"},
                        system = "IOSAdapter",
                        capacity = capacity,
                        )

        psgmxBuyTemplate = order_t.copy()
        psgmxBuyTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
        psgmxBuyOrder = Order(**psgmxBuyTemplate)
        psgmxBuyOrder.new()
        print (" ========== PLUTUSSGMX buy order =============")
        print(psgmxBuyOrder)
        psgmxBuyOrder.expect_ok()

        try:
            # Perform 100 amends, then check the external references
            for new_qty in range(2,102):
                psgmxBuyOrder.amend(qty = new_qty)

            childId = psgmxBuyOrder._childs[0]
            childOrder = psgmxBuyOrder.requestOrderImage(childId)
            print (" ========== PLUTUSSGMX child order =============")
            pprint(childOrder)
            ## GSET bucket account xref override
            xref = childOrder['orderInstructionData']['flowSpecificAustralia']['iosAccountExchangeCrossReference']
            orderCapacity =  childOrder['orderInstructionData']['orderCapacity']

            #import pdb;pdb.set_trace()
            if capacity == "Agency":
                assert xref == "GSV"
                assert orderCapacity == capacity
            else:
                assert xref == "GPR"
                assert orderCapacity == capacity

            # Colt version tags in the adapter increment by 2 per amend. If the 50 limit is hit
            # the version will be stuck around 95-100.  We need to ensure it's close to 200 in this
            # case.
            latestColtVersionTag = childOrder['orderStatusData']['externalReferences'][-1]['tag']
            coltVersionInteger = int(latestColtVersionTag.split('-')[1])
            print "FIX order version: ", coltVersionInteger
            coltTagCount = 0
            for extRef in childOrder['orderStatusData']['externalReferences']:
                if extRef['systemName'] == 'PlutusSGMX-Colt':
                    coltTagCount = coltTagCount + 1

            print "[" + str(coltTagCount) + "] 'PlutusSGMX-Colt' tags"

            assert(coltVersionInteger >= 199)
            assert(coltTagCount >= 3 and coltTagCount <= 12)
        finally:
            ## clean up
            psgmxBuyOrder.cancel()

class Test_Execution_Capacity:
    """
    FC4 - FACIL4. Should be house
    FC2 - FACIL2. Should be house
    MD1 - GREENCAPE. Should be client
    GI2 - DJERRIWAR. Should be client

    ## add currency as AUD/USD.
    """

    scenarios = []

    for currency in ('USD','AUD','NZD'):
        for orderType in ("Limit","Market"):
            scenarios.append(dict(sellXRef = 'FC4', buyXRef = 'MD1', expectedSellExecCapacity = 'CrossAsAgent',
                expectedBuyExecCapacity = 'CrossAsPrincipal',
                currency = currency,
                orderType=orderType))  # principal/agency
            scenarios.append(dict(sellXRef = 'FC4', buyXRef = 'FC2', expectedSellExecCapacity = 'CrossAsPrincipal',
                expectedBuyExecCapacity = 'CrossAsPrincipal',currency=currency,orderType=orderType))  # principal/principal
            scenarios.append(dict(sellXRef = 'MD1', buyXRef = 'GI2', expectedSellExecCapacity = 'CrossAsAgent',
                expectedBuyExecCapacity = 'CrossAsAgent', currency=currency,orderType=orderType))  # agency/agency

    @pytest.mark.test_execution_capacity
    def test_execution_capacity(self, sellXRef, buyXRef, expectedSellExecCapacity, expectedBuyExecCapacity, currency,orderType,symbol_depth):
        """ """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,with_mxq=True,top200=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        assert "MINEXECUTABLEQTY" in attrs
        mxq = int(attrs["MINEXECUTABLEQTY"])

        pprint(quote)

        orders = []
        for side in ['Buy', 'Sell']:
            print (" ========== PLUTUSSGMX " + side + " order =============")
            psgmxTemplate = { 'symbol' : symbol, 'side' : side, 'qty' : 15 }

            psgmxTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
            ## adapter should ignore currency
            psgmxTemplate.update({'extra': {'executionCurrency': currency,
                                            'settlementCurrency': currency,
                                 }
                });
            if side == "Buy":
                psgmxTemplate['xref'] = buyXRef
            else:
                psgmxTemplate['xref'] = sellXRef

            if orderType == "Limit":
                psgmxTemplate['price'] = last
            else:
                psgmxTemplate["orderType"] = "Market"
                psgmxTemplate['price'] = 0

            psgmxOrder = Order(**psgmxTemplate)
            psgmxOrder.new()
            gevent.sleep(0.1)
            print(psgmxOrder)
            if side == "Buy":
                # If it trades immediately (new/Sell), expect_ok won't necessarily work because the order closes out
                psgmxOrder.expect_ok()

            childId = psgmxOrder._childs[0]
            childOrder = psgmxOrder.requestOrderImage(childId)
            print (" ========== PLUTUSSGMX " + side + " Child order =============")
            pprint(childOrder)

            orders.append(psgmxOrder)

        for order in orders:
            order.expect("AttachExecution",timeout=240)
            print (" ========== Execution(s) =============")
            pprint(order.fills)


            executionCapacity = order.fills[0].executionData['executionCapacity']
            print "*** executionCapacity [" + executionCapacity + "] ***"
            assert order.fills[0].executionData['executionPoint'] == "SYDE"

            execRefs = order.fills[0].executionData['execExternalReferences']
            tsnumber = [t['tag'] for t in execRefs if t['externalObjectIdType'] ==  "ExchangeId"]
            assert len(tsnumber) == 1
            print "tsnumber: ", int(tsnumber[0])

            print "*** DUNG ***"
            pprint(order.orderInst)
            expectedExecCapacity = expectedSellExecCapacity
            if order.orderInst.buySell == 'Buy':
                expectedExecCapacity = expectedBuyExecCapacity

            assert(executionCapacity == expectedExecCapacity)

class Test_Cross_Party_Order_Capacity:
    """
    FC4 - FACIL4. Should be house
    FC2 - FACIL2. Should be house
    MD1 - GREENCAPE. Should be client
    GI2 - DJERRIWAR. Should be client
    OF1 - EASR. Mixed capacity account
    OPM - MIXEDBLOCK. Mixed capacity account
    ... I wonder if xref "OPM" stands for "Other People's Money"?
    """

    scenarios = []
    scenarios.append(dict(sellXRef = 'FC4', buyXRef = 'FC2', expectedSellCrossCapacity = 'Principal', expectedBuyCrossCapacity = 'Principal'))
    scenarios.append(dict(sellXRef = 'FC4', buyXRef = 'MD1', expectedSellCrossCapacity = 'Agency', expectedBuyCrossCapacity = 'Principal'))
    scenarios.append(dict(sellXRef = 'MD1', buyXRef = 'GI2', expectedSellCrossCapacity = 'Agency', expectedBuyCrossCapacity = 'Agency'))
    scenarios.append(dict(sellXRef = 'OF1', buyXRef = 'GI2', expectedSellCrossCapacity = 'Agency', expectedBuyCrossCapacity = 'Combined'))
    scenarios.append(dict(sellXRef = 'OF1', buyXRef = 'FC4', expectedSellCrossCapacity = 'Principal', expectedBuyCrossCapacity = 'Combined'))
    scenarios.append(dict(sellXRef = 'OF1', buyXRef = 'OPM', expectedSellCrossCapacity = 'Combined', expectedBuyCrossCapacity = 'Combined'))

    @pytest.mark.test_cross_party_order_capacity
    def test_cross_party_order_capacity(self, sellXRef, buyXRef, expectedSellCrossCapacity, expectedBuyCrossCapacity, symbol_depth):
        """ """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True,with_mxq=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        assert "MINEXECUTABLEQTY" in attrs
        mxq = int(attrs["MINEXECUTABLEQTY"])

        pprint(quote)

        orders = []
        for side in ['Buy', 'Sell']:
            print (" ========== PLUTUSSGMX " + side + " order =============")
            psgmxTemplate = { 'symbol' : symbol, 'side' : side, 'qty' : 5 }

            psgmxTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
            if side == "Buy":
                psgmxTemplate['xref'] = buyXRef
            else:
                psgmxTemplate['xref'] = sellXRef

            psgmxTemplate['price'] = last

            psgmxOrder = Order(**psgmxTemplate)
            psgmxOrder.new()
            gevent.sleep(0.1)
            print(psgmxOrder)
            if side == "Buy":
                # If it trades immediately (new/Sell), expect_ok won't necessarily work because the order closes out
                psgmxOrder.expect_ok()

            childId = psgmxOrder._childs[0]
            childOrder = psgmxOrder.requestOrderImage(childId)
            print (" ========== PLUTUSSGMX " + side + " Child order =============")
            pprint(childOrder)

            orders.append(psgmxOrder)

        for order in orders:
            order.expect("AttachExecution",timeout=120)
            print (" ========== Execution(s) =============")
            pprint(order.fills)


            crossPartyOrderCapacity = order.fills[0].executionData['crossPartyOrderCapacity']['orderCapacity']
            print "*** crossPartyOrderCapacity [" + crossPartyOrderCapacity + "] ***"

            assert order.fills[0].executionData['executionPoint'] == "SYDE"
            execRefs = order.fills[0].executionData['execExternalReferences']
            tsnumber = [t['tag'] for t in execRefs if t['externalObjectIdType'] ==  "ExchangeId"]
            assert len(tsnumber) == 1
            print "tsnumber: ", int(tsnumber[0])

            print "*** DUNG ***"
            pprint(order.orderInst)
            expectedCrossCapacity = expectedSellCrossCapacity
            if order.orderInst.buySell == 'Buy':
                expectedCrossCapacity = expectedBuyCrossCapacity

            assert(crossPartyOrderCapacity == expectedCrossCapacity)

class Test_Simulate_Accept_Fill_Cancel:
    """ """
    seqNum_ = SeqNumber(settings.TMP_DIR,"SIGMX")

    scenarios = []
    for i in range(20):
        for flag in (True,False):
            scenarios.append({'run': i, 'partialFill': flag})

    def _prepare_accept_child_order(self,child):
        """
        [160608 09:39:03.463588] AcceptOrderCommand<164>
            commandHeader[1]=[
                {
                CommandHeader<55>
                    commandTime="06/08/2016 09:39:03 EST"
                    isPosDup=true
                    posDupId="PPEAUCEA220160608O-1"
                    systemName="PlutusSGMX"
                    creatorId="sausage"
                    creatorIdType=External
                    systemType=AlgorithmEngine
                }
            ]
            externalReferences[2]=[
                {
                ExternalReference<42>
                    systemName="PlutusSGMX-Colt"
                    tag="PPEAUCEA220160608O-1"
                    externalObjectIdType=FixOrderId
                }
                {
                ExternalReference<25>
                    systemName="PlutusSGMX"
                    tag="0-3e1-rq"
                    externalObjectIdType=FixOrderId
                }
            ]
            orderId="PPEAUCEA220160608O"
            quantityRemaining=5

        """
        assert isinstance(child,dict)

        childStatus = child['orderStatusData']
        childOrderId = childStatus['orderId']
        childPrimaryStatus = childStatus['primaryStatus']
        if  childPrimaryStatus != "New":
            return pytest.skip("child order already accepted")

        childOrdInst = child['orderInstructionData']
        destination = childOrdInst['destinationParty']
        destId = destination['destinationId']
        assert destId == "PLUTUSSGMX"
        assert childOrdInst['isLeafOrder'] == 1
        qty = childOrdInst['quantity']

        ## prepare accept
        utcnow = datetime.utcnow()
        now = time.mktime(utcnow.timetuple())
        uid = self.seqNum_.next

        acceptOrder = {
                'commandHeader':
                    {
                        'commandTime': now,
                        'isPosDup': True,
                        'posDupId': "%s-1" % childOrderId,
                        'systemName': "PlutusSGMX",
                        'creatorId': "bot",
                        'creatorIdType': "External",
                        'systemType': "AlgorithmEngine",
                    }
                ,
                'externalReferences': [
                    {
                        'systemName': "PlutusSGMX-colt",
                        'tag': "%s-1" % childOrderId,
                        'externalObjectIdType': "FixOrderId",
                    },
                    {
                        'systemName': "bot",
                        'tag': uid,
                        'externalObjectIdType': "FixOrderId",
                    }
                    ],
            'orderId': childOrderId,
            'quantityRemaining': qty,
        }

        return acceptOrder

    def _prepare_fill_child_order(self,child,partialFill=True):
        """
          [160608 09:52:59.044694] CreateExecutionCommand<177>
            commandHeader[1]=[ 
                {
                CommandHeader<45> 
                    commandTime="06/08/2016 09:52:58 EST"
                    isPosDup=true
                    posDupId="0-3e1-rq-5"
                    systemName="PlutusSGMX"
                    creatorId="sausage"
                    creatorIdType=External
                    systemType=AlgorithmEngine
                }
            ]
            orderId="PPEAUCEA220160608O"
            execExternalReferences[1]=[ 
                {
                ExternalReference<36> 
                    systemName="PlutusSGMXExec"
                    tag="0-3e1-rq-5"
                    tagDate="06/08/2016 00:00:00 EST"
                    externalObjectIdType=OmId
                }
            ]
            quantity=1
            executionPrice=124.4
            executionTime="06/08/2016 09:52:58 EST"
            subExecutionPoint="XASX"
            executionVenue="SYDE"
            executionLastMarket="XASX"
            executionReason=AutomatedExecution
            exchangeExecutionId="0-3e1-rq-5"
            execFlowSpecificAustralia[1]=[ 
                {
                ExecFlowSpecificAustralia<5> 
                    australiaTradeConditionCode="XT"
                }
            ]

        """
        assert isinstance(child,dict)

        childStatus = child['orderStatusData']
        childOrderId = childStatus['orderId']
        childPrimaryStatus = childStatus['primaryStatus']

        childOrdInst = child['orderInstructionData']
        destination = childOrdInst['destinationParty']
        destId = destination['destinationId']
        assert destId == "PLUTUSSGMX"
        assert childOrdInst['isLeafOrder'] == 1
        qty = childOrdInst['quantity']
        price = childOrdInst['limitPrice']

        fillQty = qty if not partialFill else qty - 1

        ## prepare accept
        utcnow = datetime.utcnow()
        now = time.mktime(utcnow.timetuple())

        uid = self.seqNum_.next
        e_uid = "E-%s" % uid
        fillOrder = {
              'commandHeader':
                {
                    'commandTime': now ,
                    'isPosDup': True,
                    'posDupId': uid,
                    'systemName': "PlutusSGMX",
                    'creatorId': "bot",
                    'creatorIdType': "External",
                    'systemType': "AlgorithmEngine",
                },
                'orderId': childOrderId,
                'execExternalReferences': [
                {
                    'systemName':"PlutusSGMXExec",
                    'tag': uid,
                    'tagDate': now,
                    'externalObjectIdType': "OmId",
                }
                ],
                "quantity": fillQty,
                "executionPrice": price,
                "executionTime": now,
                "subExecutionPoint": "XASX",
                "executionVenue": "SYDE",
                "executionLastMarket": "XASX",
                "executionReason": "AutomatedExecution",
                "exchangeExecutionId": e_uid,
                "execFlowSpecificAustralia":
                    {
                        'australiaTradeConditionCode': "XT",
                    }
                }

        return fillOrder

    def _prepare_forceCancel_child_order(self,child):
        """
            [160608 09:53:13.763656] ForceCancelOrderCommand<131>
            commandHeader[1]=[
                {
                CommandHeader<58>
                    commandTime="06/08/2016 09:53:13 EST"
                    isPosDup=true
                    posDupId="PPEAUCEA220160608O-1-FC"
                    systemName="PlutusSGMX"
                    creatorId="sausage"
                    creatorIdType=External
                    systemType=AlgorithmEngine
                }
            ]
            externalReferences[1]=[
                {
                ExternalReference<42> 
                    systemName="PlutusSGMX-Colt"
                    tag="PPEAUCEA220160608O-1"
                    externalObjectIdType=FixOrderId
                }
            ]
            orderId="PPEAUCEA220160608O"

        """
        assert isinstance(child,dict)

        childStatus = child['orderStatusData']
        childOrderId = childStatus['orderId']
        childPrimaryStatus = childStatus['primaryStatus']

        childOrdInst = child['orderInstructionData']
        destination = childOrdInst['destinationParty']
        destId = destination['destinationId']
        assert destId == "PLUTUSSGMX"
        assert childOrdInst['isLeafOrder'] == 1
        qty = childOrdInst['quantity']

        ## prepare accept
        utcnow = datetime.utcnow()
        now = time.mktime(utcnow.timetuple())
        uid = self.seqNum_.next

        forceCancelOrder = {
              'commandHeader': {
                    'commandTime': now ,
                    'isPosDup': True,
                    'posDupId': "%s-FC" % uid,
                    'systemName': "PlutusSGMX",
                    'creatorId': "bot",
                    'creatorIdType': "External",
                    'systemType': "AlgorithmEngine",
                },
                'externalReferences': [
                    {
                        'systemName':"PlutusSGMX",
                        'tag': "%s-1" % childOrderId,
                        'tagDate': now,
                        'externalObjectIdType': "FixOrderId",
                    }
                ],
                'orderId': childOrderId,
            }

        return forceCancelOrder

    def _prepare_rejectCancelCommand(self,child):
        """ """
        assert isinstance(child,dict)

        childStatus = child['orderStatusData']
        childOrderId = childStatus['orderId']
        childPrimaryStatus = childStatus['primaryStatus']

        childOrdInst = child['orderInstructionData']
        destination = childOrdInst['destinationParty']
        destId = destination['destinationId']
        assert destId == "PLUTUSSGMX"
        assert childOrdInst['isLeafOrder'] == 1
        qty = childOrdInst['quantity']

        ## prepare accept
        utcnow = datetime.utcnow()
        now = time.mktime(utcnow.timetuple())
        uid = self.seqNum_.next

        rejectCancel = {
              'commandHeader': {
                    'commandTime': now ,
                    'isPosDup': True,
                    'posDupId': "%s-FC" % uid,
                    'systemName': "PlutusSGMX",
                    'creatorId': "bot",
                    'creatorIdType': "External",
                    'systemType': "AlgorithmEngine",
                },
                'externalReferences': [
                    {
                        'systemName':"PlutusSGMX",
                        'tag': "%s-1" % childOrderId,
                        'tagDate': now,
                        'externalObjectIdType': "FixOrderId",
                    }
                ],
                'orderId': childOrderId,
                'rejectReasonText': "Too last to cancel",
                'rejectReasons': {
                    'rejectReasonType': 5,
                    'rejectingSystem': 8, ## MatchingEngine
                    'rejectReasonText': "Too last to cancel",
                }
            }

        return rejectCancel
    @pytest.mark.skipif("True")
    def test_production_bug(self, run,partialFill, symbol_depth):
        """ reproduce production bug:

            -   Upstream SOR_AUSigmaX order to SigmaX via SOR
            -   Upstream cancels the order. OM2 will put the SOR child in PendingCancel
            -   Simulate or send Fill from SigmaX Adapter
            -   Simulate or send Cancel Reject from SigmaX Adapter (too late to cancel)

            [160608 15:30:55.055] SorUtilityAlgoActionTask-W-t@5967-Commit [1884] Internal Error , could not find algo param context for parent [QAEAUCEA87520160608O]

            #0  0x00007ffff16058a5 in raise () from /lib64/libc.so.6
            #1  0x00007ffff160700d in abort () from /lib64/libc.so.6
            #2  0x00007ffff15fea1e in __assert_fail_base () from /lib64/libc.so.6
            #3  0x00007ffff15feae0 in __assert_fail () from /lib64/libc.so.6
            #4  0x0000000004dcfa50 in boost::shared_ptr<SorUtilAlgoParamContext>::operator->() const ()
            #5  0x0000000004eaf1ea in SorUtilityAlgoActionTask::onChildEvent(OmOrder&, OmOrder&, Sigma::ChildOrderEvent) ()
            #6  0x0000000004dcc2de in SorUtilityAlgoGameplan::onChildEvent(OmOrder&, Sigma::ChildOrderEvent) ()
            #7  0x0000000004d52ad6 in SorSigmaOrderRouter::onSORInitiatedEvent(OmOrder&, Sigma::ChildOrderEvent) ()
            #8  0x0000000004c167f6 in OmSmartRoutedOrderManagerOnRejectOrderCancelListener::onRejectOrderCancel(OmOrder const*, OmRejectReason const*) ()
            #9  0x0000000003b4111b in OmWorkFlowListenerList<OmWfRejectOrderCancelListener, OmWfOrderFilter, OmRejectOrderCancelActor, OmOrderFilterFunctor>::act(OmBusinessObjectSet&, bool) ()
            #10 0x0000000003add6d1 in OmWorkFlowDispatcherImpl::dispatch() ()

        """

        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY",10))

        side = random.choice(['Buy','Sell'])
        XRef = random.choice(["FC2","FC3"])

        pprint(quote)
        psgmxTemplate = { 'symbol' : symbol, 'side' : side, 'qty' : 5 }

        psgmxTemplate.update(settings.DARK_ORDER_TYPES['sigmax'])
        psgmxTemplate['xref'] = XRef
        psgmxTemplate['price'] = last

        psgmxOrder = Order(**psgmxTemplate)
        psgmxOrder.new()
        print(psgmxOrder)
        active_wait(lambda: len(psgmxOrder._childs) ==1,timeout=30)
        assert len(psgmxOrder._childs) == 1
        childId = psgmxOrder._childs[0]
        childOrder = psgmxOrder.requestOrderImage(childId)

        #pytest.set_trace()
        acceptOrderCmd = self._prepare_accept_child_order(childOrder)
        ## partial or full fill child order.
        fillOrderCmd = self._prepare_fill_child_order(childOrder,partialFill)
        forceCancelOrderCmd = self._prepare_forceCancel_child_order(childOrder)
        rejectCancelOrderCmd = self._prepare_rejectCancelCommand(childOrder)

        ack = psgmxOrder.sendRF("AcceptOrderCommand",acceptOrderCmd)
        assert ack
        assert ack['wasCommandSuccessful'] == 1
        ### cancel parent order
        psgmxOrder.cancel(validate=False)
        ## 
        ack  =psgmxOrder.sendRF("CreateExecutionCommand",fillOrderCmd,wait=False)
        assert ack

        #ack = psgmxOrder.sendRF("ForceCancelOrderCommand",forceCancelOrderCmd,wait=False)
        if not partialFill:
            ack = psgmxOrder.sendRF("RejectCancelOrderCommand",rejectCancelOrderCmd,wait=False)
            assert ack['wasCommandSuccessful'] == 0
        else:
            ##
            ack = psgmxOrder.sendRF("ForceCancelOrderCommand",forceCancelOrderCmd,wait=False)
            assert ack['wasCommandSuccessful'] == 1

        ##validation
        active_wait(lambda: psgmxOrder.orderStatus.primaryStatus == "Complete")
        if partialFill:
            assert psgmxOrder.orderStatus.primaryStatus == "Complete"
        else:
            ## cancel will be rejected
            assert psgmxOrder.orderStatus.primaryStatus == "Working"
            ## previous order status will be in completed.
            assert psgmxOrder.hist(last=False)[-2].orderStatus.primaryStatus == "Complete"

