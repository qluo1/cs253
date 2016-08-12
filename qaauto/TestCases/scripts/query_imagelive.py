""" query imagelive db for order info.

this is a utility script.

"""
import os
import sys
import logging
from datetime import datetime,timedelta
import traceback
from pprint import pprint

## setup local config
import cfg
import ujson as json
from om2CompleteCatalog import om2CompleteCatalog, om2CompleteCatalogEnums
from conf import settings
import zerorpc
import pymongo
env = os.environ['SETTINGS_MODULE'].split(".")[-1]
mongo_client = pymongo.MongoClient("mongodb://dss_client:dss_client@%s:%s" % settings.MONGO_CFG)
## dynamically set dss db based on instance.
mongo_database = eval("mongo_client.%s" % env)
## dss collection
dss_db = mongo_database.dss
## image live collection
imagelive_db = mongo_database.imagelive

from bson.code import Code
from collections import defaultdict
from docopt import docopt
import itertools

def imagelive_lookup(day=0,**kwargs):
    """ """

    days = datetime.now () - timedelta(days=int(day))

    date = days.strftime("%Y%m%d")

    if 'orderId' in kwargs:
        res = imagelive_db.find({'date':date,'recordId': kwargs['orderId']})
        return res

    ## default return today's the date's orders.
    res = imagelive_db.find({'date': date})
    return res

def _extract_order_hist(res_one):
    """ internal helper to extract order histoyr.

    input: orderId query result set.
    """
    ret = []
    for r in res_one:
        version,cur_order,status = r[0], r[1]['currentOrder'], r[1]['currentOrder']['orderStatusData']
        if 'relatedEntityIndexes' not in cur_order:
            ret.append([r[0],status['primaryStatus']])
        else:
            indexs = cur_order['relatedEntityIndexes']
            for index in indexs:
                if index['relatedEntityType'] in ("ChildOrder","Execution"):
                    ret.append([r[0],status['primaryStatus'],index['relatedEntityId']])
    return ret

def extract_fill_data(orderId):
    """ """
    assert orderId.endswith("E")

    fills = [f for f in imagelive_lookup(day,orderId=orderId)]
    ret = []
    for fill in fills:
        fill_data = fill['msg']['currentExecution']['executionData']

        fill_corr = fill['msg']['currentExecution'].get("executionCorrection")

        f = {orderId: {'lastMkt': fill_data['executionLastMarket'],
                       'venue': fill_data.get('executionPoint'),
                       'status': fill_data['executionStatus'],
                       'price': fill_data['executionPrice'],
                       'qty': fill_data['quantity'],
                       'subExecPoint': fill_data.get("subExecutionPoint")}}

        ret.append(f)

    if len(ret) == 1:
        return ret[0]
    return ret


def isSorChildOrder(orderId,**kw):
    """ internal helper to check if order is child."""

    day = kw.get("day",0)

    res = imagelive_lookup(day=day,orderId=orderId)

    res_one = [(r['version'],r['msg']) for r in res]
    if len(res_one) > 0:
        #import pdb;pdb.set_trace()
        first_order = res_one[0][1]
        isRootOrder = first_order['currentOrder']['orderStatusData'].get("isRootOrder") == 1 or \
                      first_order['currentOrder']['orderInstructionData'].get("isRootOrder") == 1
        isLeafOrder = first_order['currentOrder']['orderStatusData'].get("isLeafOrder") == 1 or \
                      first_order['currentOrder']['orderInstructionData'].get("isLeafOrder") == 1
        isSorManaged = first_order['currentOrder']['orderInstructionData'].get("isSorManagedOrder") ==1 or \
                       first_order['currentOrder']['orderStatusData'].get("isSorManagedOrder") ==1
        isSorChild = first_order['currentOrder']['orderInstructionData'].get("isSorChildOrder") == 1 or \
                     first_order['currentOrder']['orderStatusData'].get("isSorChildOrder") == 1

        if isSorChild:
            return True
        return False

