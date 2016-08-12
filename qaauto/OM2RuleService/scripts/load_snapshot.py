""" load snapshot from json filed, which generated out of rds snapshot.



"""
import logging
import os
import cfg
from cfg import json
from conf import settings
import gevent

log = logging.getLogger(__name__)

from treelib import Node,Tree,NodeIDAbsentError
def _parsing_controls(controls):
    """ parsing rds line items and return control items.

    input: control data in list.
    output:
        sizeLimits in dict. key: symbol, value: sizeLimit.
        default size_limit key: notional-local.SYDE, notional-local.CHIA

        priceControl in tree.
    """

    tree_price_aggressive = Tree()
    size_limits = {}

    ## iter each line of rds record. sequence matter here for update records.
    #for item in gen_price_ctrol_data(root):
    for item in controls:

        assert isinstance(item,dict)
        log.debug("item: %s" %  item)

        key = item['LimitKey']
        keys = key.split(".")
        ## patch symbol
        if keys[-1] in ("AX","CHA"):
            keys = keys[:-2] + [keys[-2] + "." + keys[-1]]
        ## asia.stock only
        if keys[0] == 'asia' and keys[1] == "stock":
            ## price control item
            if keys[2] != "size":
                ## add node from list
                item.pop("LimitKey")
                action = item.pop("action")
                if action == "Insert" or action == "Update" and tree_price_aggressive.get_node(".".join(keys)) == None:
                    tree_price_aggressive.add_node_from_list(keys,item)
                elif action == "Update":
                    update_node = tree_price_aggressive.get_node(".".join(keys))
                    assert update_node
                    update_node.data = [item]
                elif action == "Delete":
                    ## remove node
                    #print "delete", ".".join(keys)
                    tree_price_aggressive.remove_node(".".join(keys))
            else:
                ## size limit item
                key,val = item['LimitKey'],item['LimitValue']

                if key.startswith("asia.stock.size.eq1d-size-notional-product.notional-local"):
                    size_limits[".".join(keys[5:])] = val
                else:
                    #assert False
                    size_limits[".".join(keys[3:])] = val

    return {
            'price': tree_price_aggressive,
            'size': size_limits,
            }

def _parse_rds_account(accounts):
    """ convert rds data into reg data. """
    xrefs = set([i['accountSynonym'] for i in accounts if i['accountSynonymType'] == 38])
    oeids = set([i['accountSynonym'] for i in accounts if i['accountSynonymType'] == 10])
    starids = set([i['accountSynonym'] for i in accounts if i['accountSynonymType'] == 5])
    accts = set([i['accountSynonym'] for i in accounts if i['accountSynonymType'] == 3])

    regdata_xref = {}
    regdata_oeid = {}
    regdata_starid = {}
    regdata_acct = {}
    #import pdb;pdb.set_trace()
    for xref in xrefs:
        gevent.sleep(0)
        items = [i for i in accounts if i['accountSynonym'] == xref]
        ret = {}
        for item in items:
            ret[item['propertyName'] ] = item.get('propertyValue',None)
            ret['accountSynonymType'] = item['accountSynonymType']
        regdata_xref[xref] = ret

    for xref in oeids:
        gevent.sleep(0)
        items = [i for i in accounts if i['accountSynonym'] == xref]
        ret = {}
        for item in items:
            ret[item['propertyName'] ] = item.get('propertyValue',None)
            ret['accountSynonymType'] = item['accountSynonymType']
        regdata_oeid[xref] = ret

    for xref in starids:
        gevent.sleep(0)
        items = [i for i in accounts if i['accountSynonym'] == xref]
        ret = {}
        for item in items:
            ret[item['propertyName'] ] = item.get('propertyValue',None)
            ret['accountSynonymType'] = item['accountSynonymType']
        regdata_starid[xref] = ret

    for xref in accts:
        gevent.sleep(0)
        items = [i for i in accounts if i['accountSynonym'] == xref]
        ret = {}
        for item in items:
            ret[item['propertyName'] ] = item.get('propertyValue',None)
            ret['accountSynonymType'] = item['accountSynonymType']
        regdata_acct[xref] = ret

    return {'xref': regdata_xref,
            'oeid': regdata_oeid,
            'starid': regdata_starid,
            'tam': regdata_acct,
            }


