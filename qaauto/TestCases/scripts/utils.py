"""
"""
import logging
from datetime import datetime,timedelta
from om2CompleteCatalog import om2CompleteCatalog, om2CompleteCatalogEnums

log = logging.getLogger(__name__)

def enum_lookup(label,idx):
    """
        from index to enum label
        -- used by parse ivcom message
    """
    om2Enums = om2CompleteCatalogEnums['enums']

    values = om2Enums[label]['values']
    for k in values:
        if values[k] == idx:
            return k
def lookup_enum(label,name):
    """
        from name to enum index
            - ignore case lookup
    """
    om2Enums = om2CompleteCatalogEnums['enums']

    ## try default
    if label in om2Enums:
        values = om2Enums[label]['values']
        for k in values:
            if k.lower() == name.lower():
                return values[k]
    ## try add Om2 prefix
    if "Om" + label in om2Enums:
        values = om2Enums["Om"+label]['values']
        for k in values:
            if k.lower() == name.lower():
                return values[k]

    raise ValueError("failed enum lookup:%s,%s" % (label,name))
def enrich_enum(tableName,msg):
    """ for each table item each rich enum field.  """

    #log.debug("enrich enum tableName: %s, msg: %s" % (tableName,msg))
    if tableName in om2CompleteCatalog['tables']:
        table = om2CompleteCatalog['tables'][tableName]
        for k,v in table['columns'].items():
            meta = v.get('meta-fields') or [{'value': None}] ##or fake meta for rds catalog
            if k in msg:
                if v['type'] == 'table':
                    #assert type(msg[k]) == list
                    ## trea table as dict
                    if  meta[-1]['value'] == 'struct':
                        #msg[k] = msg[k][0]
                        #log.info("key: %s, meta: %s, msg: %s" % (k,meta, msg))
                        ## recursive here
                        if type(msg[k]) == dict:
                            enrich_enum(v['tablename'],msg[k])
                        elif type(msg[k]) == list:
                            ## om2 bug in catalog
                            for m in msg[k]:
                                enrich_enum(v['tablename'],m)
                        else:
                            assert False,"unexpect type: key: %s, meta: %, msg: %s" % (k,meta,msg[k])
                    else:
                        assert type(msg[k]) == list
                        ## treat table as list
                        for m in msg[k]:
                            enrich_enum(v['tablename'],m)
                ## handle enum enrichment
                if v['type'] == 'ubyte' and 'enum' in v:
                    msg[k] = enum_lookup(v['enum'],msg[k])
class IvComDictHelper():
    """
        create IvComJson message based on
        - catalog
        - enums
        - table specified
    """
    def __init__(self,tblName,catalog=om2CompleteCatalog,enums=om2CompleteCatalogEnums):
        """
        """
        self.tbl = tblName
        self.tblscheme = catalog['tables'][tblName]
        self.enums = enums['enums']
        self.msg = {}


    def set(self,colName,value):
        """
        """
        assert colName in self.tblscheme['columns'].keys(), "colName unknown: %s,%s for tbl: %s" % (colName,value,self.tbl)
        colscheme = self.tblscheme['columns'][colName]

        if colscheme['type'] == 'table':
            ## set single table value
            if type(value) == dict:
                ## further validate/convert value to IvCom/dict
                ivValue = IvComDictHelper(colscheme['tablename'])
                for k,v in value.iteritems():
                    ivValue.set(k,v)
                log.debug("enrich subtable: %s, %s" % (colName,ivValue.msg))
                if colscheme['meta-fields'][-1]['value'] == 'collection':
                    self.msg[colName] = [ivValue.msg]
                else:
                    self.msg[colName] = ivValue.msg
                ## set list of values
            elif type(value) == list and colscheme['meta-fields'][-1]['value'] == 'collection':
                ##  further validate/convert value to IvCom/dict
                    ivVals = []
                    for val in value:
                        ivVal = IvComDictHelper(colscheme['tablename'])
                        for k,v in val.iteritems():
                            ivVal.set(k,v)
                        ivVals.append(ivVal.msg)
                    log.debug("enrich subtable: %s, %s" % (colName,ivVals))
                    self.msg[colName] = ivVals
            ## error
            else:
                raise ValueError("unknown input:%s for col %s" % (value,colName))

        elif colscheme['type'] == 'ubyte' and colscheme['enum']:
            if type(value) == int:
                self.msg[colName] = value
            else:
                ## convert string to int
                value_enum = lookup_enum(colscheme['enum'],value)
                self.msg[colName] = value_enum
        elif colscheme['type'] =='int':
            self.msg[colName] = int(value)
        elif colscheme['type'] =='double':
            self.msg[colName] = float(value)
        elif colscheme['type'] =='string':
            self.msg[colName] = str(value)
        elif colscheme['type'] == 'bool':
            assert value in (True,False), "colName:%s expect(True/False): %s,%s for tbl: %s" % (colName,value,self.tbl)
            self.msg[colName] = value
        else:
            self.msg[colName] = value

    def __str__(self):
        """
        """
        return json.dumps(self.msg)

