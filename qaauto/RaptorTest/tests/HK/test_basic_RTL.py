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
        
class TestBasicRTL:
    """
    """
    def test_basic_rejection(self, fix, dc, zcmd):

        # Turn off matching
        zcmd.turn_off_matching()
        
        order = {
                'side': 'Buy',
                'symbol': '773.HK',
                'ordType': "Market",
                'qty': 1000,
                'extra': {
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : '773.HK',
                      }
                }

        test_order = FIXOrder(fix_session, order, fix_listener = fix, dc_listener = dc)

        ## submit new order
        clOrdId = test_order.new()

        ## get reject message
        rej = fix.get_message(session = fix_session, cl_ord_id = clOrdId, expected_num_msg = 1)
        
        ## get DC
        dc_msg = dc.get_dc_message(cl_ord_id = clOrdId, expected_num_msg = 2)
        
        expected_rej = {
            'MsgType': 'ExecutionReport',
            'OrderQty': 1000,
            'LastShares': 0,
            'CumQty': 0,
            'OrdType': 'Market',
            'ExecType': 'Rejected',
            'OrdStatus': 'Rejected',
            'LeavesQty': 0,
            'Side': 'Buy'
        }
        verify_fix_message(rej[0], expected_rej)

        verify_fix_message(dc_msg[1], expected_rej)


    def test_rtl(self, fix, dc, zcmd):

        order = {
                'side': 'Buy',
                'symbol': '2588.HK',
                'ordType': "Market",
                'qty': 1000,
                'extra': {
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : '2588.HK',
                      }
        }
        
        test_order = FIXOrder(fix_session, order, fix_listener = fix, dc_listener = dc)
        
        ## submit new order
        clOrdId = test_order.new()
        
        ## reject
        rej = fix.get_message(session = fix_session, cl_ord_id = clOrdId, expected_num_msg = 1)

        expected_rej = {
            'MsgType': 'ExecutionReport',
            'ExecType': 'Rejected',
            'OrdStatus': 'Rejected',
            'Text': 'ClientRestrictedBuy risk filtered',
            'OrdRejReason': 'Broker option'
        }
        verify_fix_message(rej[0], expected_rej)

        ## get DC
        dc_msg = dc.get_dc_message(cl_ord_id = clOrdId, expected_num_msg = 2)
        verify_fix_message(dc_msg[1], expected_rej)