def imagelive_graph(orderId,**kw):
    """ query graph of the order.

    TODO: extract externalReferences like to VikingOrder

    """

    day = kw.get("day",0)

    res = imagelive_lookup(day=day,orderId=orderId)

    #import pdb;pdb.set_trace()
    res_one = [(r['version'],r['msg']) for r in res]
    if len(res_one) > 0:
        #import pdb;pdb.set_trace()
        first_order = res_one[-1][-1]
        side = first_order['currentOrder']['orderInstructionData']['buySell']
        isRootOrder = first_order['currentOrder']['orderStatusData'].get("isRootOrder") == 1 or \
                      first_order['currentOrder']['orderInstructionData'].get("isRootOrder") == 1
        isLeafOrder = first_order['currentOrder']['orderStatusData'].get("isLeafOrder") == 1 or \
                      first_order['currentOrder']['orderInstructionData'].get("isLeafOrder") == 1
        isSorManaged = first_order['currentOrder']['orderInstructionData'].get("isSorManagedOrder") ==1 or \
                       first_order['currentOrder']['orderStatusData'].get("isSorManagedOrder") ==1
        isSorChild = first_order['currentOrder']['orderInstructionData'].get("isSorChildOrder") == 1 or \
                     first_order['currentOrder']['orderStatusData'].get("isSorChildOrder") == 1

        isAlgoManaged = first_order['currentOrder']['orderInstructionData'].get("isAlgoManagedOrder") == 1

        sor_parent =  isSorManaged  and isRootOrder
        sor_child = isSorChild
        direct_order = isLeafOrder  and not sor_child
        qty = first_order['currentOrder']['orderInstructionData']['quantity']
        remainQty = first_order['currentOrder']['orderStatusData'].get('quantityRemaining')
        price = first_order['currentOrder']['orderInstructionData'].get("limitPrice")
        symbol = first_order['currentOrder']['orderInstructionData'].get('productId')
        cross = first_order['currentOrder']['orderInstructionData'].get("crossMatchingId")
        #import pdb;pdb.set_trace()
        mxq = first_order['currentOrder']['orderInstructionData'].get("minExecutableQuantity")

        if direct_order:
            inst = first_order['currentOrder']['orderInstructionData']
            venue = inst.get("subExecutionPointOverride") or inst.get('executionPointOverride')
            ordType = inst['orderType']
            tif = inst.get('timeInForce')
            hist = _extract_order_hist(res_one)
            ## enrich execution
            for o in hist:
                if len(o) == 3 and o[2].endswith("E"):
                    o[2] = {o[2]: extract_fill_data(o[2])}

            ret = {'orderId': orderId,
                    'hist': hist,
                    'venue': venue,
                    'tif': tif,
                    'qty': qty,
                    'price': price,
                    'side': side,
                }
            if remainQty and qty != remainQty: ret['qtyRemain'] = remainQty
            if mxq: ret['mxq'] = mxq
            if cross: ret['matchId'] = cross

            return ret

        if sor_parent or isAlgoManaged or isSorManaged:
            parent =  _extract_order_hist(res_one)
            for o in parent:
                if len(o) == 3:
                    if o[2].endswith("O"):
                        o[2] = {o[2]: imagelive_graph(o[2],**kw)}

            ret =  {
                    'orderId': orderId,
                    'hist': parent,
                    'ticker': symbol,
                    'qty': qty,
                    'price': price,
                    'side': side,
                    }
            if sor_parent: ret['sor_parent'] = True
            if isAlgoManaged: ret['algoManaged'] = True
            if isSorManaged: ret['sorManaged'] = True
            if remainQty and qty != remainQty:
                ret['qtyRemain'] = remainQty
            if mxq: ret['mxq'] = mxq

            return ret
        if sor_child:
            ## find parent, and list parent
            #import pdb;pdb.set_trace()
            inst = first_order['currentOrder']['orderInstructionData']
            venue = inst.get("subExecutionPointOverride") or inst['executionPointOverride']
            ordType = inst['orderType']
            tif = inst['timeInForce']
            extRef = first_order['currentOrder']['orderStatusData'].get("externalReferences")

            ret = {'orderId': orderId,
                    'hist': _extract_order_hist(res_one),
                    'venue': venue,
                    'tif': tif,
                    'qty': qty,
                    'price': price,
                    'sor_child': True,
                    }
            if remainQty and qty != remainQty:
                ret['qtyRemain'] = remainQty
            if mxq: ret['mxq'] = mxq
            if extRef: ret['extRef'] = extRef

            return ret

def query_sor_child_dark_with_mxq(**kw):
    """
    scan sor child with mxq for dark venue.

    """
    days = kw.get("day",0)
    days = datetime.now () - timedelta(days=int(day))

    date = days.strftime("%Y%m%d")

    res = imagelive_db.find({'date':date,
                             '$or': [{'msg.currentOrder.orderInstructionData.isSorChildOrder':1},
                                                 {'msg.currentOrder.orderStatusData.isSorChildOrder': 1}],
                             'msg.currentOrder.orderInstructionData.subExecutionPointOverride': {'$in': ['ASXC','CXAD','SIX']},
                            }
                             )

    print res.count()
    out = {}
    for r in res:
        inst = r['msg']['currentOrder']['orderInstructionData']
        out [inst['orderId']] = {inst.get("subExecutionPointOverride"): inst.get('minExecutableQuantity')}

    return out

if __name__ == "__main__":
    """ """

    doc = """Usage:
        queryImagelive.py [options] order <orderId>
        queryImagelive.py [options] graph <orderId>
        queryImagelive.py [options] test
        queryImagelive.py [options] sorDark


        options:
        -d D, --day D   specify day [default: 0] i.e. todya, 1 for previous day, etc.

    """

    results = docopt(doc,version="0.0.1",options_first=False)
    #print results
    day = int(results.get("--day"))

    if results['order']:
        orderId= results['<orderId>']
        res = imagelive_lookup(day,orderId=orderId)
        for r in res:
            pprint(r)
    if results['graph']:
        orderId= results['<orderId>']

        pprint(imagelive_graph(orderId,day=day))


    if results['test']:
        """ regression all order graph."""
        res = imagelive_lookup(day)

        processed = []
        for o in res:
            orderId=o['recordId']
            if orderId not in processed:
                if orderId.endswith("O"):
                    processed.append(orderId)
                    if not isSorChildOrder(orderId):
                        print "------- %s ------" % orderId
                        pprint(imagelive_graph(orderId,day=day))
    if results['sorDark']:

        res = query_sor_child_dark_with_mxq()
        pprint(res)