## price helper
from helper import *

def get_passive_price(side,quote,**kw):
    """ return passive price.

    workout passive price based on side, test_instrument.

    input:
        - quote, current quote snapshot
        - side order side



    """

    attrs = kw.get("attrs")

    assert 'bid' in quote and 'ask' in quote and 'last' in quote

    bid,ask,last = quote['bid']['bid'],quote['ask']['ask'],quote['last']

    ## enrich last if missing
    if attrs and "CLOSEPRICE" in attrs:
        last = last or float(attrs['CLOSEPRICE'])

    ## check price not breach priceStep
    if side == "Buy":
        ## there is an ask price and adjuse last less aggressive
        if ask and ask < last:
            last = ask
        # bid isn't too far from last
        if bid > 0 and bid < last  and last/bid-1 < 0.05 :
            price = bid
        else:
            price = last - tickSize(last,5)
            if price <= 0: price = 0.001

    else: ## side == Sell

        ## there is a bid price, and adjust last less aggressive
        if bid and bid > last:
            last = bid
        ## sell side here check last/ask
        if last == 0:
            price = ask
            # ask isn't too far from last 10% 
        elif ask > 0 and  ask > last and ask/last -1 < 0.1:
            price = ask
        else:
            price = last + tickSize(last,10)

    ##remove off-tick price if any
    return round_price(price,side=side)


from conf import settings
class PegType:

    """peg type enum."""

    MID = 1
    MARKET = 2
    BEST = 3

def getPegOrderType(sor,side,pegType=PegType.MID):
    """  return peg order type.    """
    assert sor in ('asx','chia')

    tags = settings.ORDER_TYPES[sor].copy()
    tags['orderType'] = 'Pegged'

    if pegType == PegType.MID:
        tags['pegType'] = 'Mid'
        return tags

    if side == "Buy":
        if pegType == PegType.BEST:
            tags['pegType'] = 'Bid'
        if pegType == PegType.MARKET:
            tags['pegType'] = 'Ask'
    else:
        if pegType == PegType.BEST:
            tags['pegType'] = 'Ask'
        if pegType == PegType.MARKET:
            tags['pegType'] = 'Bid'

    assert 'pegType' in tags, "unknown pegType: %s" % pegType

    return tags

class AckFailed(Exception):
    pass

def valid_rf_ack(ack):
    """validate ack from RPC call. return tuple (orderId,eventId). """

    if isinstance(ack,dict):
        orderId = None
        eventId = None
        if ack and 'wasCommandSuccessful' in ack and ack['wasCommandSuccessful'] == True:
            eventId = ack['eventIdWrapper']['eventId']
            orderId = ack.get('orderId')
        else:
            print "ack failed %s" % ack
            raise AckFailed(ack)

        return (orderId,eventId)
    else:
        assert isinstance(ack,bool)
        assert ack == True

        return ack

## common FIX time in force
DAY = 1
GTC = 3
GTD = 6
IOC = FAK = 4
FOK = 4

"""
'version': 5,
'values': {
    'INVALID': 0,
    'Day': 1,
    'GoodTillDate': 2,
    'GoodTillCancelled': 3,
    'ImmediateOrCancel': 4,
    'ValidUntilNextAuction': 5,
    'Open': 6,
    'Close': 7,
    'Auction': 8,
    'Extended': 9,
    'SessionOrClose': 10,
    'BlockCrossingSession': 11,
    'GoodInTradingSession': 12,
    'GoodTillTime': 13,
    'Core': 14,
    'GoodForMilliseconds': 15,
    'GoodForScheduledAuction': 16,

"""
import collections
## convert all unicode to string, ivcom don't like unicod
def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


import socket
def porttry(ip,port,timeout=0.5):
    """ """
    scan_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #socket.AF_INET, socket.SOCK_STREAM
    socket.setdefaulttimeout(timeout)
    try:
        scan_socket.connect((ip,port))
        scan_socket.close()
        return True
    except :
        return False

import os
from datetime import date
import mmap
import ctypes

