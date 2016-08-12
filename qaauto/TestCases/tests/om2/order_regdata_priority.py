import os
import time
import random
import copy
from pprint import pprint
from itertools import chain
import math
import re
import pytest
from datetime import datetime,timedelta

from utils import (
              tickSize,
              halfTick,
              get_passive_price,
              opposite_side,
              getPegOrderType,
              PegType,
              AckFailed,
              )
from clientOrderId import clientOrderId

from om2Order import Order

from conf import settings
import zerorpc
server = zerorpc.Client(settings.ORDER_API_URL)

from rdsGenTestData.genRdsData import rds_data,data_to_command,test_data

from val_regdata import val_reg_data_2, val_si_data_2

###############################################
## test case for regdata and si override
## update
## 286    // 2) or apply reg data found by: gsoeId or xref or starId or primary account (search in this order)
###############################################
testcases = [
        ## baseline
        {'data': {'oeid'    : '1001'},   'expect': 'oeid'},
        {'data': {'starid'  : '2001T'},   'expect': 'starid'},
        ## startId lookup oeid
        {'data': {'starid'  : '3001T'},   'expect': 'oeid'},

        {'data': {'xref'    : 'SAM'},    'expect': 'xref'},
        {'data': {'tam'     : 'TAMSAM'}, 'expect': 'tam'},

        ## oeid override starid
        {'data': {'oeid'    : '1001',
                  'starid'  : '2001T'},  'expect': 'oeid'},
        ## 
        {'data': {'oeid'    : 'junk',
                  'starid'  : '2001T'},  'expect': 'starid'},

        ## xref override starId
        {'data': {'starid'  : '2001T',
                  'xref'    : 'SAM'},   'expect': 'xref'},
        ##
        {'data': {'starid'  : 'junk',
                  'xref'    : 'SAM'},   'expect': 'xref'},

        ## oeid override xref
        {'data': {'oeid'    : '1001',
                  'xref'    : 'SAM'},   'expect': 'oeid'},

        {'data': {'oeid'    : 'junk',
                  'xref'    : 'SAM'},   'expect': 'xref'},

        ## xref override tam
        {'data': {'tam'     : 'TAMSAM',
                  'xref'    : 'SAM'},   'expect': 'xref'},

        {'data': {'tam'     : 'TAMSAM',
                  'xref'    : 'junk'},   'expect': 'tam'},
        ##default
        ##for oeid explicity set capacity to workaround in inconsistent behaviour
        {'data': {'oeid'    : 'junk', 'extra': {'orderCapacity': 'Agency',}},  'expect': 'default_oeid_junk'},
        {'data': {'starid'  : 'junk'},  'expect': 'default'},
        {'data': {'tam'     : 'JUNK'},  'expect': 'default'},
        {'data': {'xref'    : 'JUNK'},  'expect': 'default'},

        ## syntetic, will be override as default_p
        {'data': {'oeid'    : '1011',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},
        {'data': {'starid'  : '2011',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},
        {'data': {'tam'     : 'TAMAGENT',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},
        {'data': {'xref'    : 'SAMA',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},

        {'data': {'oeid'    : 'junk',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},
        {'data': {'starid'    : 'junk',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},
        {'data': {'xref'    : 'junk',
                  'synthetic': random.randint(1,4)},  'expect': 'default_p'},

       ## si based on oeid JIRA-672
        {'data': {'oeid'    : '1002'},    'expect': 'si_oeid_asx'},
        {'data': {'oeid'    : '1003'},    'expect': 'si_oeid_asxonly'},
        {'data': {'oeid'    : '1004'},    'expect': 'si_oeid_bp'},
        {'data': {'oeid'    : '1005'},    'expect': 'si_oeid_bpmq'},
        {'data': {'oeid'    : '1006'},    'expect': 'si_oeid_bpmquni'},
        {'data': {'oeid'    : '1007'},    'expect': 'si_oeid_bpmqnolit'},
        {'data': {'oeid'    : '1008'},    'expect': 'si_oeid_bpmqnolituni'},
        {'data': {'oeid'    : '1009'},    'expect': 'si_oeid_bpmv'},

        ## si based on xref
        {'data': {'xref'    : 'SAM2'},    'expect': 'si_xref_asx'},
        {'data': {'xref'    : 'SAM3'},    'expect': 'si_xref_asxonly'},
        {'data': {'xref'    : 'SAM4'},    'expect': 'si_xref_bp'},
        {'data': {'xref'    : 'SAM5'},    'expect': 'si_xref_bpmq'},
        {'data': {'xref'    : 'SAM6'},    'expect': 'si_xref_bpmquni'},
        {'data': {'xref'    : 'SAM7'},    'expect': 'si_xref_bpmqnolit'},
        {'data': {'xref'    : 'SAM8'},    'expect': 'si_xref_bpmqnolituni'},
        {'data': {'xref'    : 'SAM9'},    'expect': 'si_xref_bpmv'},

## "Changes 1 : Allow StandingInstruction to be applied to OkToCross orders in Australia.

#         """ Summary of the changes:
#            Previously, SOR  standingInstruction will be applied only for OkToSmartRoute SOR orders. 
#            The new changes will allow standingInstructions to be applied to SOR orders with purely OkToCross orders as well.
#
#            You may test the following scenario:
#                an order sent from ATP or Plutus, smartRouteConsent==.., crossConsent==.OkToCross., tradingAlgo=.BestPriceMinQty., 
#                StandingInstruction for the client is .ASXOnly.. The result will be the SOR strategy being converted to ASXOnly.
#        """
       ## si based on oeid JIRA-672
        {'data': {'oeid'    : '1002', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_oeid_asx'},
        {'data': {'oeid'    : '1003', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_oeid_asxonly'},
        {'data': {'oeid'    : '1004', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bp'},
        {'data': {'oeid'    : '1005', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},   'expect': 'si_oeid_bpmq'},
        {'data': {'oeid'    : '1006', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bpmquni'},
        {'data': {'oeid'    : '1007', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},   'expect': 'si_oeid_bpmqnolit'},
        {'data': {'oeid'    : '1008', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bpmqnolituni'},
        {'data': {'oeid'    : '1009', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bpmv'},
       ## si based on oeid JIRA-672
        {'data': {'oeid'    : '1002', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_oeid_asx'},
        {'data': {'oeid'    : '1003', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_oeid_asxonly'},
        {'data': {'oeid'    : '1004', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bp'},
        {'data': {'oeid'    : '1005', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},   'expect': 'si_oeid_bpmq'},
        {'data': {'oeid'    : '1006', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bpmquni'},
        {'data': {'oeid'    : '1007', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},   'expect': 'si_oeid_bpmqnolit'},
        {'data': {'oeid'    : '1008', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bpmqnolituni'},
        {'data': {'oeid'    : '1009', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_oeid_bpmv'},

        ## si based on xref
        {'data': {'xref'    : 'SAM2', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_asx'},
        {'data': {'xref'    : 'SAM3', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_asxonly'},
        {'data': {'xref'    : 'SAM4', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_bp'},
        {'data': {'xref'    : 'SAM5', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmq'},
        {'data': {'xref'    : 'SAM6', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmquni'},
        {'data': {'xref'    : 'SAM7', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmqnolit'},
        {'data': {'xref'    : 'SAM8', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmqnolituni'},
        {'data': {'xref'    : 'SAM9', 'extra': {'smartRouteConsent':'INVALID','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmv'},
        ## si based on xref
        {'data': {'xref'    : 'SAM2', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_asx'},
        {'data': {'xref'    : 'SAM3', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_asxonly'},
        {'data': {'xref'    : 'SAM4', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_bp'},
        {'data': {'xref'    : 'SAM5', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmq'},
        {'data': {'xref'    : 'SAM6', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmquni'},
        {'data': {'xref'    : 'SAM7', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmqnolit'},
        {'data': {'xref'    : 'SAM8', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmqnolituni'},
        {'data': {'xref'    : 'SAM9', 'extra': {'smartRouteConsent':'DoNotSmartRoute','crossConsent':'OkToCross'}},  'expect': 'si_xref_bpmv'},

]

class Test_Order_RegData_Dynamic:

    """ test regdata dynamically

    1) setup_class insert test data into OM2/RDS
    2) testcase specify combination of oeid/starid/xref/tam with expected result
       note: testcase must based on previous test data

    """
    scenarios = []

    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)

    for sor in test_order_types:
        for testcase in testcases:
            ## skip sigmax due to :No account found for xref [SAM]. Using bucket account
            if sor == 'sigmax': continue
            data = dict(sor=sor,testcase=testcase)
            scenarios.append(data)

    def setup_class(cls):
        """ helper setup refdata for each test run. """
        ## QAE/PPE only, PME need manual load snapshot
        print "setup rds data. "
        for k, data in rds_data.iteritems():
            assert isinstance(data,list)
            for test in data:
                cmd = data_to_command("Insert",test,settings.RDS_REQ)
                #print cmd
                ack = Order.sendRdsHermes(cmd)
                assert "Success" == ack['status']

    #@pytest.mark.skipif("True")
    def test_new_amend_cancel(self,sor,testcase,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True,top200=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY",0))
        ## market depth
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        side = random.choice(settings.TEST_SIDES)
        price = get_passive_price(side,quote)
        ## for amend passive
        delta = -1 if side == "Buy" else 1
        ## prepare test
        assert isinstance(testcase,dict)
        testdata = testcase['data']
        testexpect = testcase['expect']
        assert testexpect in test_data

        order_t = {
                'symbol': symbol,
                'side': side,
                'price': price,
                'qty': random.randint(300,600),
                'extra': {}
        }
        if 'oeid' in testdata:
            order_t['extra']['customerOeId'] = testdata['oeid']
        if 'starid' in testdata:
            order_t['extra']['clientStarId'] = testdata['starid']
        if 'xref' in testdata:
            order_t['xref'] = testdata['xref']
        if 'tam' in testdata:
            order_t['account'] = testdata['tam']
        if 'synthetic' in testdata:
            order_t['extra']['syntheticType'] = testdata['synthetic']
        ## set additional attrs for test order
        if 'extra' in testdata:
            order_t['extra'].update(testdata['extra'])
        ## unfortunately direct peg order will failed with this smartRouteConsent, crossConsent
        if sor not in settings.SOR:
            if 'smartRouteConsent' in order_t['extra']: order_t['extra'].pop("smartRouteConsent")
            if 'crossConsent' in order_t['extra']: order_t['extra'].pop("crossConsent")

        ## for bpmv, random update order value > 120k for buy
        if testexpect.endswith("bpmv") and random.random() > 0.5:
            minQty = 120005.0 / order_t['price']
            order_t['qty'] = round(minQty) + 10

        tags = settings.ORDER_TYPES[sor]
        order_t.update(tags)
        pprint(order_t)

        test_order = Order(**order_t)
        ###########################################
        try:
            clOrdId,_ = test_order.new()
            test_order.expect_ok()
            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
        except ValueError,e:
            # asxcb order, certain symbol need minimum value > $200k from ASX
            p = re.compile("Order value is less than the minimum order value.")
            if not p.search(test_order.orderStatus.rejectReasonText):
                raise(e)
            ### can still validate regdata for new
            val_reg_data_2(test_order.orderInst,test_data[testexpect],**order_t)
            ### validate si for new
            if sor in settings.SOR and testexpect.startswith("si"):
                val_si_data_2(test_order,test_data[testexpect],mxq,**order_t)

            ## stop here and pass the test
            return
        except AckFailed,e:
            #if si_sor in IN_COMPATIABLE_SI_SOR and sor in IN_COMPATIABLE_SI_SOR[si_sor]:
            rejectReasons =  e.message['rejectReasons'][0]
            if rejectReasons['rejectReasonText'] == 'Validation failed: Incompatible with StandingInstruction' and \
                rejectReasons['rejectingSystem'] == "Rules" and \
                rejectReasons['rejectReasonType'] == "InvalidOrderType":
                return
            else:
                raise


        ######################################
        ### validate regdata for new
        val_reg_data_2(test_order.orderInst,test_data[testexpect],**order_t)

        ######################################
        ### validate si for new
        if sor in settings.SOR and testexpect.startswith("si"):
            val_si_data_2(test_order,test_data[testexpect],mxq,**order_t)

        ##########################################
        clOrdId,_ = test_order.amend(price = price + tickSize(price,delta),
                                     qty = order_t['qty'] + 200)

        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend, %s, %s" % (clOrdId,acks)
        ######################################
        ### validate order regdata for amend
        val_reg_data_2(test_order.orderInst,test_data[testexpect],**order_t)

        ######################################
        ### validate si for amend
        if sor in settings.SOR and testexpect.startswith("si"):
            val_si_data_2(test_order,test_data[testexpect],mxq,**order_t)

        clOrdId,_ = test_order.cancel()
        acks =  test_order.events(clOrdId)
        print "cancel: %s , %s" % (clOrdId,acks)


class Test_FAKFOK_RegData_Dynamic:

    """ test fakfok order regdata dynamically

    1) setup_class insert test data into OM2/RDS
    2) testcase specify combination of oeid/starid/xref/tam with expected result
       note: testcase must based on previous test data

    """
    scenarios = []

    test_order_types = {}
    test_order_types.update(settings.ORDER_TYPES)

    allOrNones = (True,False)

    for sor in test_order_types:
        ## skip uni sor
        if sor in settings.SOR_UNI: continue
        #if sor not in ("asxcb","asxc"): continue
        for allOrNone in allOrNones:
            for testcase in testcases:
                expect = testcase['expect']
                ## skip sor override for uni sor
                if expect.endswith("uni"): continue
                data = dict(sor=sor,allOrNone=allOrNone,testcase=testcase)
                scenarios.append(data)

    def setup_class(cls):
        """ helper setup refdata for each test run. """
        print "setup rds data. "
        #pytest.set_trace()
        for k, data in rds_data.iteritems():
            assert isinstance(data,list)
            for test in data:
                cmd = data_to_command("Insert",test,settings.RDS_REQ)
                #print cmd
                ack = Order.sendRdsHermes(cmd)
                assert "Success" == ack['status']


    def test_fakfok(self,sor,allOrNone,testcase,symbol_depth):
        """ """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY",0))
        ## market depth
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        side = random.choice(settings.TEST_SIDES)

        price = get_passive_price(side,quote)

        ## prepare test
        assert isinstance(testcase,dict)
        testdata = testcase['data']
        testexpect = testcase['expect']
        assert testexpect in test_data

        order_t = {
                'symbol': symbol,
                'side'  : side,
                'price' : price,
                'qty'   : random.randint(100,200),
                'allOrNone' : allOrNone,
                'tif'  : "ImmediateOrCancel",
                'extra' : {},
        }

        if 'oeid' in testdata:
            order_t['extra']['customerOeId'] = testdata['oeid']
        if 'starid' in testdata:
            order_t['extra']['clientStarId'] = testdata['starid']
        if 'xref' in testdata:
            order_t['xref'] = testdata['xref']
        if 'tam' in testdata:
            order_t['account'] = testdata['tam']
        if 'synthetic' in testdata:
            order_t['extra']['syntheticType'] = testdata['synthetic']
        ## set additional attrs for test order
        if 'extra' in testdata:
            order_t['extra'].update(testdata['extra'])

        ## unfortunately direct peg order will failed with this smartRouteConsent, crossConsent
        if sor not in settings.SOR:
            if 'smartRouteConsent' in order_t['extra']: order_t['extra'].pop("smartRouteConsent")
            if 'crossConsent' in order_t['extra']: order_t['extra'].pop("crossConsent")

        ## for bpmv, random update order value > 120k for buy
        if testexpect.endswith("bpmv") and random.random() > 0.5:
            minQty = 120005.0 / order_t['price']
            order_t['qty'] = round(minQty) + 10

        tags = settings.ORDER_TYPES[sor]
        order_t.update(tags)
        ########################################
        ## if asxcb and allOrNone == true, reset maq == orderQty
        ## otherwise, it wil exchange reject: Message Text: Minimum Acceptable quantity too large, Number: -420721
        if sor == 'asxcb' and allOrNone == True:
            order_t['maq'] = order_t['qty']
        if sor in ("asxsb","asxs","asxsweep") and allOrNone == True:
            pytest.skip("exchange not supported FOK for %s" % sor)

        pprint(order_t)
        ###########################################
        try:
            test_order = Order(**order_t)
            clOrdId,_ = test_order.new()
            test_order.expect("OrderAccept")
            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
        except ValueError,e:

            #rejectReasonType': 'MaximumNotionalValueExceeded'
            if test_order.orderStatus.rejectReasonType == 'MaximumNotionalValueExceeded':
                return pytest.skip("%s" % test_order.orderStatus)

            # asxcb order, certain symbol need minimum value > $200k from ASX
            p = re.compile("Order value is less than the minimum order value.")
            if not p.search(test_order.orderStatus.rejectReasonText):
                raise(e)
            ## not stop here, should be able to validate regdata and SI on orderInst
            #pytest.skip("symbol rejected by exchange: %s" % test_order.orderStatus.rejectReasonText)
        except AckFailed,e:
            #if si_sor in IN_COMPATIABLE_SI_SOR and sor in IN_COMPATIABLE_SI_SOR[si_sor]:
            rejectReasons =  e.message['rejectReasons'][0]
            if rejectReasons['rejectReasonText'] == 'Validation failed: Incompatible with StandingInstruction' and \
                rejectReasons['rejectingSystem'] == "Rules" and \
                rejectReasons['rejectReasonType'] == "InvalidOrderType":
                return
            else:
                raise

        ######################################
        ### validate order regdata for amend
        val_reg_data_2(test_order.orderInst,test_data[testexpect],**order_t)
        ######################################
        ### ivalidate SI for sor order,
        if sor in settings.SOR and testexpect.startswith("si"):
            val_si_data_2(test_order,test_data[testexpect],mxq,**order_t)


class Test_TradeReport:

    """ asx trade report. """

    scenarios = []
    for cond in (
                'NX',
                'BP',
                ):
        for testcase in testcases:
            data = dict(sor='asx',cond=cond,testcase=testcase)
            scenarios.append(data)

    def setup_class(cls):
        """ helper setup refdata for each test run. """

        print "setup rds data. "
        for k, data in rds_data.iteritems():
            assert isinstance(data,list)
            for test in data:
                cmd = data_to_command("Insert",test,settings.RDS_REQ)
                #print cmd
                ack = Order.sendRdsHermes(cmd)
                assert "Success" == ack['status']


    def test_new_cross_trade(self,sor,cond,testcase,symbol_depth):
        """ test trade report . """
        symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY",0))
        ## prepare test
        assert isinstance(testcase,dict)
        testdata = testcase['data']
        testexpect = testcase['expect']
        assert testexpect in test_data

        tags = settings.TRADE_REPORTS[sor]


        pprint(quote)
        print ("-------- test case -------")
        pprint(testcase)
        order_t = {
                'symbol': symbol,
                'price': last,
                'qty': random.randint(300,600),
                'extra': {},
        }
        if 'oeid' in testdata:
            order_t['extra']['customerOeId'] = testdata['oeid']
        if 'starid' in testdata:
            order_t['extra']['clientStarId'] = testdata['starid']
        if 'xref' in testdata:
            order_t['xref'] = testdata['xref']
        if 'tam' in testdata:
            order_t['account'] = testdata['tam']
        if 'synthetic' in testdata:
            order_t['extra']['syntheticType'] = testdata['synthetic']
        ## set additional attrs for test order
        if 'extra' in testdata:
            order_t['extra'].update(testdata['extra'])

        if sor not in settings.SOR:
            if 'smartRouteConsent' in order_t['extra']: order_t['extra'].pop("smartRouteConsent")
            if 'crossConsent' in order_t['extra']: order_t['extra'].pop("crossConsent")

        ## sigma order leg
        order_t.update(tags)

        buy = order_t.copy()
        sell = order_t.copy()

        ## create clOrdId based on xref if present or "side"
        buy['clOrdId'] =  clientOrderId(order_t.get("xref") or "Buy")
        buy['side'] = 'Buy'

        sell['clOrdId'] = clientOrderId(order_t.get("xref") or "Sell")
        sell['side'] = 'Sell'
        ## set crossMatchId
        buy['crossMatchId'] = sell['crossMatchId'] = "%s:%s" % (buy['clOrdId'],sell['clOrdId'])
        ## condition code for trade report
        buy['conditionCode'] = sell['conditionCode'] = cond

        buy_order = Order(**buy)
        sell_order = Order(**sell)

        buy_order.new(validate=False)
        sell_order.new(validate=False)

        # accept after both legs
        buy_order.expect("OrderAccept")
        sell_order.expect("OrderAccept")
        #import pdb;pdb.set_trace()

        print "buy: ", buy_order
        print "sell: ", sell_order
        ## trade reported
        buy_order.expect("AttachExecution")
        sell_order.expect("AttachExecution")

        print 'buy leg:', buy_order.fills
        print 'sell leg:', sell_order.fills

        assert buy_order.orderStatus.primaryStatus == "Complete"
        assert sell_order.orderStatus.primaryStatus == "Complete"
        ######################################
        ### validate order regdata for buyOrder
        val_reg_data_2(buy_order.orderInst,test_data[testexpect],**order_t)
        ######################################
        ### validate order regdata for sellOrder
        val_reg_data_2(sell_order.orderInst,test_data[testexpect],**order_t)


class Test_GSET_BucketOrder:
    """
    Changes 2 : Assigning default xrefs for Australian GSET bucketed orders.

    """
    gset_test_cases = [
            ## default no changes i.e. system=PlutusChild_DEV
            {'data': {'oeid': '1001', 'extra': {'businessUnit':'DMA' }},
                'expect': {'key': 'oeid'} },
            {'data': {'oeid': '1001A', 'extra': {'businessUnit':'DMA' }},
                'expect': {'key': 'oeid_a'} },

            ## override known firm order
            {'data': {'oeid': '1001', 'capacity': 'Principal', 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'oeid','xref':'GPR'} },
            ## override know synthetic order 
            {'data': {'oeid': '1001', 'capacity': 'Principal', 'synthetic': 1, 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'bucket_xref_gpr'} },

            ## unknown oeid, principal order, override as GPR
            {'data': {'oeid': 'junk', 'capacity': 'Principal', 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'bucket_xref_gpr'} },

            ## unknown oeid, client order, override xref
            {'data': {'oeid': 'junk', 'capacity': 'Agency', 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'default_oeid_junk', 'xref': 'GSV'} },

            ## unknoen oeid, agency order, override as GSV
            {'data': {'oeid': 'junk', 'capacity': 'Agency', 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'bucket_xref_gsv', 'orig':'junk'} },

            ## incorrect capacity should be override xref only as GSV
            {'data': {'oeid': '1001A', 'capacity': 'Principal', 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'oeid_a', 'xref': 'GSV'} },

            ## synthetic client, should override as GRP
            {'data': {'oeid': '1001A', 'capacity': 'Agency', 'synthetic': 1, 'extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'bucket_xref_gpr'} },

            ## no change for other businessUnit
            {'data': {'oeid': '1001', 'capacity': 'Principal', 'extra': {'businessUnit':'PT' }, 'system':'IOSAdapter'},
                'expect': {'key':'oeid'} },
            {'data': {'oeid': '1001A', 'capacity': 'Principal', 'extra': {'businessUnit':'PT' }, 'system':'IOSAdapter'},
                'expect': {'key':'oeid_a'} },

            ## si override, override xref - GSV
            {'data': {'oeid' : '1004','extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key': 'si_oeid_bp','xref':'GSV'} },

            ## startId, default
            {'data': {'starid' : '2001T','capacity': 'Agency','extra': {'businessUnit':'DMA' }, 'system':'IOSAdapter'},
                'expect': {'key':'bucket_xref_gsv' }},
    ]

    order_types = settings.ORDER_TYPES.copy()
    #order_types = ['asx','sor1','sor4']
    scenarios = []
    for sor in order_types:
        for testcase in gset_test_cases:
            ## skip sigmax due to :No account found for xref [SAM]. Using bucket account
            if sor == 'sigmax': continue
            data = dict(sor=sor,testcase=testcase)
            scenarios.append(data)

    def setup_class(cls):
        """ helper setup refdata for each test run. """
        ## QAE/PPE only, PME need manual load snapshot
        print "setup rds data. "
        for k, data in rds_data.iteritems():
            assert isinstance(data,list)
            for test in data:
                cmd = data_to_command("Insert",test,settings.RDS_REQ)
                #print cmd
                ack = Order.sendRdsHermes(cmd)
                assert "Success" == ack['status']

    def test_new_amend_cancel(self,sor,testcase,symbol_depth):
        """ order basic - new/amend/cancel for all order types . """
        if sor in settings.ASXCP :
            symbol, quote, cha_quote, attrs = symbol_depth.get_tradable_symbol(build=True)
        else:
            symbol, quote, cha_quote, attrs = symbol_depth.get_test_symbol(with_last=True,with_depth=True)

        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']
        mxq = int(attrs.get("MINEXECUTABLEQTY",0))
        ## market depth
        bid,ask,last = quote['bid']['bid'], quote['ask']['ask'], quote['last']

        side = random.choice(settings.TEST_SIDES)
        price = get_passive_price(side,quote)
        ## for amend passive
        delta = -1 if side == "Buy" else 1

        ## prepare test validation
        assert isinstance(testcase,dict)
        testdata = testcase['data']
        testexpect = testcase['expect']
        assert 'key' in testexpect
        testexpect_key = testexpect['key']
        assert testexpect_key in test_data

        test_regdata = copy.copy(test_data[testexpect_key])
        ## set xref override
        if 'xref' in testexpect:
            test_regdata['xref'] = testexpect['xref']
        if 'orig' in testexpect:
            test_regdata['ASICORIGINOFORDER'] = testexpect['orig']

        order_t = {
                'symbol': symbol,
                'side': side,
                'price': price,
                'qty': random.randint(300,600),
                'extra': {},
        }
        if 'oeid' in testdata:
            order_t['extra']['customerOeId'] = testdata['oeid']
        ## startId
        if 'starid' in testdata:
            order_t['extra']['clientStarId'] = testdata['starid']

        if 'synthetic' in testdata:
            order_t['extra']['syntheticType'] = testdata['synthetic']
        ## set additional attrs for test order
        if 'extra' in testdata:
            order_t['extra'].update(testdata['extra'])
        if 'capacity' in testdata:
            order_t['capacity'] = testdata['capacity']
        if 'system' in testdata:
            order_t['system'] = testdata['system']

        ## unfortunately direct peg order will failed with this smartRouteConsent, crossConsent
        if sor not in settings.SOR:
            if 'smartRouteConsent' in order_t['extra']: order_t['extra'].pop("smartRouteConsent")
            if 'crossConsent' in order_t['extra']: order_t['extra'].pop("crossConsent")

        ## for bpmv, random update order value > 120k for buy
        if testexpect_key.endswith("bpmv") and random.random() > 0.5:
            minQty = 120005.0 / order_t['price']
            order_t['qty'] = round(minQty) + 10

        tags = settings.ORDER_TYPES[sor]
        order_t.update(tags)
        pprint(order_t)

        test_order = Order(**order_t)
        ###########################################
        try:
            clOrdId,_ = test_order.new()
            test_order.expect_ok()
            acks =  test_order.events(clOrdId)
            print "orderId,%s, %s" % (test_order.orderId,acks)
        except ValueError,e:
            # asxcb order, certain symbol need minimum value > $200k from ASX
            p = re.compile("Order value is less than the minimum order value.")
            if not p.search(test_order.orderStatus.rejectReasonText):
                raise(e)
            ### can still validate regdata for new
            val_reg_data_2(test_order.orderInst,test_regdata,**order_t)
            ### validate si for new
            if sor in settings.SOR and testexpect_key.startswith("si"):
                val_si_data_2(test_order,test_regdata,mxq,**order_t)

            ## stop here and pass the test
            return

        ######################################
        ### validate regdata for new
        val_reg_data_2(test_order.orderInst,test_regdata,**order_t)

        ######################################
        ### validate si for new
        if sor in settings.SOR and testexpect_key.startswith("si"):
            val_si_data_2(test_order,test_regdata,mxq,**order_t)

        ##########################################
        clOrdId,_ = test_order.amend(price = price + tickSize(price,delta),
                                     qty = order_t['qty'] + 200)

        test_order.expect_ok()
        acks =  test_order.events(clOrdId)
        print "amend, %s, %s" % (clOrdId,acks)
        ######################################
        ### validate order regdata for amend
        val_reg_data_2(test_order.orderInst,test_regdata,**order_t)

        ######################################
        ### validate si for amend
        if sor in settings.SOR and testexpect_key.startswith("si"):
            val_si_data_2(test_order,test_regdata,mxq,**order_t)

        clOrdId,_ = test_order.cancel()
        acks =  test_order.events(clOrdId)
        print "cancel: %s , %s" % (clOrdId,acks)


