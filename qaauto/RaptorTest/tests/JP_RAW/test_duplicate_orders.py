from conf import settings
from scapy.all import *
from config.service.ahd import *

import pytest
import logging

log = logging.getLogger(__name__)

CLIENT_ID = 'VIRTU'

## TODO: For amending price, we need to know the ticksize and current mkt price of product
class TestDuplicateOrders :
               
    def test_duplicateOrders_allMatched(self, ahd_service):
        ## enable the client if it is already disabled
        status = ahd_service.zcmd.get_client_status(CLIENT_ID, 'status')
        if status == 'Disabled':
            ahd_service.acmd.enable_client(CLIENT_ID)
      
        ## Setting the client duplicate orders limit to 10
        max_dup_limit = 10
        ahd_service.zcmd.set_client_limits(CLIENT_ID, {'maxDupOrders':max_dup_limit})
        #file_name = os.getenv('REF_DATA_PATH')+'/clientLimits.csv'
        #f = open(file_name, 'a')
        #f.write(VIRTU,XTKS,CS,120000000000,4000000000000,-24000000000000,2400000000000,N,N,N,N,Y,1000000,10)
        #ahd_service.zcmd.set_ClientLimits()
               
        symbol = '1301'
        qty = 2000
        symbol_price = 263
        mkt_order_price = ' 0           '
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'

        for side in ['1','3']:
            for execCond in ['0', '2', '4', '6', '8']:
                for shortSellFlag in ['0','5','7']:
                    for price in [mkt_order_price, symbol_price] :
                        ## For each combination of parameters, we send order max_dup_limit + 1 times
                        ordids = []
                        for i in range(max_dup_limit + 1):
                            # omit short sell, exempt / buy combo
                            if not shortSellFlag == '0' and side == '3':
                                continue
                            # omit funari / market combo
                            if execCond == '6' and  price == mkt_order_price:
                                continue
                            # omit short sell / market combo
                            if shortSellFlag == '5' and price == mkt_order_price:
                                continue
                            #omit IOC order
                            if execCond == '8' :
                                continue
                             
                            # Order will be rejected on the max_dup_limit + 1 time attempt
                            if i == max_dup_limit:
                                reasoncode = '8020'             
                            else:
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
                                 'ShortSellFlag': '0',
                                 'StabArbCode': '0',
                                 'PropBrokerageClass': propBrokerageClass,
                                 'Price': price,
                                 'Qty': qty
                            }
                            testname = 'NewOrder_Side:' + str(side) + '_ExecCond:' + str(execCond) + '_Price:' + str(price) + '_Reject'
                            ahd_service.expect(ordid, expected_msg, testname) 

                            ordids.append(ordid)

                            if i == repeat+1:
                                # Client should be disabled on the if max_dup_limit is reached
                                client_status = ahd_service.zcmd.get_client_status(CLIENT_ID, 'status')
                                testname = 'Client should be disabled'
                                ahd_service.expect_field(client_status, 'Disabled', 'ClientStatus', testname) 

                                # Modification should be rejected if max_dup_limit is reached
                                # Try modify price or qty
                                if price == mkt_order_price:
                                    ahd_service.sendMod(ordids[0], symbol, qty = qty / 2)
                                else:
                                    ahd_service.sendMod(ordids[0], symbol, price = price + 1)

                                expected_msg = {
                                    'DataClassCode': 'F231',
                                    'MsgType': '50',
                                    'ReasonCode': '8020'
                                }
                                ahd_service.expect(ordids[0], expected_msg, testname)

                                # Cancel should be accepted if max_dup_limit is reached  
                                ahd_service.sendCancel(ordids[1], symbol)

                                expected_msg = {
                                    'DataClassCode': 'F221',
                                    'MsgType': '50',
                                    'ReasonCode': '0000'
                                }
                                ahd_service.expect(ordids[1], expected_msg, testname)
        



    def test_duplicateOrders_

