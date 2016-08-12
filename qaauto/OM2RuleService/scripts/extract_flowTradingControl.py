""" helper module to extract rds data based on on disk snapshot files



 Column_name      Type      Length     Prec     Scale     Nulls     
 ---------------  --------  ---------  -------  --------  --------  
 LimitKey         varchar      200     NULL      NULL         0     
 LimitSubKey      float          8     NULL      NULL         1     
 LimitSubKeyStr   varchar      200     NULL      NULL         1     
 LimitVal         float          8     NULL      NULL         1     
 LimitStr         varchar      400     NULL      NULL         1     
 UpdateTimestamp  datetime       8     NULL      NULL         1     
 IsActive         bit            1     NULL      NULL         0     
"""
import os
import logging

from treelib import Node,Tree,NodeIDAbsentError

## setup local project 
import cfg
from conf import settings

log = logging.getLogger("extract_flowTradingControl")

__all__ = [ 'parsing_controls','priceStep_rules']

####################
## public methods
def parsing_controls(root):
    """ parsing rds line items and return control items.

    input: rds snapshot folder.

    output:
        sizeLimits in dict. key: symbol, value: sizeLimit.
        default size_limit key: notional-local.SYDE, notional-local.CHIA

        priceControl in tree.
    """

    tree_price_aggressive = Tree()
    size_limits = {}

    ## iter each line of rds record. sequence matter here for update records.
    #for item in gen_price_ctrol_data(root):
    for item in gen_ctrol_data(root):

        assert isinstance(item,dict)

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

def priceStep_rules(price_aggr_tree,rule_tag,**kw):
    """
    """
    exch = kw.get("exch","SYDE")
    symbol = kw.get("symbol","default-product")
    businessUnit = kw.get("businessUnit","DEFAULT")
    assert businessUnit
    if "auction" in rule_tag:
        return priceStep_auction_rules(price_aggr_tree,rule_tag,exch,symbol,businessUnit)
    else:
        return priceStep_open_rules(price_aggr_tree,rule_tag,exch,symbol,businessUnit)

