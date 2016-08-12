from conf import settings

import pytest
import gevent
import zerorpc
import logging
import copy

fix_session = "RONINDO"
dc_session = "DC_RAPTOR"

log = logging.getLogger(__name__)

from tests._utils import verify_fix_message
from tests.fix_util import FIXOrder
        
class TestBasicExecution:
    """
    """
    def test_basic_execution(self, fix, dc, zcmd):

        # Turn on matching
        zcmd.turn_on_matching()
        
        order_buy = {
                'side': 'Buy',
                'symbol': '0001.HK',
                'ordType': "Market",
                'qty': 1000,
                'extra': {
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : '0001.HK',
                      }
                }

        order_sell = {
                'side': 'Sell',
                'symbol': '0001.HK',
                'ordType': "Market",
                'qty': 1000,
                'extra': {
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : '0001.HK',
                      }
                }

        test_order_buy = FIXOrder(fix_session, order_buy, fix_listener = fix, dc_listener = dc)
        test_order_sell = FIXOrder(fix_session, order_sell, fix_listener = fix, dc_listener = dc)
        ## submit new order
        clOrdId_buy = test_order_buy.new()
        clOrdId_sell = test_order_sell.new()

        ## get ACK message
        buy_ack = fix.get_message(session = fix_session, cl_ord_id = clOrdId_buy, expected_num_msg = 1)
        sell_ack = fix.get_message(session = fix_session, cl_ord_id = clOrdId_sell, expected_num_msg = 1)
        
        ## get DC
        buy_dc = dc.get_dc_message(cl_ord_id = clOrdId_buy, expected_num_msg = 2)
        sell_dc = dc.get_dc_message(cl_ord_id = clOrdId_sell, expected_num_msg = 2)
        
        ## get Execution message
        buy_execution = fix.get_message(session = fix_session, cl_ord_id = clOrdId_buy, expected_num_msg = 1)
        sell_execution = fix.get_message(session = fix_session, cl_ord_id = clOrdId_sell, expected_num_msg = 1)

        expected_buy_execution = {
            'MsgType': 'ExecutionReport',
            'OrderQty': 1000,
            'LastShares': 1000,
            'CumQty': 1000,
            'OrdType': 'Market',
            'ExecType': 'Fill',
            'OrdStatus': 'Filled',
            'LeavesQty': 0,
            'Side': 'Buy'
        }
        verify_fix_message(buy_execution[0], expected_buy_execution)

        expected_sell_execution = copy.deepcopy(expected_buy_execution)
        expected_sell_execution['Side'] = 'Sell'
        verify_fix_message(sell_execution[0], expected_sell_execution)

        ## get Execution DC
        buy_execution_dc = dc.get_dc_message(cl_ord_id = clOrdId_buy, expected_num_msg = 1)
        sell_execution_dc  = dc.get_dc_message(cl_ord_id = clOrdId_sell, expected_num_msg = 1)
        
        expected_buy_execution_dc = copy.deepcopy(expected_buy_execution)
        verify_fix_message(buy_execution_dc[0], expected_buy_execution_dc)

        expected_sell_execution_dc = copy.deepcopy(expected_sell_execution)
        verify_fix_message(sell_execution_dc[0], expected_sell_execution_dc)