class RDS_Snapshot:
    """ load rds from json file.

    input: env

    attrs:
        rds_account
        rds_control
        rds_product
    """

    def __init__(self,env="PME_RDS"):
        """ load rds snaptshot data from generated json file."""

        assert env in settings.OM2_PATHS
        _input = os.path.join(settings.GENRATED_SNAPSHOTS,env)
        ## TODO: find latest by timestamp
        _latest = sorted([r for r in os.listdir(_input)])[-1]

        _filename = os.path.join(_input,_latest)
        assert os.path.exists(_filename)
        log.info("loading json: %s" % _filename)
        data = json.load(open(_filename,"r"))

        rds_product = data['RdsTransactionalProduct']
        rds_control = data['RdsFlowTradingControlLimit']
        rds_account = data['RdsAccountPropertyInfo']

        self.data_=  {
                    'product': rds_product,
                    'control': rds_control,
                    'account': rds_account,
                    }

        log.info("loaded: %s" % len(rds_account))

        self.cache_ = {}

    @property
    def rds_product(self):
        """ """
        assert self.data_  and 'product' in self.data_
        assert isinstance(self.data_['product'],list)


        if 'product' in self.cache_:
            return self.cache_['product']

        out = {}
        for prod in self.data_['product']:
            #import pdb;pdb.set_trace()
            gevent.sleep(0)
            action = prod['action']
            productId = int(prod['data'].pop("productId"))
            if action in ("Insert","Update"):
                out[productId] = prod['data']
            elif action == "Delete":
                if productId in out:
                    del out[productId]
            else:
                raise ValueError("unexpected action: %s" % action)

        ## convert list to dict for product.
        stock = {}
        warrant = {}
        index = {}
        right = {}
        stock_ticker = {}
        for k,v in out.iteritems():
            if 'productSummaryInfo' in v:
                if v['productSummaryInfo']['productType'] == 0:
                    stock[k] = v
                elif v['productSummaryInfo']['productType'] == 6:
                    warrant[k] = v
                elif v['productSummaryInfo']['productType'] == 4:
                    index[k] = v
                elif v['productSummaryInfo']['productType'] == 7:
                    right[k] = v
                else:
                    raise ValueError("unexpected productType: %s, %s "%(v['productSummaryInfo']['productType'], v))

                if v['productSummaryInfo'].get("productSynonymPrimaryRic"):
                    stock_ticker[v['productSummaryInfo']["productSynonymPrimaryRic"]] = v

        ## only interested stock ticker
        self.cache_['product'] = stock_ticker
        return stock_ticker


    @property
    def rds_control(self):
        """ """

        if 'control' in self.cache_:
            return self.cache_['control']

        ## convert list to dict for control
        controls = []
        assert self.data_  and 'control' in self.data_
        assert isinstance(self.data_['control'],list)

        for control in self.data_['control']:
            action = control['action']
            data = control['data']
            control_key = control['data']['tradingControlLimitKey']

            ret = {'action': action}
            for k, v in data.iteritems():
                if k == "tradingControlLimitKey":
                    ret['LimitKey'] = v
                elif k == "tradingControlLimitValue":
                    ret['LimitValue'] = v
                elif k == "tradingControlLimitValueStr" and v:
                    ret['LimitValueStr'] = v
                elif k == "tradingControlLimitSubkey" and v:
                    ret['LimitSubkey'] = v
                elif k == "tradingControlLimitSubkeyStr" and v:
                    ret['LimitSubkeyStr'] = v
                else:
                    pass
            if control_key.startswith("asia.stock.size"):
                controls.append(ret)
            elif control_key.startswith("asia.stock.price-aggressive"):
                controls.append(ret)
            else:
                print ("unexpected control key: %s" % control_key)

        ret =  _parsing_controls(controls)
        self.cache_['control'] = ret
        return ret

    @property
    def rds_account(self):
        """ """

        if 'account' in self.cache_:
            return self.cache_['account']

        assert self.data_  and 'account' in self.data_
        assert isinstance(self.data_['account'],list)

        res = []
        for account in self.data_['account']:
            action = account['action']
            data = account['data']
            ## ignore chia
            if data['market'] != 'CHIA':
                res.append(data)
            gevent.sleep(0)

        ret =  _parse_rds_account(res)

        self.cache_['account'] = ret
        return ret

