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

from tests._utils import verify_fix_message, verify_ahd_message, ahd_price, ahd_qty
from tests.JP_RAW.ahd_util import AHDOrder

log = logging.getLogger(__name__)

class TestAHD:
    """
    simple arrowhead order testing
    """

    def test_new_amend_cancel(self, ahd_service):
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


    def test_side_validation_reject(self, ahd_service):
        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = '0'
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
        execCond = '0'

        # For each side (1 -> sell, 3 -> buy)
        for side in ['0', '-1', '2', ' ']:
             for shortSellFlag in ['0', '5']:
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
                        'ReasonCode': '8047',
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': '0',
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                    ahd_service.expect(ordid, expected_msg, testname)

    def test_execCond_validation_reject(self, ahd_service):
        ##order
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = '0'
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
        shortSellFlag = '0'

        # For each side (1 -> sell, 3 -> buy)
        for side in ['0', '-1', '2', ' ']:
             for execCond in ['1', '3', '-5', '9', 'XYZ', ' ' ]:
                # Limit & market order:
                for price in [symbol_price]:
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
                        'ReasonCode': '8046',
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': '0',
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                    ahd_service.expect(ordid, expected_msg, testname)



    def test_qty_validation(self, ahd_service):
        
        symbol = '1301'
        symbol_price = 263
        mkt_order_price = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        shortSellFlag = '0'
        execCond = '0'
        for side in ['1', '3']:
             for price in [symbol_price, mkt_order_price]:
                 for qty in ['0', '1', '-1','1001']:
                    if qty == '0':
                        reasoncode = '8048' 
                    elif qty == '1':
                        reasoncode = '8013'
                    elif qty == '-1':
                        reasoncode = '8019'
                    elif qty == '1001':
                        reasoncode = '8019'

                    ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)

                    expected_msg = {
                        'DataClassCode': 'A111',
                        'Side': side,
                        'MsgType': '50',
                        'ReasonCode': reasoncode,
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': '0',
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                    ahd_service.expect(ordid, expected_msg, testname)

   def test_PropBrokerClass_validation(self, ahd_service):

        symbol = '1301'
        symbol_price = 263
        mkt_order_price = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        shortSellFlag = '0'
        execCond = '0'
        qty = '1000'
        for side in ['1', '3']:
             for price in [symbol_price, mkt_order_price]:
                 for  in propBrokerageClass['5', '9', '-1','XYZ',' ']:
                    ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)

                     expected_msg = {
                        'DataClassCode': 'A111',
                        'Side': side,
                        'MsgType': '50',
                        'ReasonCode': '8026',
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': '0',
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                    ahd_service.expect(ordid, expected_msg, testname)

  def test_CashMarginCode_validation(self, ahd_service):

        symbol = '1301'
        symbol_price = 263
        mkt_order_price = '0'
        propBrokerageClass = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        shortSellFlag = '0'
        execCond = '0'
        qty = '1000'
        for side in ['1', '3']:
             for price in [symbol_price, mkt_order_price]:
                 for  in cashMarginCode['2', '4', '-1','XYZ','3',' ']:
                    ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)

                     expected_msg = {
                        'DataClassCode': 'A111',
                        'Side': side,
                        'MsgType': '50',
                        'ReasonCode': '8025',
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': '0',
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
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
        

        # (5 -> with price restriction(cannot be market order), 7 -> without price restriction)A
        for side in ['3', '1']:
            for shortSellFlag in ['5', '7','0','6', '-1', 'XYZ', ' ']:
                for price in [mkt_order_price, symbol_price]:
                    for execCond in ['0', '2', '4']:
                        # Test step 1: create a new order
                        if side == '3' or shortSellFlag in ['0','6', '-1', 'XYZ', ' ']:
                           reasoncode = '8047'
                        elif side == '1' and shortSellFlag = '5' and mkt_order_price = mkt_order_price:
                           reasoncode = '8047'  # TODO  need to check the reason code 
                        else:
                           reasoncode = '0000'
                        ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                            execCond, shortSellFlag ,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)

                        expected_msg = {
                            'DataClassCode': 'A111',
                            'Side': '1',
                            'MsgType': '50',
                            'ReasonCode': reasoncode,
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
                        if reasoncode == '0000':
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

    def xtest_funari_create_amend_cancel(self, ahd_service):            
        # Test funari order
        for side in ['1', '3']:
            price = symbol_price #funari must be limit order
            execCond = '6' #funari order

            # Test step 1: create a new order
            ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                execCond, shortSellFlag,
                propBrokerageClass,
                cashMarginCode, stabArbCode,
                ordAttrClass, suppMemberClass)    

            pkt = ahd_service.get_ahd_message(order_id = ordid, expected_num_msg = 1)[0]
    
            # Verify return message
            assert pkt.getfieldval('DataClassCode') == 'A111'
            assert pkt.getfieldval('Side') == side 
            assert pkt.getfieldval('MsgType') == '50'
            assert pkt.getfieldval('ReasonCode') == '0000'
            assert pkt.getfieldval('ExecCond') == execCond
            assert pkt.getfieldval('CashMarginCode') == '0'
            assert pkt.getfieldval('ShortSellFlag') == '0'
            assert pkt.getfieldval('StabArbCode') == '0'
            assert pkt.getfieldval('Price') == ahd_price(price)
            assert pkt.getfieldval('Qty') == ahd_qty(qty)

            # Test step 2: send order modification 
            ahd_service.sendMod(ordid, symbol, qty=qty / 2)

            pkt = ahd_service.get_ahd_message(order_id = ordid, expected_num_msg = 1)[0]
            assert pkt.getfieldval('MsgType') == '50'
            assert pkt.getfieldval('DataClassCode') == 'F231'
            #assert pkt.getfieldval('ExecCond') == '0'
            assert pkt.getfieldval('ReasonCode') == '0000'
            assert pkt.getfieldval('Qty') == ahd_qty(qty / 2)

            # Test step 3: send order cancel
            ahd_service.sendCancel(ordid, symbol)
            pkt = ahd_service.get_ahd_message(order_id = ordid, expected_num_msg = 1)[0]
            assert pkt.getfieldval('MsgType') == '50'
            assert pkt.getfieldval('DataClassCode') == 'F221'
            assert pkt.getfieldval('ReasonCode') == '0000'


      def test_basic_fill(self, ahd_service):
        ## Step 1: Full fill
        ## Turn on fill mode of mxsim
        ahd_service.zcmd.turn_on_fill()

        ##order
        symbol = '1301'
        qty = 2000
        mkt_order_price = '0'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'

        # Order 1: buy 2000 @ mkt
        price = mkt_order_price
        for side in ('1', '3'):
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
 
        # Test Cases for partfill executions 
        ahd_service.zcmd.turn_on_partial_fill()
       
        qty = 8000 
        for side in ('1', '3'):
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

            # Test step 2: send order modification
            if side == '1':
               ordid = ahd_service.sendMod(ordid, symbol, qty=qty / 2)
            if side == '3':
               ordid = ahd_service.sendMod(ordid, symbol, price=price-1)


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


        ahd_service.zcmd.turn_off_partial_fill()
        ahd_service.zcmd.turn_off_fill()


    def test_compliance_restriction(self):

        file_name = os.getenv('REF_DATA_PATH')+'/restriction.csv'
        f = open(file_name, 'a')
        f.write('VIRTU,9437,XTKS,N,N,N,N,CS\n'+
                'VIRTU,6753,XTKS,N,Y,Y,Y,CS\n'+
                'VIRTU,1334,XTKS,N,Y,Y,Y,CS\n')

        ahd_service.acmd.reload_restrictions()
                                                     

        symbol_price = 263
        mkt_order_price = '0'
        propBrokerageClass = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        shortSellFlag = '0'
        execCond = '0'
        qty = '1000'
        cashMarginCode = '0'
        price = mkt_order_price 
            for symbol in ('9437','6753','1334')
               for (side, shortSellFlag) in [('1', '0'), ('1','5'), ('1','7'), ('3','0')]: 
                    if symbol in ('9437','6753','1334') and side == '3'
                        reasoncode = '8014'
                    elif symbol == '9437' and side == '1' and shortSellFlag = '0'
                        reasoncode = '8015'
                    elif symbol == '9437' and side == '1' and shortSellFlag = '5'
                        reasoncode = '8016'
                    elif symbol == '9437' and side == '1' and shortSellFlag = '7'
                        reasoncode = '8017'
                    elif symbol in ('6753','1334') and side == '1'
                        reasoncode = '0000'
                        

                    ordid = ahd_service.sendNewOrder(symbol, qty, side, price,
                        execCond, shortSellFlag,
                        propBrokerageClass,
                        cashMarginCode, stabArbCode,
                        ordAttrClass, suppMemberClass)

                     expected_msg = {
                        'DataClassCode': 'A111',
                        'Side': side,
                        'MsgType': '50',
                        'ReasonCode': reasoncode,
                        'ExecCond': execCond,
                        'CashMarginCode': cashMarginCode,
                        'ShortSellFlag': shortSellFlag,
                        'StabArbCode': '0',
                        'PropBrokerageClass': propBrokerageClass,
                        'Price': price,
                        'Qty': qty
                    }
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                    ahd_service.expect(ordid, expected_msg, testname)
        
       
      

    def test_compliance_lift_restriction(self):

        file_name = os.getenv('REF_DATA_PATH')+'/restriction.csv'
        f = open(file_name, 'a')
        f.write('VIRTU,9437,XTKS,N,N,N,N,CS\n'+
                'VIRTU,6753,XTKS,N,Y,Y,Y,CS\n'+
                'VIRTU,1334,XTKS,N,Y,Y,Y,CS\n')

        symbol_price = 263
        mkt_order_price = '0'
        propBrokerageClass = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
        shortSellFlag = '0'
        execCond = '0'
        qty = '1000'
        cashMarginCode = '0'
        price = mkt_order_price
            for symbol in ('9437','6753','1334')
               for (side, shortSellFlag) in [('1', '0'), ('1','5'), ('1','7'), ('3','0')]:
 
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
                    testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                    ahd_service.expect(ordid, expected_msg, testname)
  
