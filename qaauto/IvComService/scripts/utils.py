"""
"""
import logging
from datetime import datetime,timedelta
import cfg
from cfg import json
from cfg import om2CompleteCatalog, om2CompleteCatalogEnums

log = logging.getLogger(__name__)
from conf import settings


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

### common utils
def tickSize(last,num=1):
    """ return right tickSize based on last price.

    tick size for both ASX/CXA
    input in dollar

    """
    if last >= 2.00:  # $2.00
        return 0.01 * num # 1cent
    elif last >= 0.1: # $0.1 to $2.00 (not inc)
        return 0.005 * num # half cent
    else:
        return 0.001 * num # 0.1 cent

def halfTick(last):
    """ return half tick.  """

    one_t = tickSize(last)
    return one_t * 0.5

def opposite_side(side):
    """ return opposide side. """

    assert type(side) == str
    assert side.upper() in set(['BUY','B','SELL','S','SHORT SELL','SS','SHORT', 'SSE','SHORT SELL EXEMPT'])
    if side.upper() in set(['BUY','B']):
        return 'Sell'
    return 'Buy'

def norm_side(side):
    """ return nomalized side. """

    assert type(side) == str
    assert side.upper() in set(['BUY','B','SELL','S','SHORT SELL','SS','SHORT', 'SSE','SHORT SELL EXEMPT'])
    if side.upper() in set(['BUY','B']):
        return 'Buy'
    return 'Sell'

def round_price(price,**kw):
    """ return rounded price in the right tickSize.

    input: price in dollar, regardless buy or sell, round upward
    price right tick size
        >= 200   1 cent
        200 ~ 10 0.5 cent
        < 10   0.1 cent

    """
    dollar = kw.get("dollar",True)
    side = kw.get("side","Buy")

    if dollar:
        price = price * 100.0

    if price == 0.0:
        return price
    # round price for 1 cent
    if price >=200:
        if round(price)/100.0 == price/100.0:
            return price/100.0
        elif price/100.0 > round(price)/100.0:
            ## round down
            if side == "Buy":
                return round(price)/100.0
            else:
                return round(price+1)/100.0
        else:
            ## round up
            if side == "Buy":
                return round(price-1)/100.0
            else:
                return round(price)/100.0

    elif price >=10:
        if price == math.floor(price):
            return round(price)/100.0
        # fraction and > 0.5
        elif price > math.floor(price) + 0.5:
            if side == "Buy":
                ## round down
                return (math.floor(price) + 0.5)/100.0
            else:
                ## round up
                return math.ceil(price) /100.0

        else: # < 0.5, round up to 0.5 cents

            if side == "Buy":
                return math.floor(price)/100.0
            else:
                return (math.floor(price) + 0.5)/100.0
    else:
        # 0.1 cent
        if price /100.0 == round(price,1)/100.0:
            return round(price,1)/100.0

        elif price/100.0 > round(price,1)/100.0:
            ## round down
            if side == "Buy":
                return round(price,1)/100.0
            else:
                return round(price + 0.1)/100.0
        else:
            ## round up
            if side == "Buy":
                return round(price-0.1,1)/100.0
            else:
                return round(price,1)/100.0


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

import ctypes
import mmap
import time
import os
import struct
from datetime import date
class SeqNumber():
    """ quick/dirty sequence generator."""

    def __init__(self,path,name):
        """ """
        today = date.today().isoformat()
        fn = os.path.join(path,'%s_%s.mmap' %(name,today))
        if os.path.exists(fn):
            fd = os.open(fn,os.O_RDWR)
        else:
            fd = os.open(fn,os.O_CREAT|os.O_TRUNC|os.O_RDWR)
            assert os.write(fd,'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE

        self.buf_ = mmap.mmap(fd,mmap.PAGESIZE,mmap.MAP_SHARED)

        log.info("Init SeqNumber name:%s, date:%s at:%d" % (name,today,self.current))

    @property
    def next(self):
        """ return next seq nmber"""
        seq = ctypes.c_int64.from_buffer(self.buf_)

        seq.value +=1

        return seq.value

    def set_next(self,val):
        seq = ctypes.c_int64.from_buffer(self.buf_)
        seq.value = val

    @property
    def current(self):
        seq = ctypes.c_int64.from_buffer(self.buf_)
        return seq.value