def priceStep_open_rules(price_aggr_tree,rule_tag, exch,symbol,businessUnit):
    """
    from price_aggr_tree data  extract: rules (i.e. price step and per last) based on rule_tag.

    rule_tag lookup priceStep rule and perLast rule:
        i.e. 'exchange-continuous-limit', 'exchange-continuous-market','exchange-continuous-pegged'
        or  'exchange-open-auction-limit', 'exchange-open-auction-market', 'exchange-open-auction-pegged'
        or  'exchange-close-auction-limit', 'exchange-close-auction-market', 'exchange-close-auction-pegged'


    1) based on rule_tag search for lookup_node

    2) based on lookup_node's value search rule block: i.e. 'eq1d-au-price-step', 'eq1d-au-segment-auction' or 'eq1d-au-segment-auction-product'.

    3) if symbol specified, lookup symbol specified rule.

    4) new: businessUnit lookup key on priceStep

    return rule data: price step  and/or per last.
    """
    log.debug("priceStep_open_rules: rule_tag: %s, exch: %s, symbol: %s, businessUnit: %s" %(rule_tag,exch,symbol,businessUnit))
    #import pdb;pdb.set_trace()
    root = "asia.stock.price-aggressive"
    ## based on rule_tag workout phase tag
    assert "continuous" in rule_tag
    phase = "continuous"
    #import pdb;pdb.set_trace()
    if symbol != "default-product":
        ## if symbol specified, try lookup symobl specified
        lookup_nid = ".".join([root,rule_tag,exch,symbol])
        log.debug("lookup_nid: %s" % lookup_nid)
        lookup_node = price_aggr_tree.get_node(lookup_nid)
        ## fallback to default
        if not lookup_node :
            lookup_nid = ".".join([root,rule_tag,exch,"default-product"])
            log.debug("lookup_nid default-product: %s" % lookup_nid)
            lookup_node = price_aggr_tree.get_node(lookup_nid)
    else:
        ## using default-product
        lookup_nid = ".".join([root,rule_tag,exch,symbol])
        log.debug("lookup_nid default-product: %s" % lookup_nid)
        lookup_node = price_aggr_tree.get_node(lookup_nid)

    log.debug("node data: %s" % lookup_node.data)
    assert len(lookup_node.data) == 1
    #print lookup_node.identifier,lookup_node.data
    rule_nid = lookup_node.data[0]["LimitValueStr"]

    ## rule lookup path
    rule_path =  ".".join([root,rule_nid,businessUnit])
    log.debug("rule_path: %s" % rule_path)
    try:
        rule_tree = price_aggr_tree.subtree(rule_path)
        log.debug("rule_tree: %s" % rule_tree)
    except NodeIDAbsentError:
        msg = "not rule found for: %s" % rule_path
        log.info(msg)
        raise ValueError(msg)

    ## workout price step data
    last_price_node_path = ".".join([rule_path,"last-price-step-limit",phase])
    log.debug("last_price_node_path: %s" % last_price_node_path)
    last_price_node = price_aggr_tree.get_node(last_price_node_path)
    assert last_price_node

    overlap_price_node_path = ".".join([rule_path,"overlap-price-step-limit",phase])
    log.debug("overlap_price_node_path: %s" % overlap_price_node_path)
    overlap_price_node = price_aggr_tree.get_node(overlap_price_node_path)
    assert overlap_price_node

    price_step_node_path = ".".join([rule_path,"price-step-limit",phase])
    log.debug("price_step_node_path: %s" % price_step_node_path)
    price_step_node = price_aggr_tree.get_node(price_step_node_path)
    assert price_step_node

    def get_node_data(node):
        """ helper for locate leaf node's data, and extract price band."""
        assert node
        data = sorted(node.data, key=lambda k:k['LimitSubKey'],reverse=True)
        ## extract price band
        return [(d['LimitSubKey'],d['LimitValue']) for d in data]

    last_price_step_data = get_node_data(last_price_node)
    price_step_data = get_node_data(price_step_node)
    overlap_price_data = get_node_data(overlap_price_node)

    return {
            'price_step': price_step_data,
            'price_last': last_price_step_data,
            'price_overlap': overlap_price_data,
            'identifier': (rule_tag,rule_path),
            }

