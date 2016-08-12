import logging
import gevent
import zerorpc
import re

from conf import settings

log = logging.getLogger(__name__)

COMPONENT_RAPTOR = 'raptor'
COMPONENT_MXSIM = 'mxsim'

class Zcmd(object):
    def __init__(self):
        self.zcmd_service_ = zerorpc.Client(settings.ZCMD_API_ENDPOINT, heartbeat = 30, timeout = 60)

    def market_open_ct(self):
        args = 'HKG.marketStatus -i CT -s O'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_RAPTOR, args)

    def turn_off_matching(self):
        args = 'cf --autoMatch=0 --fill=0'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def turn_on_matching(self):
        args = 'cf --autoMatch=1 --fill=1'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def list_open_orders(self):
        args = ['list']
        ret = self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)
        ret = ret.split('\n')
        order_ids = []
        for line in ret:
            m = re.search('OrderID=(\d+)', line)
            if m:
                order_ids.append(m.groups()[0])
        return order_ids

    def cancel_open_orders(self):
        """
            - This method should only be called for clean-up purpose
            - DC and FIX message will be generated after canceling order by zcmd
        """
        open_orders = self.list_open_orders()
        for order in open_orders:
            self.cancel_order(order)

    def cancel_order(self, order_id):
        args = ['cancel', order_id]
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

