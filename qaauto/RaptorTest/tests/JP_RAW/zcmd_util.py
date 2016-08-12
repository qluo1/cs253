import logging
import gevent
import zerorpc
import re
import os

from conf import settings

log = logging.getLogger(__name__)

COMPONENT_RAPTOR='raptor'
COMPONENT_MXSIM='mxsim'

class Zcmd(object):
    def __init__(self):
        self.zcmd_service_ = zerorpc.Client(settings.ZCMD_API_ENDPOINT, heartbeat = 30, timeout = 60)

    def turn_on_matching(self):
        log.info('Calling Zcmd turn_on_matching')
        args = 'cf --autoMatch=1 --fill=1'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def turn_off_matching(self):
        log.info('Calling Zcmd turn_off_matching')
        args = 'cf --autoMatch=0 --fill=0'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def turn_on_fill(self):
        log.info('Calling Zcmd turn_on_fill')
        args = 'cf --fill=1'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def turn_off_fill(self):
        log.info('Calling Zcmd turn_off_fill')
        args = 'cf --fill=0'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def turn_on_partial_fill(self):
        log.info('Calling Zcmd turn_on_partial_fill')
        args = 'cf --fillPartial=1'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def turn_off_partial_fill(self):
        log.info('Calling Zcmd turn_off_partial_fill')
        args = 'cf --fillPartial=0'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args)

    def reload_restrictions(self):
        log.info('Calling Zcmd reload_restriction')
        args = 'restriction " < ' + os.getenv('REF_DATA_PATH') + '/restrictions.csv "'
        args = args.split()
        self.zcmd_service_.send_zcmd(COMPONENT_RAPTOR, args)

#    def set_ClientLimits(self):
#        log.info('Calling Zcmd set_ClientLimits')
#        args = 'limits " < ' + os.getenv('REF_DATA_PATH') + '/clientLimits.csv "'
#        args = args.split()
#        self.zcmd_service_.send_zcmd(COMPONENT_RAPTOR, args)
    def set_client_limits(self, client_id, limits_dict):
        log.info('Calling zcmd set_client_limits with following parameters: %s' % str(limits_dict))
        args = ['limits', '--func=A']
        for limit in limits_dict:
            args.append('--' + limit + '=' + limits_dict[limit])
        ## TODO: now the EXDEST and SECTYPE is hardcoded
        args += ['XTKS', 'CS', client_id]
        self.zcmd_service_.send_zcmd(COMPONENT_RAPTOR, args)

    def get_client_status(self, client_id, query_field):
        log.info('Calling Zcmd get_client_id on client_id %s with field %s' % (client_id, query_field))
        args = ['acct', client_id]
        ret = self.zcmd_service_.send_zcmd(COMPONENT_RAPTOR, args)
        for line in ret:
            m = re.search('clientID = ' + client_id, line)
            if m:
                m = re.search(query_field + ' = (.*)\]'
                if m:
                    return m.groups()[0]
        return None

    def enable_client(self, client_id):
        log.info('Calling zcmd enable_client on client_id: %s' % client_id)
        args = ['acct', '-e', client_id]
        self.zcmd_service_.send_zcmd(COMPONENT_RAPTOR, args)

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
        log.info('Calling Zcmd cancel_open_orders')
        open_orders = self.list_open_orders()
        for order in open_orders:
            self.cancel_order(order)

    def cancel_order(self, order_id):
        args = ['cancel', order_id]
        self.zcmd_service_.send_zcmd(COMPONENT_MXSIM, args) 
