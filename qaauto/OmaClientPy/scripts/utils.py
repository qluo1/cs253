""" local helper.

"""
import logging
from pynvp.nvpData import NVPData

log = logging.getLogger(__name__)

### helper
def _splitOrderId(orderId):
    """ based on orderId work out system, order#, date.  """

    if "|" in orderId:
        orderId = orderId.split("|")[0]
    firstDigit = -1
    for i in range(len(orderId)):
        if str.isdigit(orderId[i:]):
            ## system, date, orderNumber
            return (orderId[:i], int(orderId[-8:]),int(orderId[i:-8]))

    raise ValueError("not a valid oma orderId: %s" % orderId)

#from rediscli import c as db, list_order_history
class RdbHelper:
    """ helper for nvp redis. """
    def __init__(self,db):
        self.rdb_ = db
    def order_history(self,orderId):
        """ list order history. """
        if "|" in orderId:
            orderId = orderId.split("|")[0]

        ## parse as oma order, sorted by order version.
        return sorted([o for o in self.rdb_.scan_iter("%s*" % orderId)],key=lambda x: int(x.split("|")[1]))

    ## helper method list members for the set
    def set_members(self,name):
        members =  self.rdb_.smembers(name)
        ## sorted by (order date, orderId)
        if members:
            return sorted([o for o in members],key=lambda x: (int(x[-8:]),int(x[7:-8])))

    def smembers(self,name):
        """ """
        members = self.rdb_.smembers(name)
        if members:
            try:
                ## remove duplicated orderId, sorted by date/orderNumber
                members  = sorted(list(set([i.split("|")[0] for i in members])),key=lambda x: _splitOrderId(x)[1:])
                log.debug("sorted members: %s" % members)
                for member in members:
                    ## filter order by date
                    log.debug("list order hist of:  %s" % member)
                    hist = self.order_history(member)
                    order = None
                    for order in hist:
                        log.debug("process order: %s" % order)
                        data = self.rdb_.get(order)
                        nvpData = NVPData(data)
                        yield nvpData
                    ## clean up empty order in list
                    if order is None:
                        log.debug("remove member: %s" % member)
                        self.rdb_.srem(name, member)
            except Exception,e:
                log.exception(e)

    def get(self,key):
        """ """
        return self.rdb_.get(key)

