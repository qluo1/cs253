""" OM2 test cases for order with Standing Instruction.

split out of order_basic.py but only cover SI  test scenarios.

handle incompatiable SI reject.
handle new sor dark /dualPost.

"""

import time
import random
from pprint import pprint
from itertools import chain
import math
import re
import pytest
import gevent
from datetime import datetime,timedelta
import gevent
from functools import partial
## local scripts
from utils import (
                  tickSize,
                  halfTick,
                  get_passive_price,
                  opposite_side,
                  getPegOrderType,
                  PegType,
                  AckFailed,
                  active_wait,
                  )
from clientOrderId import clientOrderId

from om2Order import Order

from conf import settings

import importlib
mod = importlib.import_module(settings.RDS_TEST_DATA)
## load reg test data from module
rdsTestData = mod.RDSTestData()
## select sample of test xrefs
test_xrefs = rdsTestData.si_xrefs()

from val_regdata import val_reg_data,val_si_data

##############################################
## SOR_DIRECT will not be override
## ASXSWEEP is SOR order type
SOR_DIRECT = ('asx','asx_mid','asx_bid','asx_ask','chia','chia_mid','chia_bid','chia_ask',
              'asxc','asxcb','asxsb','asxs',)

### SI incompitable with following direct order type will be rejected.
SOR_SI_DIRECT_REJECT = ['asx_mid','asx_bid','asx_ask','asxc','asxcb','chia','chia_mid','chia_bid','chia_ask']
SOR_SI_DIRECT_REJECT_NOCP = [s for s in SOR_SI_DIRECT_REJECT if not s.startswith("asxc")]

SOR_DARK = ['audarkcp','audarkExchix','audarkExchixMxq','audark','audarkMxq','sigmax']
SOR_DARK_NOCP = [s for s in SOR_DARK if  s != 'audarkcp']

IN_COMPATIABLE_SI_SOR = {
    'BestPriceMinValue'         : SOR_DARK + SOR_SI_DIRECT_REJECT,
    'BestPriceMinQtyNoLit'      : SOR_DARK_NOCP,
    'BestPriceMinQtyNoLitUni'   : SOR_DARK_NOCP,
    'ASXOnly'                   : SOR_DARK_NOCP + SOR_SI_DIRECT_REJECT_NOCP,
    'ASXDirect'                 : SOR_DARK + SOR_SI_DIRECT_REJECT,
}

## sor compitable with SI sor will override SI SOR
COMPATIABLE_SI_SOR = {
    'audarkcp': {
                 'sor': ('ASXOnly','BestPriceMinQtyNoLit','BestPriceMinQtyNoLitUni'),
                 'si_sor': 'CENTREPOINT'
                },
}