def priceStep_auction_rules(price_aggr_tree,rule_tag,exch,symbol,businessUnit):
    """
    from price_aggr_tree data  extract: rules (i.e. price step and per last) based on rule_tag.

    rule_tag lookup priceStep rule and perLast rule:
        i.e. 'exchange-continuous-limit', 'exchange-continuous-market','exchange-continuous-pegged'
        or  'exchange-open-auction-limit', 'exchange-open-auction-market', 'exchange-open-auction-pegged'
        or  'exchange-close-auction-limit', 'exchange-close-auction-market', 'exchange-close-auction-pegged'


    1) based on rule_tag search for lookup_node

    2) based on lookup_node's value search rule block: i.e. 'eq1d-au-price-step', 'eq1d-au-segment-auction' or 'eq1d-au-segment-auction-product'.

    3) if symbol specified, lookup symbol specified rule.

    4) new: businessUnit lookup key on priceStep

    return rule data: price step  and/or per last.
    """
    log.info("priceStep_auction_rules: tag:%s, exch:%s, symbol:%s, bu:%s" %(rule_tag,exch,symbol,businessUnit))
    #import pdb;pdb.set_trace()
    root = "asia.stock.price-aggressive"
    ## based on rule_tag workout phase tag
    assert "auction" in rule_tag
    #import pdb;pdb.set_trace()
    if symbol != "default-product":
        ## if symbol specified, try lookup symobl specified
        lookup_nid = ".".join([root,rule_tag,exch,symbol])
        lookup_node = price_aggr_tree.get_node(lookup_nid)
        ## fallback to default
        if not lookup_node :
            lookup_nid = ".".join([root,rule_tag,exch,"default-product"])
            lookup_node = price_aggr_tree.get_node(lookup_nid)
    else:
        ## using default-product
        lookup_nid = ".".join([root,rule_tag,exch,symbol])
        lookup_node = price_aggr_tree.get_node(lookup_nid)
    log.info("lookup nid: %s" %lookup_nid)
    ### 
    assert len(lookup_node.data) == 1
    rule_nid = lookup_node.data[0]["LimitValueStr"]
    log.info("rule nid: %s" % rule_nid)

    #import pdb;pdb.set_trace()
    ## rule lookup path
    rule_path = ".".join([root,rule_nid,businessUnit])
    log.info("rule path:%s" % rule_path)
    try:
        rule_tree = price_aggr_tree.subtree(rule_path)
    except NodeIDAbsentError:
        raise ValueError("not rule found for: %s" % rule_path)

    ## workout price step data
    last_price_node_path = ".".join([rule_path,"last-price-step-limit","auction"])
    log.debug("last_price_node_path: %s" % last_price_node_path)
    last_price_node = price_aggr_tree.get_node(last_price_node_path)
    assert last_price_node

    overlap_price_node_path = ".".join([rule_path,"overlap-price-step-limit","auction"])
    log.debug("overlap_price_node_path: %s" % overlap_price_node_path)
    overlap_price_node = price_aggr_tree.get_node(overlap_price_node_path)
    assert overlap_price_node

    price_step_node_path = ".".join([root,rule_nid,"price-step-limit","auction"])
    log.debug("price_step_node_path: %s" % price_step_node_path)
    price_step_node = price_aggr_tree.get_node(price_step_node_path)
    assert price_step_node

    def get_node_data(node):
        """ helper for locate leaf node's data, and extract price band."""
        assert node
        data = sorted(node.data, key=lambda k:k['LimitSubKey'],reverse=True)
        ## extract price band
        return [(d['LimitSubKey'],d['LimitValue']) for d in data]

    last_price_step_data = get_node_data(last_price_node)
    price_step_data = get_node_data(price_step_node)
    overlap_price_data = get_node_data(overlap_price_node)

    ##default auction phase i.e. close.
    auction_phase = "exchange-close-auction-limit"
    if "open" in rule_tag:
        auction_phase = "exchange-open-auction-limit"
    ## using default segment-auction
    per_last_nid = None
    if symbol == "default-product" or symbol != "default-product" and rule_nid == "eq1d-au-segment-auction":
        assert rule_nid == "eq1d-au-segment-auction"
        per_last_nid = ".".join([root,rule_nid,"aggressive-band-last",exch,auction_phase,businessUnit])
        log.debug ("per last nid: %s" % per_last_nid)
        per_last_node = price_aggr_tree.get_node(per_last_nid)

    ## using segment-auction-product for specific product.
    elif symbol != "default-product":
        assert rule_nid == "eq1d-au-segment-auction-product"
        per_last_nid = ".".join([root,rule_nid,"aggressive-last",symbol,auction_phase,businessUnit])
        log.debug("per last product  nid: %s" % per_last_nid)
        per_last_node = price_aggr_tree.get_node(per_last_nid)
    else:
        raise ValueError("unexpected rule: %s, symbol: %s" % (rule_nid,symbol))

    ## bad configuration 
    assert per_last_node, "lookup_nid: %s active , per_last_nid: %s not found ?!" % (lookup_nid,per_last_nid)

    per_last_data = get_node_data(per_last_node)

    log.info("per_last_data: %s" % per_last_data)
    ## auction
    return {
            'price_step': price_step_data,
            'price_last': last_price_step_data,
            'price_overlap': overlap_price_data,
            'per_last': per_last_data,
            'identifier': (rule_tag,rule_path,per_last_nid)
            }