"""
def load_snapshot(name):
    """ """

    filename = os.path.join(settings.RDSDATA,"snapshots",name + ".json")
    if not os.path.exists(filename):
        raise ValueError("snapshot file not found: %s" % filename)


    data = json.load(open(filename,"r"))

    rds_product = data['RdsTransactionalProduct']
    rds_control = data['RdsFlowTradingControlLimit']
    rds_account = data['RdsAccountPropertyInfo']

    return {'product': rds_product,
            'control': rds_control,
            'account': rds_account,
            }


def process_rds_control(rds_control):
    """ """
    ## convert list to dict for control
    controls = []

    for control in rds_control:
        action = control['action']
        data = control['data']
        control_key = control['data']['tradingControlLimitKey']

        ret = {'action': action}
        for k, v in data.iteritems():
            if k == "tradingControlLimitKey":
                ret['LimitKey'] = v
            elif k == "tradingControlLimitValue":
                ret['LimitValue'] = v
            elif k == "tradingControlLimitValueStr" and v:
                ret['LimitValueStr'] = v
            elif k == "tradingControlLimitSubkey" and v:
                ret['LimitSubkey'] = v
            elif k == "tradingControlLimitSubkeyStr" and v:
                ret['LimitSubkeyStr'] = v
            else:
                pass
        if control_key.startswith("asia.stock.size"):
            controls.append(ret)
        elif control_key.startswith("asia.stock.price-aggressive"):
            controls.append(ret)
        else:
            print ("unexpected control key: %s" % control_key)

    return _parsing_controls(controls)

def process_rds_account(rds_account):
    """ """
    res = []
    for account in rds_account:
        action = account['action']
        data = account['data']
        res.append(data)

    return res


def process_rds_product(rds_product):
    """ """
    assert isinstance(rds_product,list)
    out = {}
    for prod in rds_product:
        #import pdb;pdb.set_trace()
        action = prod['action']
        productId = int(prod['data'].pop("productId"))
        if action in ("Insert","Update"):
            out[productId] = prod['data']
        elif action == "Delete":
            if productId in out:
                del out[productId]
        else:
            raise ValueError("unexpected action: %s" % action)

    ## convert list to dict for product.
    stock = {}
    warrant = {}
    index = {}
    right = {}
    stock_ticker = {}
    for k,v in out.iteritems():
        if 'productSummaryInfo' in v:
            if v['productSummaryInfo']['productType'] == 0:
                stock[k] = v
            elif v['productSummaryInfo']['productType'] == 6:
                warrant[k] = v
            elif v['productSummaryInfo']['productType'] == 4:
                index[k] = v
            elif v['productSummaryInfo']['productType'] == 7:
                right[k] = v
            else:
                raise ValueError("unexpected productType: %s, %s "%(v['productSummaryInfo']['productType'], v))

            if v['productSummaryInfo'].get("productSynonymPrimaryRic"):
                stock_ticker[v['productSummaryInfo']["productSynonymPrimaryRic"]] = v

    return stock_ticker

def process_rds_control(rds_control):
    """ """
    ## convert list to dict for control
    controls = []

    for control in rds_control:
        action = control['action']
        data = control['data']
        control_key = control['data']['tradingControlLimitKey']

        ret = {'action': action}
        for k, v in data.iteritems():
            if k == "tradingControlLimitKey":
                ret['LimitKey'] = v
            elif k == "tradingControlLimitValue":
                ret['LimitValue'] = v
            elif k == "tradingControlLimitValueStr" and v:
                ret['LimitValueStr'] = v
            elif k == "tradingControlLimitSubkey" and v:
                ret['LimitSubkey'] = v
            elif k == "tradingControlLimitSubkeyStr" and v:
                ret['LimitSubkeyStr'] = v
            else:
                pass
        if control_key.startswith("asia.stock.size"):
            controls.append(ret)
        elif control_key.startswith("asia.stock.price-aggressive"):
            controls.append(ret)
        else:
            print ("unexpected control key: %s" % control_key)

    return _parsing_controls(controls)

"""

if __name__ == "__main__":
    """ """
    snapshot = RDS_Snapshot("PME_RDS")
    accounts = snapshot.rds_account

    from pprint import pprint
    pprint(accounts)