class Test_Order_Basic:

    """ @Test: Test all standard order types for new/amend/cancel.

    @Feature: 1) regulatory data validation
              2) standing instruction validation.

    """

    scenarios = []

    tifs = ("Day","GoodTillCancelled","GoodTillDate")

    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)
    test_order_types.update(settings.DARK_ORDER_TYPES)

    for sor in test_order_types:
        for xref in test_xrefs:
            for tif in tifs:
                ## GTD only asx
                if tif != "Day" and sor not in ("asx","asx_bid","asx_ask","asxs") : continue
                data = dict(tif=tif,sor=sor,xref=xref,qualifier="xref")
                scenarios.append(data)

    def test_new_amend_cancel(self,tif,sor,xref,qualifier,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote,attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        ## random side reduce amount of tests
        side = random.choice(settings.TEST_SIDES)
        delta = -1 if side == "Buy" else 1

        # using ticker
        mxq = attrs.get("MINEXECUTABLEQTY")
        ## check price not breach priceStep
        price = get_passive_price(side,quote)
        print "=== market quote / passsive price ==="
        pprint(quote)
        print price, side, attrs
        ## lookup reg data
        regdata = rdsTestData.get(xref,qualifier=qualifier)

        print " === regdata === "
        pprint(regdata)
        assert "SORSTRATEGYOVERRIDE" in regdata
        si_sor = regdata["SORSTRATEGYOVERRIDE"]

        order = dict(symbol =symbol,
                     side   =side,
                     price  =price,
                     qty    =random.randint(500,1000),
                     tif    =tif,
                     extra = {},
                     )

        if 'oeid' == qualifier:
            order['extra']['customerOeId'] = xref
        elif 'starid' == qualifier:
            order['extra']['clientStarId'] = xref
        elif 'xref' == qualifier:
            order['xref'] = xref
        elif 'tam' == qualifier:
            order['account'] = xref
        else:
            assert False, "unknown qualifier"

        ## update tags
        order.update(self.test_order_types[sor])

        ## expire in 3 days
        if tif == "GoodTillDate":
            utcnow = datetime.utcnow() + timedelta(days=3)
            order['extra']['expirationDateTime'] = time.mktime(utcnow.timetuple())

        ## test  BPMV
        if si_sor == "BestPriceMinValue":
            ## for buy side make sure order value > 120k
            if side == 'Buy':
                minQty = 120005.0 / order['price']
                order['qty'] = round(minQty) + 10

        print " ==== order data === "
        pprint(order)
        ##
        test_order = Order(**order)
        ###########################################
        try:
            clOrdId,_ = test_order.new()
            test_order.expect_ok()
        except (AckFailed,ValueError),e:
            if si_sor in IN_COMPATIABLE_SI_SOR and sor in IN_COMPATIABLE_SI_SOR[si_sor]:
                if isinstance(e,AckFailed):
                    rejectReasons =  e.message['rejectReasons']
                else:
                    assert isinstance(e,ValueError)
                    assert test_order.events()[-1] == 'OrderEntryFailure'
                    rejectReasons = test_order.hist()[-1].orderStatus.rejectReasons
                assert rejectReasons[0]['rejectReasonText'] == 'Validation failed: Incompatible with StandingInstruction'
                assert rejectReasons[0]['rejectingSystem'] == "Rules"
                assert rejectReasons[0]['rejectReasonType'] == "InvalidOrderType"
                return

            else:
                raise

        acks =  test_order.events()
        print "orderId,%s, %s" % (test_order.orderId,acks)

        ##  override to compatiable SOR
        if sor in COMPATIABLE_SI_SOR and si_sor in COMPATIABLE_SI_SOR[sor]['sor']:
            si_sor = COMPATIABLE_SI_SOR[sor]['si_sor']

        ######################################
        ### validate order regdata for new
        val_reg_data(test_order.orderInst,qualifier,xref,regdata)
        ######################################
        ### validate si for new
        if sor not in SOR_DIRECT:
            val_si_data(test_order,sor,si_sor,mxq,xref)
            ## validate possive 
            if si_sor in IN_COMPATIABLE_SI_SOR: assert sor not in IN_COMPATIABLE_SI_SOR[si_sor]
        else:
            val_si_data(test_order,sor,sor,mxq,xref)

        ###################################################
        ## exclude dark amend bug on SI override
        if sor in settings.SOR_DARK:
            return

        ## amend qty down
        clOrdId,_ = test_order.amend(qty = order['qty']-100)
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend qty, %s, %s" % (clOrdId,acks)
        ## amend price passive
        clOrdId,_ = test_order.amend(price = price  + tickSize(price,delta))
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend price, %s, %s" % (clOrdId,acks)
        ## amend both price/qty
        clOrdId,_ = test_order.amend(price = price + tickSize(price,delta),
                                     qty = order['qty'] + 200)
        #print "amend: %s, %s" % amend_ack
        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend qty/price, %s, %s" % (clOrdId,acks)
        ######################################
        ### validate order regdata for amend
        val_reg_data(test_order.orderInst,qualifier,xref,regdata)
        ######################################
        ### validate si for amend
        if sor not in SOR_DIRECT:
            val_si_data(test_order,sor,si_sor,mxq,xref)

        clOrdId,_ = test_order.cancel()
        acks =  test_order.events(clOrdId)
        print "cancel: %s , %s" % (clOrdId,acks)

class Test_FAKFOK:

    """ @Test IOC-FAK/FOK for all standard order types except FAK for ASXS/ASXCB.

    @Feature: FAK/FOK, no trade expected.

    all uni-sor, will be converted into NO uni sor internally.

    """

    scenarios = []

    ## FAK or IOC
    allOrNones = (True,False)

    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)
    test_order_types.update(settings.DARK_ORDER_TYPES)
    ## 'Validation failed: Direct orders to Sigma-X are not supported'
    if 'sigmax' in test_order_types:
        test_order_types.pop("sigmax")

    for sor in test_order_types:
        for xref in test_xrefs:
            regdata = rdsTestData.get(xref)
            for allOrNone in allOrNones:
                ## not valid ASX order type
                if  allOrNone == True and sor in ('asxs','asxcb','asxsb','asxsweep'):
                    continue
                data = dict(sor=sor,xref=xref,allOrNone=allOrNone)
                scenarios.append(data)

    def test_order(self,sor,xref,allOrNone,symbol_depth):
        """ test FOK order type. """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        mxq = attrs.get("MINEXECUTABLEQTY")

        ## random side reduce amount of tests
        side = random.choice(settings.TEST_SIDES)

        price = get_passive_price(side,quote)
        ## lookup reg data
        regdata = rdsTestData.get(xref)
        print " === regdata === "
        pprint(regdata)
        assert "SORSTRATEGYOVERRIDE" in regdata
        si_sor = regdata["SORSTRATEGYOVERRIDE"]

        order = dict(symbol=symbol,
                     side=side,
                     price=price,
                     tif="ImmediateOrCancel",
                     allOrNone=allOrNone,
                     qty=random.randint(100,1000),
                     xref=xref)

        tags = self.test_order_types[sor]
        order.update(tags)
        #if sor in ('asxcb',) and 'blockLimit' in inst:
        #    order['qty'] = round(inst['blockLimit'] / price ) + 10
        pprint(order)

        print("======== quote ========")
        pprint(quote)
        test_order = Order(**order)
        ###########################################
        try:
            clOrdId,_ = test_order.new()
            test_order.expect("OrderAccept")
        except AckFailed,e:
            if si_sor in IN_COMPATIABLE_SI_SOR and sor in IN_COMPATIABLE_SI_SOR[si_sor]:
                rejectReasons =  e.message['rejectReasons']
                assert rejectReasons[0]['rejectReasonText'] == 'Validation failed: Incompatible with StandingInstruction'
                assert rejectReasons[0]['rejectingSystem'] == "Rules"
                assert rejectReasons[0]['rejectReasonType'] == "InvalidOrderType"
                return
            else:
                raise

        print "new order  %s" % test_order
        ### validate order regdata for new
        val_reg_data(test_order.orderInst,"xref",xref,regdata)
        ######################################
        ### validate si for new, si only applicable for SOR order type
        ##  override to compatiable SOR
        if sor in COMPATIABLE_SI_SOR and si_sor in COMPATIABLE_SI_SOR[sor]['sor']:
            si_sor = COMPATIABLE_SI_SOR[sor]['si_sor']
        if sor not in SOR_DIRECT:
            ## uni-sor internal converted as no uni for IOC
            ##http://eq-trading.jira.services.gs.com/jira/browse/ANZIN-269
            if si_sor == 'BestPriceMinQtyNoLitUni':
                val_si_data(test_order,sor,"BestPriceMinQtyNoLit",mxq,xref)
            elif si_sor == "BestPriceMinQtyUni":
                val_si_data(test_order,sor,"BestPriceMinQty",mxq,xref)
            else:
                val_si_data(test_order,sor,si_sor,mxq,xref)

        ## active wait for order complete
        order_complete = lambda order: order.orderStatus.primaryStatus == "Complete"
        assert active_wait(partial(order_complete,test_order))
        ##############################
        ## wait OM2 cancel event
        ## sor is "ForceCancel", direct is "DoneForDay"
        ## due to SI, can't tell easily without lookup reference.
        events = test_order.events()
        if "AttachExecution" in events:
            if test_order.orderStatus != "Complete":
                assert "ForceCancelFailure" in events
        else:
            assert "ForceCancel" in events or "DoneForDay" in events

        assert test_order.orderStatus.primaryStatus == "Complete", test_order.events()
        print test_order.orderStatus

