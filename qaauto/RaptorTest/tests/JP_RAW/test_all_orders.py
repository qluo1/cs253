from conf import settings
from scapy.all import *
from config.service.ahd import *

import pytest
import gevent
import zerorpc
import logging
import logging.config
import os
import copy

log = logging.getLogger(__name__)

class TestAHD:
    """
    simple arrowhead order testing
    """

    def test_new_amend_cancel(self, ahd_service):
        ahd_service.zcmd.turn_off_matching()

        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = ' 0           '
        shortSellFlag = '0'
        # TODO: what does this mean? ( 0 -> brokerage, 9 -> proprietary) can only be 0 or reject at 8026  
        propBrokerageClass = '0'
        # TODO: what does this mean? ( 0 -> cash, 2 -> margin, 4 -> liquidation) can only be 0 or reject at 8025 
        cashMarginCode = '0'
        # TODO: what does this mean? ( 0 -> non, 6 -> stabilization, 8 -> arbitrage trading) can only be 0 or reject at 8026
        stabArbCode = '0'
        # ( 1 -> automatic, 2 -> manual), has to be 1 or reject at 8041
        ordAttrClass = '1'
        # ( 0-> non, 1 -> support member order), has to be 0 or reject at 8043
        suppMemberClass = '0'

        # For each side (1 -> sell, 3 -> buy)
        for side in ['1', '3']:
            # For each execution condition (0 -> non, 2 -> open auction, 4 -> close auction, 6 -> funari, 8 -> IOC)
            # Funari must be sent as limited price order
            for execCond in ['0', '2', '4']:
                # Limit & market order:
                for price in [mkt_order_price, symbol_price]:
                    # Test step 1: create a new order
                    ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

                    expected_msg = {
                        'DataClassCode': 'A111',
                        'Side': side,
                        'MsgType': '50',
                        'ReasonCode': '0000',
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': '0',
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price)
                    ahd_service.expect(ordid, expected_msg, testname)

                    # Test step 2: send order modification 
                    ordid = ahd_service.sendMod(ordid, symbol, qty=qty / 2)

                    expected_msg = {
                        'MsgType': '50',
                        'DataClassCode': 'F231',
                        'ReasonCode': '0000',
                        'Qty': qty / 2
                    }
                    testname = 'ModOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price)
                    ahd_service.expect(ordid, expected_msg, testname)

                    # Test step 3: send order cancel
                    ordid = ahd_service.sendCancel(ordid, symbol)

                    expected_msg = {
                        'MsgType': '50',
                        'DataClassCode': 'F221',
                        'ReasonCode': '0000'
                    }
                    testname = 'ModOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price)
                    ahd_service.expect(ordid, expected_msg, testname)

    def test_IOC_create_amend_cancel(self, ahd_service):
        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = ' 0           '
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        execCond = '8' #IOC
        ordAttrClass = '1'
        suppMemberClass = '0'
        
        # Test IOC order
        for side in ['1', '3']:
            for price in [mkt_order_price, symbol_price]:
                ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                    execCond, shortSellFlag,
                    propBrokerageClass,
                    cashMarginCode, stabArbCode,
                    ordAttrClass, suppMemberClass)    

                # First return message -> acceptance notice
                expected_msg = {
                    'DataClassCode': 'A111',
                    'Side': side,
                    'MsgType': '50',
                    'ReasonCode': '0000',
                    'ExecCond': '8',
                    'CashMarginCode': '0',
                    'ShortSellFlag': '0',
                    'StabArbCode': '0',
                    'Price': price,
                    'Qty': qty
                }
                testname = 'IOC_CreateOrder_Side:' + side + '_Price:' + str(price)
                ahd_service.expect(ordid, expected_msg, testname)

                # Second return message -> invalidation notice
                # TODO: for invalidation message, the price is always mkt order price?
                expected_msg = {
                    'DataClassCode': 'K241',
                    'ReasonCode': '    ',
                    'MsgType': '50',
                    'ExecCond': '8',
                    'Qty': 0,
                    'Price': mkt_order_price,
                    'PartExecQty': 0
                }
                testname = 'IOC_Invalidation_Side:' + side + '_Price:' + str(price)
                ahd_service.expect(ordid, expected_msg, testname)

    def test_funari_create_amend_cancel(self, ahd_service):            
        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = ' 0           '
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        execCond = '6' #Funari
        ordAttrClass = '1'
        suppMemberClass = '0'

        price = symbol_price #funari must be limit order

        for side in ['1', '3']:
            # Test step 1: create a new order
            ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                execCond, shortSellFlag,
                propBrokerageClass,
                cashMarginCode, stabArbCode,
                ordAttrClass, suppMemberClass)    

            expected_msg = {
                'DataClassCode': 'A111',
                'Side': side,
                'MsgType': '50',
                'ReasonCode': '0000',
                'ExecCond': '6',
                'CashMarginCode': '0',
                'ShortSellFlag': '0',
                'StabArbCode': '0',
                'Price': price,
                'Qty': qty
            }
            testname = 'Funari_Create_Side:' + side
            ahd_service.expect(ordid, expected_msg, testname)

            # Test step 2: send order modification 
            ahd_service.sendMod(ordid, symbol, qty=qty / 2)

            expected_msg = {
                'DataClassCode': 'F231',
                'MsgType': '50',
                'ReasonCode': '0000',
                'Qty': qty / 2
            }
            testname = 'Funari_Mod_Side:' + side
            ahd_service.expect(ordid, expected_msg, testname)

            # Test step 3: send order cancel
            ahd_service.sendCancel(ordid, symbol)

            expected_msg = {
                'DataClassCode': 'F221',
                'MsgType': '50',
                'ReasonCode': '0000'
            }
            testname = 'Funari_Cancel_Side:' + side
            ahd_service.expect(ordid, expected_msg, testname)

    def test_shortsell_create_amend_cancel(self, ahd_service):
        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = ' 0           '
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        side = '1' #Must be sell

        # (5 -> with price restriction(cannot be market order), 7 -> without price restriction)
        for shortSellFlag in ['5', '7']:
            for price in [mkt_order_price, symbol_price]:
                for execCond in ['0', '2', '4']:
                    # Test step 1: create a new order
                    if shortSellFlag == '5' and price == mkt_order_price:
                        # TODO: add a test case for this
                        continue
                    ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

                    expected_msg = {
                        'DataClassCode': 'A111',
                        'Side': '1',
                        'MsgType': '50',
                        'ReasonCode': '0000',
                        'ExecCond': execCond,
                        'CashMarginCode': '0',
                        'ShortSellFlag': shortSellFlag,
                        'StabArbCode': '0',
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'ShortSell_Create_Flag:' + shortSellFlag + '_Price:' + str(price) + '_execCond:' + execCond
                    ahd_service.expect(ordid, expected_msg, testname)

                    # Test step 2: send order modification 
                    ahd_service.sendMod(ordid, symbol, qty=qty / 2)

                    expected_msg = {
                        'DataClassCode': 'F231',
                        'MsgType': '50',
                        'ReasonCode': '0000',
                        'Qty': qty / 2
                    }
                    testname = 'ShortSell_Mod_Flag:' + shortSellFlag + '_Price:' + str(price) + '_execCond:' + execCond
                    ahd_service.expect(ordid, expected_msg, testname)

                    # Test step 3: send order cancel
                    ahd_service.sendCancel(ordid, symbol)
                    expected_msg = {
                        'DataClassCode': 'F221',
                        'MsgType': '50',
                        'ReasonCode': '0000'
                    }
                    testname = 'ShortSell_Mod_Flag:' + shortSellFlag + '_Price:' + str(price) + '_execCond:' + execCond
                    ahd_service.expect(ordid, expected_msg, testname)


    def test_basic_matching(self, ahd_service):
        # cancel open orders
        ahd_service.zcmd.cancel_open_orders()
        # before running this testcase, should run zcmd on exchange simulator (cf --autoMatch=1)
        ahd_service.zcmd.turn_on_matching()

        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = ' 0           '
        side = '3'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        
        # Order 1: buy 2000 @ mkt
        price = mkt_order_price
        ordid_buy = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

        # ack 1
        ahd_service.ahd.get_ahd_message(order_id = ordid_buy)

        # Order 2: sell 1000 @ mkt
        side = '1'
        qty = 1000
        ordid_sell_1 = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

        # ack 2
        ahd_service.ahd.get_ahd_message(order_id = ordid_sell_1)

        # Verify partial execution 1
        expected_execution = {
            'MsgType': '50',
            'DataClassCode': 'J211',
            'ReasonCode': '0000',
            'Side': '3',
            'ExecCond': '0',
            'Qty': 1000,
            'ValidOrderQty': 1000
        }
        testname = 'Execution_Buy_PartialFill'
        ahd_service.expect(ordid_buy, expected_execution, testname)
        
        
        # Verify execution 2
        expected_execution['Side'] = '1'
        expected_execution['ValidOrderQty'] = 0
        testname = 'Execution_Sell_1_Fill'
        ahd_service.expect(ordid_sell_1, expected_execution, testname)

        # Order 3: sell 1000 @ mkt
        side = '1'
        qty = 1000
        ordid_sell_2 = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

        # ack 3 
        ahd_service.ahd.get_ahd_message(order_id = ordid_sell_2)

        # Verify full execution 1
        expected_execution['Side'] = '3'
        testname = 'Execution_Buy_Fill'
        ahd_service.expect(ordid_buy, expected_execution, testname)
        
        
        # Verify execution 3
        expected_execution['Side'] = '1'
        testname = 'Execution_Sell_2_Fill'
        ahd_service.expect(ordid_sell_2, expected_execution, testname)

        ## Finally turn off matching
        ahd_service.zcmd.turn_off_matching()

    def test_basic_fill(self, ahd_service):
        ## Step 1: Full fill
        ## Turn on fill mode of mxsim
        ahd_service.zcmd.turn_on_fill()
        
        ##order
        symbol = '1301'
        qty = 2000
        mkt_order_price = ' 0           '
        side = '3'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        
        # Order 1: buy 2000 @ mkt
        price = mkt_order_price
        ordid_buy = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

        # ack 1
        pkt = ahd_service.ahd.get_ahd_message(order_id = ordid_buy)[0]

        # Verify execution 1
        expected_execution = {
            'MsgType': '50',
            'DataClassCode': 'J211',
            'ReasonCode': '0000',
            'Side': '3',
            'ExecCond': '0',
            'Qty': 2000,
            'ValidOrderQty': 0
        }
        testname = 'Execution_Buy_Fill'
        ahd_service.expect(ordid_buy, expected_execution, testname)

        ## Step 2: Partial fill
        ahd_service.zcmd.turn_on_partial_fill()

        # Order 2: buy 2000 @ mkt
        price = mkt_order_price
        ordid_buy = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)    

        # ack 2 
        ahd_service.ahd.get_ahd_message(order_id = ordid_buy)

        # Verify execution 2
        expected_execution = {
            'MsgType': '50',
            'DataClassCode': 'J211',
            'ReasonCode': '0000',
            'Side': '3',
            'ExecCond': '0',
            #'Qty': 2000,
            #'ValidOrderQty': 0
        }
        testname = 'Execution_Buy_Partial_Fill'
        ahd_service.expect(ordid_buy, expected_execution, testname)

        ahd_service.zcmd.turn_off_partial_fill()
        ahd_service.zcmd.turn_off_fill()


    def xtest_basic_restriction(self):
        ##order
        symbol = '1305'
        qty = 2000
        mkt_order_price = ' 0           '
        side = '3'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        price = mkt_order_price

        # buy
        m = ahd_service.sendNewOrder(symbol, qty, side, price,
            execCond, shortSellFlag,
            propBrokerageClass,
            cashMarginCode, stabArbCode,
            ordAttrClass, suppMemberClass)    

        ret = queue.get(timeout = 10)
        pkt = ESPCommon(ret)
        assert pkt.getfieldval('MsgType') == '50'
        assert pkt.getfieldval('DataClassCode') == 'C119' #New order acceptance error
        assert pkt.getfieldval('ReasonCode') == '8014' #Client buy restricted

        # sell
        side = '1'
        m = ahd_service.sendNewOrder(symbol, qty, side, price,
            execCond, shortSellFlag,
            propBrokerageClass,
            cashMarginCode, stabArbCode,
            ordAttrClass, suppMemberClass)    

        ret = queue.get(timeout = 10)
        pkt = ESPCommon(ret)
        assert pkt.getfieldval('MsgType') == '50'
        assert pkt.getfieldval('DataClassCode') == 'C119' #New order acceptance error
        assert pkt.getfieldval('ReasonCode') == '8015' #Client sell restricted

        # short sell exempt
        side = '1' 
        shortSellFlag = '7'
        m = ahd_service.sendNewOrder(symbol, qty, side, price,
            execCond, shortSellFlag,
            propBrokerageClass,
            cashMarginCode, stabArbCode,
            ordAttrClass, suppMemberClass)    

        ret = queue.get(timeout = 10)
        pkt = ESPCommon(ret)
        assert pkt.getfieldval('MsgType') == '50'
        assert pkt.getfieldval('DataClassCode') == 'C119' #New order acceptance error
        assert pkt.getfieldval('ReasonCode') == '8017' #Client shortsell exempt restricted

        # short sell
        side = '1'
        shortSellFlag = '5'
        price = 200
        m = ahd_service.sendNewOrder(symbol, qty, side, price,
            execCond, shortSellFlag,
            propBrokerageClass,
            cashMarginCode, stabArbCode,
            ordAttrClass, suppMemberClass)    

        ret = queue.get(timeout = 10)
        pkt = ESPCommon(ret)
        assert pkt.getfieldval('MsgType') == '50'
        assert pkt.getfieldval('DataClassCode') == 'C119' #New order acceptance error
        assert pkt.getfieldval('ReasonCode') == '8016' #Client shortsell restricted