##########################################
#### internal helper functions
def parse_rds_line(line):
    """
    Insert df FlowTradingControlLimit [ tradingControlLimitKey String "asia.stock.size.eq1d-size-notional-product.notional-local.NAE.CHA" ] [ tradingControlLimitSubkey Double "0" ] [ tradingControlLimitValue Double "1500000" ] [ tradingControlLimitValueStr String "" ] [ itemUpdate collection [ 0 ItemUpdate  ]  ]


    Update df FlowTradingControlLimit [ tradingControlLimitKey String "asia.stock.price-aggressive.exchange-close-auction-limit.SYDE.OFX.AX" ] [ tradingControlLimitSubkey Double "0" ] [ tradingControlLimitValue Double "0" ] [ tradingControlLimitValueStr String "eq1d-au-segment-auction-product" ] [ itemUpdate collection [ 0 ItemUpdate [ updateTimestamp DateTime "02/08/16 09:58:19.210" ] [ sequenceNum Long "14" ] [ updateType Int "1" ]  ]  ]
    """

    start = 0
    complete = False
    items = []

    ret = {'action': "Insert"}
    if line.startswith("Update"):
        ret['action'] = "Update"
    elif line.startswith("Delete"):
        ret['action'] = "Delete"

    while not complete:
        idx_l = line.find("[",start)
        if idx_l == -1:
            complete = True
        else:
            idx_r = line.find("]",idx_l)
            assert idx_r != -1
            start = idx_r +1
            if 'itemUpdate' not in line[idx_l:idx_r+1]:
                items.append(line[idx_l+1:idx_r].strip())


    for item in items:
        k,t,v = item.split()
        v = v.replace('"','')
        if k.endswith("LimitKey"):
            assert t == "String"
            ret['LimitKey'] = v
        elif k.endswith("LimitSubkey"):
            assert t == "Double"
            ret["LimitSubKey"] = float(v)
        elif k.endswith("LimitSubkeyStr"):
            assert t == "String"
            ret["LimitSubKeyStr"] = v
        elif k.endswith("LimitValue"):
            assert t == "Double"
            ret["LimitValue"] = float(v)
        elif k.endswith("LimitValueStr"):
            assert t == "String"
            ret["LimitValueStr"] = v
        elif k == "sequenceNum":
            assert t == "Long"
        elif k == "updateType":
            assert t == "Int"
        else:
            raise ValueError ("unexpected key value: %s" % item)

    #import pdb;pdb.set_trace()
    return ret

def dump_price_control_items(root):
    """ helper dump rds control for only price control line to file.
        also sorted by key.
    """
    def filter_price(ln):
        item = parse_rds_line(ln)
        if item['LimitKey'].split(".")[2] == "size":
            return False
        return True
    ret = [d for d in gen_rds_control_snapshot(root,filter_price)]
    def parse_key(ln):
        item = parse_rds_line(ln)
        return item['LimitKey']

    for ln in sorted(ret,key=parse_key):
        print ln

def dump_size_limit_items(root):
    """ helper dump rds control for sizeLimit line to file."""
    def filter_price(ln):
        item = parse_rds_line(ln)
        if item['LimitKey'].split(".")[2] == "size":
            return True
        return False

    ret = [d for d in gen_rds_control_snapshot(root,filter_price)]
    def parse_key(ln):
        item = parse_rds_line(ln)
        return item['LimitKey']

    for ln in sorted(ret,key=parse_key):
        print ln

def gen_price_ctrol_data(root):
    """ return price control data item."""
    for ln in gen_rds_control_snapshot(root):
        item = parse_rds_line(ln)
        if item['LimitKey'].split(".")[2] != "size":
            yield item

def gen_ctrol_data(root):
    """ """
    for ln in gen_rds_control_snapshot(root):
        item = parse_rds_line(ln)
        yield item

def gen_rds_control_snapshot(root,filter=None):
    """ lookup rds control property from snapshot."""
    files = os.listdir(root)
    for file in files:
        if file.startswith("RdsFlowTradingControlLimit"):
            rdsAccounts = []
            with open(os.path.join(root,file),"r") as f:
                for ln in f:
                    ln = ln.strip()
                    if ln == "": continue
                    ## collect all control data.
                    if filter:
                        if filter(ln):
                            yield ln
                        else:
                            continue
                    else:
                        yield ln


#####################################################
## extract TradingControls out of sybase
import copy
import pprint
import sys
sys.path.insert(0,"/gns/mw/lang/python/modules/2.7.2/sybase-0.39/lib/python2.7/site-packages")
import Sybase

