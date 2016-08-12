""" in memory, oma order graph.

source system: XTDb, XPXz, etc.

system has collection of -> parent_orders, child_orders


parent order has graph track version of parent orders and fills

child order has a graph track version of child orders, fills and related parent order/version

pt_wave has a graph track all parent orders.

"""
import sys
import os
import time
import logging
import zerorpc
import localcfg
import traceback
## check which environment
from conf import settings

import pynvp.MultiDict as MultiDict
from pynvp.nvpData import NVPData

## rds db helper
from utils import RdbHelper
_db_helper = RdbHelper(localcfg.rdb)

log = logging.getLogger(__name__)

class OmaOrder(object):
    """ """

    def __init__(self,nvpData):
        """ """
        assert isinstance(nvpData,MultiDict.OrderedMultiDict)
        self.versions_ = []
        self.parent_ = None
        self.childs_ = []
        self.symbol_ = None
        self.side_ = None
        self.qty_ = None
        self.price_ = None
        self.status_ = None
        self.tif_ = None
        self.aucea_orderId_ = None

        order = nvpData.get("OmaOrder") or nvpData.get("OmaStandAloneExecution")
        self.orderId_ = order["OmaNvpUniqueTag"]
        orderVersion = order["OmaNvpVersionNumber"]

        ## this is a child order
        if "ParentWrapper" in order:
            parentId = order["ParentWrapper"]["OmaNvpUniqueTag"]
            parentVersiona = order["ParentWrapper"]["OmaNvpVersionNumber"]
            self.parent_ = (parentId,parentVersiona)

        if "OmaExecution" in nvpData:
            self.versions_.append((orderVersion,True))
        else:
            self.versions_.append((orderVersion,False))

        if "OmaStatus" in order:
            self.status_ = order["OmaStatus"]["OmaNvpStatus"]
        ## capture more attrs
        alias_list  = order["ProductInformation"]["ProductAliasList"].getall("ProductAlias")
        for alias in alias_list:
            if alias['OmaNvpProductIdType'] == "Ticker" and alias['OmaNvpProductIdSubType'] == "AX":
                self.symbol_ = alias['OmaNvpProductId']
                break
        if not self.symbol_ and "OmaNvpFIXSymbol" in order:
            self.symbol_ = order["OmaNvpFIXSymbol"]

        self.side_ = order["OmaNvpSide"]
        self.qty_ = order["OmaNvpQuantity"]
        self.price_ = order.get("OmaNvpLimitPrice")

        if "OmaNvpTimeInForce" in order:
            self.tif_ = order["OmaNvpTimeInForce"]

        if "OmaLocationInformation" in order:
            locs = order.getall("OmaLocationInformation")
            for loc in locs:
                if loc["OmaNvpSystemName"].endswith("AUCEA"):
                    self.aucea_orderId_ = loc["OmaNvpTag"]

    @property
    def orderId(self):
        return self.orderId_

    @property
    def versions(self):
        return self.versions_

    @property
    def parent(self):
        """ return parent orderId and version """
        return self.parent_
    @property
    def childs(self):
        """ expose childs. """
        return self.childs_

    def nvp_formatted(self,version=0):
        """ return order nvp MultiDict."""

        ver = [v for v in self.versions_ if v[0] == version]
        assert ver and len(ver) == 1
        ver = ver[0]
        if ver[1]: 
            lookupId = "%s|%d|fill" % (self.orderId, version)
        else:
            lookupId = "%s|%d" % (self.orderId, version)

        nvp = _db_helper.get(lookupId)
        assert nvp,"no nvp found in db: %s" % lokupId
        return NVPData(nvp).root_.toList()

    def nvp_raw(self,version=0):
        """ return raw nvp data. """
        ver = [v for v in self.versions_ if v[0] == version]
        assert ver and len(ver) == 1
        ver = ver[0]
        if ver[1]: 
            lookupId = "%s|%d|fill" % (self.orderId, version)
        else:
            lookupId = "%s|%d" % (self.orderId, version)

        nvp = _db_helper.get(lookupId)
        if not nvp:
            raise ValueError("no nvp found in db: %s" % lookupId)
        return nvp

    @property
    def to_json(self):
        """ """
        ret =  {'orderId': self.orderId,
                'versions': self.versions,
                'parent': self.parent,
                'symbol': self.symbol_,
                'side': self.side_,
                'qty': self.qty_,
                'price': self.price_,
                'status': self.status_,
                'tif': self.tif_,
                }
        if self.parent is None and len(self.childs) > 0:
            ret['childs'] = [i.to_json for i in self.childs]
        if self.aucea_orderId_:
            ret['aucea'] = self.aucea_orderId_
        return ret

    def __eq__(self,order):
        if isinstance(order,self.__class__):
            return order.orderId == self.orderId
        if isinstance(order,str):
            return order == self.orderId

    def __str__(self):
        return "%s:%s:%s" % (self.orderId,self.versions_,self.parent_)

    def __repr__(self):
        return self.__str__()

    def update(self,nvpData):
        """ update order version. """
        assert isinstance(nvpData,MultiDict.OrderedMultiDict)

        order = nvpData.get("OmaOrder") or nvpData.get("OmaStandAloneExecution")
        orderId = order["OmaNvpUniqueTag"]
        orderVersion = order["OmaNvpVersionNumber"]

        assert orderId == self.orderId_
        update_version = False
        if  orderVersion in [i[0] for i in self.versions_]:
            update_version = True
            log.debug("version already exist: %s" % nvpData)
        if not update_version:
            ## add order version
            if "OmaExecution" in nvpData:
                self.versions_.append((orderVersion,True))
            else:
                self.versions_.append((orderVersion,False))
        else:
            if "OmaExecution" in nvpData:
                for idx,ver in enumerate(self.versions_):
                    if ver[0] == orderVersion and ver[1] == False:
                        #log.info("ver: %s" % str(ver))
                        # replace old version with new one
                        self.versions_[idx] = (ver[0],True)
        ## update status based on latest version
        if "OmaStatus" in order:
            self.status_ = order["OmaStatus"]["OmaNvpStatus"]
        ## todo: track aucea orderId
        if "OmaLocationInformation" in order:

            locs = order.getall("OmaLocationInformation")
            for loc in locs:
                if loc["OmaNvpSystemName"].endswith("AUCEA"):
                    self.aucea_orderId_ = loc["OmaNvpTag"]


