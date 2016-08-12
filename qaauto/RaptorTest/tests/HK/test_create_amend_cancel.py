from conf import settings

import pytest
import gevent
import zerorpc
import logging
import copy

fix_session = "RONINDO"
dc_session = "DC_RAPTOR"

log = logging.getLogger(__name__)

from tests._utils import verify_fix_message, clean_up
from tests.fix_util import FIXOrder
        
class TestRaptor:

    def test_new_amend_cancel(self, zcmd, fix, dc):
        """ """

        order = {
                'side': 'Buy',
                'symbol': '0001.HK',
                'ordType': "Limit",
                'price': 90,
                'qty': 1000,
                'extra': {
                      "HandlInst"   : "auto-private",
                      "IDSource"    : "RIC code",
                      "SecurityID"  : '0001.HK',
                      }
                }
        ## send market open
        zcmd.market_open_ct()
        zcmd.turn_off_matching()

        test_order = FIXOrder(fix_session, order, fix_listener = fix, dc_listener = dc)
        ## submit new order
        clOrdId = test_order.new()

        ## verify return message
        ret_msg = fix.get_message(session = fix_session, cl_ord_id = clOrdId, expected_num_msg = 1)[0]
        expected_ret_msg = {
            'MsgType': 'ExecutionReport',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 1000,
            'CumQty': 0,
            'OrdType': 'Limit',
            'ExecType': 'New',
            'ExecTransType': 'New',
            'OrdStatus': 'New',
            'Price': 90,
            'LeavesQty': 1000,
            'TimeInForce': 'Day'
        }
        verify_fix_message(ret_msg, expected_ret_msg)
        
        ## get dropcopy message
        dc_msg = dc.get_dc_message(cl_ord_id = clOrdId, expected_num_msg=2)

        ## verify dc message
        expected_dc_msg = {
            'MsgType': 'NewOrderSingle',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 1000,
            'OrdType': 'Limit',
            'Price': 90,
            'TimeInForce': 'Day',
            'ClientID': '11333292C', #what is this?
            'BookingType': 'RegularBooking',
            'OrderCapacity': 'Agency',
            'OnBehalfOfCompID': 'RONINDO_C'
        }
        verify_fix_message(dc_msg[0], expected_dc_msg)

        expected_dc_msg = {
            'MsgType': 'ExecutionReport',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 1000,
            'CumQty': 0,
            'OrdType': 'Limit',
            'ExecType': 'New',
            'ExecTransType': 'New',
            'OrdStatus': 'New',
            'Price': 90,
            'LeavesQty': 1000,
            'TimeInForce': 'Day',
            'ClientID': '11333292C', #what is this?
            'BookingType': 'RegularBooking',
            'OrderCapacity': 'Agency',
            'DeliverToCompID': 'RONINDO_C',
            # how to get to know the meaning of these custom tags?
            '9418': 'C',
            '9411': 'RONINDO_CLC',
            '9401': 'FIX.RONINDO',
            '9402': 'HKG.main'
        }
        verify_fix_message(dc_msg[1], expected_dc_msg)
        
        gevent.sleep(0.5)


        ## Amend
        clOrdId = test_order.amend(qty=order['qty'] + 2000,
                                   price=order['price'] + 0.50)
        ret_msg = fix.get_message(session = fix_session, cl_ord_id = clOrdId, expected_num_msg = 1)[0]
        expected_msg = {
            'MsgType': 'ExecutionReport',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 3000,
            'CumQty': 0,
            'OrdType': 'Limit',
            'ExecType': 'Replace',
            'ExecTransType': 'New',
            'OrdStatus': 'Replaced',
            'Price': 90.5,
            'LeavesQty': 3000,
            'TimeInForce': 'Day'
        }
        verify_fix_message(ret_msg, expected_msg)

        dc_msg = dc.get_dc_message(cl_ord_id = clOrdId, expected_num_msg=2)
        # For OrderCancelReplaceRequest and OrderCancelRequest type of DC message, BookingType field does not exist
        expected_dc_msg = {
            'MsgType': 'OrderCancelReplaceRequest',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 3000,
            'OrdType': 'Limit',
            'Price': 90.5,
            'TimeInForce': 'Day',
            'ClientID': '11333292C', #what is this?
            'OrderCapacity': 'Agency',
            'OnBehalfOfCompID': 'RONINDO_C'
        }
        verify_fix_message(dc_msg[0], expected_dc_msg)

        expected_dc_msg = {
            'MsgType': 'ExecutionReport',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 3000,
            'CumQty': 0,
            'OrdType': 'Limit',
            'ExecType': 'Replace',
            'ExecTransType': 'New',
            'OrdStatus': 'Replaced',
            'Price': 90.5,
            'LeavesQty': 3000,
            'TimeInForce': 'Day',
            'ClientID': '11333292C', #what is this?
            'BookingType': 'RegularBooking',
            'OrderCapacity': 'Agency',
            'DeliverToCompID': 'RONINDO_C',
            # how to get to know the meaning of these custom tags?
            '9418': 'C',
            '9411': 'RONINDO_CLC',
            '9401': 'FIX.RONINDO',
            '9402': 'HKG.main'
        }
        verify_fix_message(dc_msg[1], expected_dc_msg)
        gevent.sleep(0.5)

        ## Cancel
        clOrdId = test_order.cancel()
        ret_msg = fix.get_message(session = fix_session, cl_ord_id = clOrdId, expected_num_msg = 1)[0]
        expected_msg = {
            'MsgType': 'ExecutionReport',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 3000,
            'CumQty': 0,
            'OrdType': 'Limit',
            'ExecType': 'Canceled',
            'ExecTransType': 'New',
            'OrdStatus': 'Canceled',
            'Price': 90.5,
            'LeavesQty': 0,
            'TimeInForce': 'Day'
        }
        verify_fix_message(ret_msg, expected_msg)

        dc_msg = dc.get_dc_message(cl_ord_id = clOrdId, expected_num_msg=2)
        expected_dc_msg = {
            'MsgType': 'OrderCancelRequest',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 3000,
            'OrdType': 'Limit',
            'Price': 90.5,
            'TimeInForce': 'Day',
            'ClientID': '11333292C', #what is this?
            'OrderCapacity': 'Agency',
            'OnBehalfOfCompID': 'RONINDO_C'
        }
        verify_fix_message(dc_msg[0], expected_dc_msg)

        expected_dc_msg = {
            'MsgType': 'ExecutionReport',
            'Side': 'Buy',
            'Symbol': '0001.HK',
            'OrderQty': 3000,
            'CumQty': 0,
            'OrdType': 'Limit',
            'ExecType': 'Canceled',
            'ExecTransType': 'New',
            'OrdStatus': 'Canceled',
            'Price': 90.5,
            'LeavesQty': 0,
            'TimeInForce': 'Day',
            'ClientID': '11333292C', #what is this?
            'BookingType': 'RegularBooking',
            'OrderCapacity': 'Agency',
            'DeliverToCompID': 'RONINDO_C',
            # how to get to know the meaning of these custom tags?
            '9418': 'C',
            '9411': 'RONINDO_CLC',
            '9401': 'FIX.RONINDO',
            '9402': 'HKG.main'
        }
        verify_fix_message(dc_msg[1], expected_dc_msg)
        clean_up(zcmd = zcmd, fix_listener = fix, dc_listener = dc)