def gen_db_priceControl_item():
    """ generator for db item."""
    APEQTQ01 = {
        'server': 'APEQTQ01',
        'user': 'rds_ro',
        'pwd': 'rds_ro',
        'database': 'TradingControls',
    }

    conn_  = Sybase.connect(APEQTQ01['server'],
                            APEQTQ01['user'],
                            APEQTQ01['pwd'],
                            APEQTQ01['database']
            )
    cur = conn_.cursor()
    sql = """ select LimitKey,LimitSubKey,LimitSubKeyStr,LimitVal,LimitStr
              from FlowSpecificTradingControls
              where IsActive = 1
              and LimitKey like 'asia.stock.price-aggressive%'
              order by LimitSubKey
        """

    try:
        cur.execute(sql)
        for r in cur.fetchall():
            log.debug("row: %s" % str(r))

            item = {
                    "LimitKey":r[0],
                    "LimitSubKey":r[1],
                    "LimitSubKeyStr": r[2],
                    "LimitVal":r[3],
                    "LimitStr": r[4],
                    }

            if item['LimitSubKey'] == None: item.pop('LimitSubKey')
            if item['LimitSubKeyStr'] == None: item.pop('LimitSubKeyStr')
            if item['LimitStr'] == None: item.pop("LimitStr")

            yield item
    finally:
        cur.close()

def get_db_sizeLimits_item(force=False):
    """ get for db sizeLimit in batch."""

    if not force and hasattr(get_db_sizeLimits_item,"cache"):
        return get_db_sizeLimits_item.cache

    APEQTQ01 = {
        'server': 'APEQTQ01',
        'user': 'rds_ro',
        'pwd': 'rds_ro',
        'database': 'TradingControls',
    }

    conn_  = Sybase.connect(APEQTQ01['server'],
                            APEQTQ01['user'],
                            APEQTQ01['pwd'],
                            APEQTQ01['database']
            )
    cur = conn_.cursor()
    sql = """ select LimitKey,LimitSubKey,LimitSubKeyStr,LimitVal,LimitStr
              from FlowSpecificTradingControls
              where IsActive = 1
              and LimitKey like 'asia.stock.size.eq1d-size-notional-product.notional-local%'
              order by LimitKey
        """
    ret = {}
    try:
        cur.execute(sql)
        for r in cur.fetchall():

            item = {
                    "LimitKey":r[0],
                    "LimitVal":r[3],
                    }

            keys = r[0].split(".")

            ret[".".join(keys[5:])] = r[3]

    finally:
        cur.close()

    ## cache locally
    get_db_sizeLimits_item.cache = ret

    return ret

############################
## 

def load_rule_tree(**kw):
    """ load rule tree from local rdsdata folder or sybase snapshot


    """
    folder = kw.get("folder",None)

    if folder:
        folder = os.path.join(setings.RDSDATA,folder)
        ## 
        data = parsing_controls(folder)
        tree = data['price'].subtree("asia.stock.price-aggressive")
        ignore_tags =['JPNX','TKYO','HKGE','GEM','CHIJ','CXAD','XSSC','SIX']
        ## 
        tree.dump_tree("price-tree-%s.out" % snapshots[-1],ignore_tags=ignore_tags)
        tree.dump_tree("price-tree-data-%s.out" % snapshots[-1],with_data=True,ignore_tags=ignore_tags)
        return tree
    else:
        ## LOAD FORM SYBASE
        tree = Tree()
        count = 0
        for item in gen_db_priceControl_item():
            #print item
            keys = item.pop("LimitKey").split(".")
            ## patch symbol
            if keys[-1] in ("AX","CHA"):
                keys = keys[:-2] + [keys[-2] + "." + keys[-1]]

            #print keys, item
            ## patch sybase to snapshot
            limitVal = item.pop("LimitVal")
            item['LimitValue'] = limitVal
            if "LimitStr" in item:
                limitStr = item.pop("LimitStr")
                item['LimitValueStr'] = limitStr.strip()

            tree.add_node_from_list(keys,item)
            count +=1
        ignore_tags =['JPNX','TKYO','HKGE','GEM','CHIJ','CXAD','XSSC','SIX']
        print "total: %s" % count
        ptree =tree.subtree("asia.stock.price-aggressive")
        ptree.dump_tree("test-sybase.out",ignore_tags=ignore_tags)
        ptree.dump_tree("test-sybase-data.out",with_data=True,ignore_tags=ignore_tags)

        return tree