class OmaRegister(object):
    """
    """
    ## internal register
    _register = {
    }

    ## setup register
    if not _register.keys():
        for oma in settings.OMA_SVRS:
            print oma
            _register[oma] = []

    def _load_from_redis(self):
        """ pupulate internal register from redis db."""

        log.info(" ===========> load from redis <===========")
        #import pdb;pdb.set_trace()
        for k,v in self._register.iteritems():
            log.debug("load %s" % k)
            for nvpData in _db_helper.smembers(k):
                self._process_nvp(k,nvpData.root_)

        log.info(" ===========> load completed <===========")

    def _process_nvp(self,system, nvpData):
        """ realtime process """
        log.debug("process nvp: %s, %s" % (system,nvpData))
        assert isinstance(nvpData,MultiDict.OrderedMultiDict)
        ## ignore not configured oma
        if system not in self._register.keys(): return

        if "OmaOrder" in nvpData or "OmaStandAloneExecution" in nvpData:
            order = nvpData.get("OmaOrder") or nvpData.get("OmaStandAloneExecution")
            orderId = order["OmaNvpUniqueTag"]
            orderVersion = order["OmaNvpVersionNumber"]

            if orderId and orderId not in self._register[system]:
                log.info("append order to registery: %s" % orderId)
                self._register[system].append(OmaOrder(nvpData))
            else:
                log.info("update order in registery: %s" % orderId)
                found = [o for o in self._register[system] if o == orderId]
                assert len(found) == 1
                found = found[0]
                found.update(nvpData)

            #link child to parent
            found = [o for o in self._register[system] if o == orderId]
            assert len(found) == 1
            found = found[0]
            if found.parent:
                log.info('order with parent: %s' % found)
                parent = [o for o in self._register[system] if o.orderId == found.parent[0]]
                if parent and len(parent) == 1 and found not in parent[0].childs:
                    log.info("found parent: %s" % parent)
                    parent[0].childs.append(found)


    def _iter_order(self,system):
        assert system in self._register.keys()
        return iter(self._register[system])

    @zerorpc.stream
    def list_orders(self,system,**kw):
        """ """
        if system not in self._register.keys():
            raise ValueError("system: %s not registered" % system)

        parentOnly = kw.get("parentOnly",False)
        childOnly = kw.get("childOnly",False)
        fillOnly = kw.get("fillOnly",False)

        for order in self._iter_order(system):

            ##skip child order 
            if parentOnly and order.parent: continue

            if childOnly and order.parent is None: continue

            if fillOnly:
                if True not in set([v[1] for v in order.versions]): continue

            yield order.orderId

    def get_order(self,orderId,**kwargs):
        """ """
        ## default formatted
        version = kwargs.get("version",0)
        nvp = kwargs.get("nvp",False)
        raw = kwargs.get("raw",False)
        for key in self._register.keys():
            if orderId.startswith(key):
                for order in self._register[key]:
                    if order.orderId == orderId:
                        if nvp:
                            if raw:
                                return order.nvp_raw(version)
                            else:
                                return order.nvp_formatted(version)
                        else:
                            return order.to_json

    def get_order_history(self,orderId):
        """ list version of order. """
        hist = _db_helper.order_history(orderId)
        if  len(self.hist_)  == 0:
            raise ValueError("orderId: %s not exist in redis" %  orderId)
        return hist

    def list_system(self):
        """ """
        ret = {}
        for k,v in self._register.iteritems():
            ret[k] = len(v)
        return ret

    def cleanup_registery(self):
        """ clean up set for item has been expired by redis. """
        for k,v in self._register.iteritems():
            log.info("clean up system: %s" % k)
            for order in v:
                hist = _db_helper.order_history(order.orderId)
                if not hist:
                    log.info("remove order: %s " % order)
                    v.pop(order)

        return self.list_system()