class SeqNumber():
    """ quick/dirty sequence generator."""

    def __init__(self,root_dir,name):
        """ """
        fn = os.path.join(root_dir,\
                '%s_%s.mmap' %(name,date.today().isoformat()))
        if os.path.exists(fn):
            fd = os.open(fn,os.O_RDWR)
        else:
            fd = os.open(fn,os.O_CREAT|os.O_TRUNC|os.O_RDWR)
            assert os.write(fd,'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE

        self.buf_ = mmap.mmap(fd,mmap.PAGESIZE,mmap.MAP_SHARED)

    @property
    def next(self):
        """ return next seq nmber"""
        seq = ctypes.c_int64.from_buffer(self.buf_)

        seq.value +=1

        return seq.value

    def set_next(self,val):
        seq = ctypes.c_int64.from_buffer(self.buf_)
        seq.value = val

import cStringIO
from pprint import pprint
class ERItem(object):

    """ wrapper for DSS message. """

    def __init__(self,msg):
        assert type(msg) == dict
        self.__dict__.update(msg)

    def __getattr__(self,key):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            return None

    def __repr__(self):
        """ internal repr, return as formated string."""
        ret = {}
        for k,v in self.__dict__.items():
            if not k.startswith("__"):
                ret[k] = v
        io = cStringIO.StringIO()
        pprint(ret,stream=io,indent=2)
        out =io.getvalue()
        io.close()
        return out

class ER(object):

    """ parseing DSS into ER. """

    def __init__(self,msg):

        assert type(msg) == dict
        assert 'currentOrder' in msg and 'orderInstructionData' in msg['currentOrder']
        self.order = ERItem(msg['currentOrder']['orderInstructionData'])
        assert 'orderStatusData' in msg['currentOrder']
        self.orderStatus = ERItem(msg['currentOrder']['orderStatusData'])
        assert 'eventData' in msg
        self.eventData = ERItem(msg['eventData'])
        if 'currentExecution' in msg:
            self.execution = ERItem(msg['currentExecution'])
        ## pending
        if 'pendingCorrection' in msg['currentOrder']:
            self.pendingCorrection = ERItem(msg['currentOrder']['pendingCorrection'])
        if 'pendingCancel' in msg['currentOrder']:
            self.pendingCancel = ERItem(msg['currentOrder']['pendingCancel'])
        ## relatedIndex i.e. childOrders
        self.childOrders = None
        if "relatedEntityIndexes" in msg["currentOrder"]:
            """
             u'relatedEntityIndexes': [{u'entityFirstVersion': 2,
             u'entityId': u'PPEAUCEA1025120151207O',
             u'relatedEntityFirstVersion': 1,
             u'relatedEntityId': u'PPEAUCEA1025220151207O',
             u'relatedEntityType': u'ChildOrder'}],
             """
            assert isinstance(msg["currentOrder"]['relatedEntityIndexes'],list)
            childs = []
            for i in msg["currentOrder"]['relatedEntityIndexes']:
                if i["relatedEntityType"] == u'ChildOrder':
                    childs.append(i["relatedEntityId"])
            if childs:
                self.childOrders = childs

        self.eventKeys = []
        if self.eventData.events:
            for event in sorted(self.eventData.events,key=lambda k: k.get('internalEventSequenceNumber',0)):
                if 'internalEventType' in event:
                    self.eventKeys.append(event['internalEventType'])
        else:
            log.warn("message:%s, without events" % (msg))
        ##timestamp on received
        self.timestamp = datetime.now()

    def __repr__(self):
        er ={'order': self.order,
                'status': self.orderStatus,
                'eventData': self.eventData,
                'eventKeys': self.eventKeys,
                'time': self.timestamp,
                'childs': self.childOrders,
                }
        if hasattr(self,'execution'):
            er['fill']  = self.execution
        if hasattr(self,'pendingCorrection'):
            er['pendingCorrection'] = self.pendingCorrection
        if hasattr(self,'pendingCancel'):
            er['pendingCancel'] = self.pendingCancel
        return "%r" % er

    def __str__(self):
        return "%s" % self.__repr__()


def translateOrderType(inst):
    """ translate order type based on om2 order instruction, note: inst is an ERItem.
        - ASX
        - CHIA
        - ASXCP
        - ASXS
        - tradeReport
        - or SOR
    """
    ## sor type
    algoType = inst.tradingAlgorithm
    algoParams = inst.tradingAlgorithmParameters
    minQty = inst.minExecutableQuantity
    minVal = inst.minExecutableNotionalValue

    if inst.destinationParty:
        dest = inst.destinationParty.get("destinationMarketId",'')
    else:
        dest = 'unk'

    if inst.isSorManagedOrder:
        return  _translateAlgoType(algoType,algoParams,minQty,minVal)
    elif dest in ("SYDE","CHIA"):
        ## figure what kid of direct order
        orderType       = inst.orderType
        pegOffsetType   = inst.pegOffsetType
        pegType         = inst.pegType
        routingStrategy = inst.routingStrategy
        crossMatchingId = inst.crossMatchingId
        if routingStrategy:
            return dest+"-ASXS" if not minQty else dest+"-ASXS/MAQ"
        elif crossMatchingId:
            return dest + "-tradeReport"
        elif pegType and pegOffsetType:
            return dest + "-" + pegType + ":" + pegOffsetType if not  minQty else dest + "-" + pegType + ":" + pegOffsetType   + "/MAQ"
        else:
            return dest + "-" + orderType if not minQty else dest + "-"  + orderType + "/MAQ"
    else:
        return dest

########### translate sor 
def _translateAlgoType(algoType,algoParams,minQty,minVal):
    """
       based on : rcsid[] = "$Id: OmRuleActionAUPlutusStrategyConversion.cpp,v 1.8 2014/09/24 17:35:00 vekard Exp $";
    """
    if algoType not in ('SOR_AsiaBasic','SOR_ALGO','CsorAuction'):
        return "??%s,%s" % (algoType,algoParams)

    if algoType == 'CsorAuction':
        return 'CsorAuction'

    try:
        params = dict([i.split("=") for i in algoParams.split(",")])
    except Exception:
        #import pdb;pdb.set_trace()
        #must be atp algo order
        return algoType

    ret_algo_type = params.get('_displayAlgoName')
    if algoType == 'SOR_AsiaBasic':
        ## -- asxonly
        if params['okToSweepExchange']  == 'true' and \
                params['okToPostExchange']   == 'true' and \
                params['okToSweepLit']       == 'false' and \
                params['okToPostLit']        == 'false' and \
                params['okToSweepAltHidden'] == 'false':
                    ret_algo_type =  'ASXOnly'

        ## -- best price
        if params['okToSweepExchange'] == 'true' and \
                params['okToPostExchange']  == 'true' and \
                params['okToSweepLit']      == 'true' and \
                params['okToPostLit']       == 'false' and \
                params['okToSweepAltHidden'] == 'true':
                    if minVal:
                        ret_algo_type = 'BPMV'
                    else:
                        ret_algo_type =  'BP'

        ## -- best price minQty noLit
        if params['okToSweepExchange'] == 'true' and \
                params['okToPostExchange']  == 'true' and \
                params['okToSweepLit']      == 'false' and \
                params['okToPostLit']       == 'false' and \
                params['okToSweepAltHidden'] == 'true' :
                    ret_algo_type =  'BPNoLit'

    if algoType == 'SOR_ALGO':
        if params['okToSweepExchange'] == 'true' and \
                params['okToPostExchange']  == 'true' and \
                params['okToSweepLit']      == 'true' and \
                params['okToPostLit']       == 'false' and \
                params['okToSweepAltHidden'] == 'true' :
                    ret_algo_type =  'BPUni'


        if params['okToSweepExchange'] == 'true' and \
                params['okToPostExchange']  == 'true' and \
                params['okToSweepLit']      == 'false' and \
                params['okToPostLit']       == 'false' and \
                params['okToSweepAltHidden'] == 'true' :
                    ret_algo_type =  'BPNoLitUni'

    if minQty:
        ret_algo_type += "MAQ"

    return ret_algo_type

class DepthStyle:

    """ depth style. """

    ASXONLY = 0
    MIXED = 1
    ASXCHIA = 2  # ASX/Buy, CHIA/Sell
    CHIAASX = 3  # CHIA/Buy, ASX/Sell
    CHIAONLY = 4
    MIRROR = 5   # CHIA mirror ASX

import gevent
def active_wait(predicate,**kw):
    """ """
    assert callable(predicate)
    timeout = kw.get("timeout",5)
    raise_timeout = kw.get("raise_timeout",False)

    start = datetime.now()
    while True:
        if predicate():
            break
        else:
            now = datetime.now()
            if (now - start).total_seconds() < timeout:
                gevent.sleep(0.01)
            else:
                if raise_timeout:
                    raise TimeoutError("timeout: %d for %s" % (timeout,predicate()))
                return predicate()

    return True