def find_rule_priceStep(tree,price,**kw):
    """ entry point for find priceStep rules.

    assume price in dollar.
    """
    rule_tag = kw.get("rule_tag","exchange-continuous-limit")
    ## default
    exch = kw.get("exchange","SYDE")
    symbol = kw.get("symbol","default-product")
    businessUnit = kw.get("businessUnit","DEFAULT")
    # import pdb;pdb.set_trace()
    ## lookup rule
    rules = priceStep_rules(tree,rule_tag,exch=exch,symbol=symbol,businessUnit=businessUnit)

    assert 'price_step' in rules and 'price_last'in rules and 'price_overlap' in rules
    assert len(rules['price_step']) == len(rules['price_last']) == len(rules['price_overlap'])

    if 'auciton' in rule_tag:
        assert 'per_last' in rules

    ret = {}

    for idx, rule in enumerate(rules['price_step']):
        if price > rule[0]:
            log.info("found price step rule for price %f, : %s " % (price,str(rule)))
            ret['price_step'] =  rules['price_step'][idx][1]
            ret['price_last'] = rules['price_last'][idx][1]
            ret['price_overlap'] =  rules['price_overlap'][idx][1]
            ret['trace_price_step_band'] = rules['price_step'][idx][0]
            ret['trace_price_step'] = (idx,rules)
            break
    ## workaround 0.001 price
    if price > 0 and price <= 0.001:
        assert ret == {}
        ret['price_step'] =  rules['price_step'][-1][1]
        ret['price_last'] =  rules['price_last'][-1][1]
        ret['price_overlap'] =  rules['price_overlap'][-1][1]
        ret['trace_price_step_band'] =  rules['price_step'][idx][0]
        ret['trace_price_step'] =  (-1, rules)

    if 'per_last' in rules:

        for idx,rule in enumerate(rules['per_last']):
            if price > rule[0]:
                ret['per_last'] = rules['per_last'][idx][1]
                ret['trace_per_last_band'] = rules['per_last'][idx][0]
                ret['trace_per_last'] = (idx,rules['per_last'])
                break
        if 'per_last' not in ret:
            ret['per_last'] = rules['per_last'][-1][1]
            ret['trace_per_last_band'] = rules['per_last'][-1][0]
            ret['trace_per_last'] = (-1, rules)

    ## found rule
    assert 'trace_price_step_band' in ret
    if 'auction' in rule_tag: assert 'trace_per_last_band' in ret

    return ret


def find_priceStep(price,rule_tag, **kw):
    """ """

    folder = kw.get("snapshot",None)

    if not hasattr(find_priceStep,'tree'):
        tree = load_rule_tree(folder=folder)
        find_priceStep.tree = tree
    else:
        tree = find_priceStep.tree
    return find_rule_priceStep(tree,price,rule_tag=rule_tag,**kw)

if __name__ == "__main__":
    """ """
    import logging
    logging.basicConfig(filename="extract_flowTradingControl.debug",level=logging.DEBUG)

    #load_rule_tree()
    #dump_size_limit_items("Snapshot_160222_06_45_22")
    #data = parsing_controls("Snapshot_160222_06_45_22")
    #size = data['size']

    #assert "DMA.CSL.AX" in size
    #assert "PT.CSL.AX" in size
    #assert "DEFAULT.CSL.CHA" in size
    #assert "ALGO_DEFAULT.CSL.CHA" in size
    #size = get_db_sizeLimits_item()
    #import pdb;pdb.set_trace()

    print "open"
    print find_priceStep(43.24,"exchange-continuous-limit",businessUnit="OPERATOR")
    print "open-auction"
    print find_priceStep(43.24,"exchange-open-auction-limit",businessUnit="OPERATOR")
    print "close-auction"
    print find_priceStep(43.24,"exchange-close-auction-limit",businessUnit="OPERATOR")

