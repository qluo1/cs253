### this is an old code no longer used.
""" load symbol/sedol out of prime

GSPrimeSymbols  - load all symbols out of prime based exchange i.e. SYDE,CHIA
GSSymbol        - lookup primeID, lookup sedol for individual symbol
GSSymbolAttr    - lookup symbol trading attributes like minQty

caching list symobl in redis

"""
from datetime import datetime,timedelta
from connection_info import DB_Conns, Sybase
from collections import namedtuple

from cfg import json

GSSYMBOL = namedtuple("GSSYMBOL","GSID,SYMBOL")

today = datetime.now()

class GSSymbol:

    """ query GS product_id.

    caching primeId with db as hset

    """

    conn_info = DB_Conns['PRODUCT_T1']
    #import pdb;pdb.set_trace()
    conn_  = Sybase.connect(conn_info['server'],
                            'rds_ro',
                            'rds_ro',
                            conn_info['database'])


    ## internal cache
    cache_ = {}

    def query_symbol(self,symbol):
        """ query symbol   """
        symbol = symbol.upper()
        cur = self.conn_.cursor()

        exch = "SYDE"
        ## default to SYDE
        if "." not in symbol:
            symbol = symbol + ".AX"

        ## set to CHIA
        if symbol.endswith(".CHA"):
            exch = "CHIA"

        if not rdb.hmget(self.cache_key,symbol)[0]:
            ## build cache
            sql = """select s.product_id_i,rtrim(s.synonym_c)
                    from synonym s, product p
                    where s.syn_market_cd_c = '%s'
                    and s.synonym_type_cd_c = 'RIC'
                    and s.product_id_i = p.product_id_i
                    and s.synonym_end_d is NULL
                    and p.instr_type_cd_c IN ('STOCK','WRNT')
                    and (p.issue_status_cd_c IS NULL OR
                    p.issue_status_cd_c NOT IN (
                                    'NAM',
                                    'NAC',
                                    'INV',
                                    'MER',
                                    'CLD',
                                    'MAT',
                                    'BKT',
                                    'WI' ,
                                    'DLS',
                                    'LIQ',
                                    'TRS'
                                        )
                ) and s.synonym_c = '%s' """ % (exch,symbol)

            #print sql
            cur.execute(sql)
            ret = [GSSYMBOL._make(r) for r in cur.fetchall()]
            if len(ret) != 1:
                raise ValueError("unexpect symbol :%s %s" %(symbol,ret))

            #import pdb;pdb.set_trace()
            assert rdb.hmset(self.cache_key,{ret[0].SYMBOL: ret[0].GSID})
            ##  expire the key in 1 day
            if not rdb.ttl(self.cache_key):
                rdb.expireat(self.cache_key,today + timedelta(days=1))

            cur.close()

        return int(rdb.hmget(self.cache_key,symbol)[0])

    def query_sedol(self,symbol):
        """ """

        gssymbol = self.query_symbol(symbol)
        assert gssymbol
        cur = self.conn_.cursor()

        sql = "select synonym_c from synonym where product_id_i = %d and synonym_type_cd_c = 'SED'" % gssymbol

        cur.execute(sql)

        ret = [r for r in cur.fetchall()]
        cur.close()
        #print ret
        assert len(ret) == 1
        return r[0].strip()


class GSSymbolAttr:

    """ query symbol attributes."""

    conn_info = DB_Conns['CLIENT_T1']
    conn_  = Sybase.connect(conn_info['server'],
                            'rds_ro',
                            'rds_ro',
                            conn_info['database'])
    gssymbol_ = GSSymbol()

    ## caching key in prime: 
    cache_ = {}
    def query_symbol(self,symbol):

        if symbol in self.cache_:
            return self.cache_[symbol]

        primeId = self.gssymbol_.query_symbol(symbol)
        cur = self.conn_.cursor()
        sql = "select property_name, property_value from product_property where product_id = '%s' " % primeId
        #print sql
        cur.execute(sql)
        ret = dict([(r[0], r[1]) for r in cur.fetchall()])
        ret['GSID'] = primeId
        if 'CLOSEPRICE' in ret and 'OUTSTANDINGSHARES' in ret:
            ret['RANK'] = int(round(float(ret['OUTSTANDINGSHARES']) * float(ret['CLOSEPRICE']) / 1000000))
        cur.close()

        self.cache_[symbol] = ret

        return self.cache_[symbol]

class GSPrimeSymbols:

    """ list all gs primary symbol for AX or CHA. """

    conn_info = DB_Conns['PRODUCT_T1']
    conn_ = Sybase.connect(conn_info['server'],
                           conn_info['user'],
                           conn_info['pwd'],
                           conn_info['database'])

    cache_key = "GS_symbol_"

    def list_prime_symbols(self,exch='AX',cache={}):
        """ query GS for ASX symbols.

        input: exch = AX, CHA
        return list of GSSYMBOL

        """
        exch = exch.upper()
        if exch in cache:
            return cache[exch]

        if not rdb.exists(self.cache_key + exch):

            cur= self.conn_.cursor()

            ## only select STOCK, load prime take too long to load, ignore type: rtrim(p.instr_type_cd_c)
            sql = """ select s.product_id_i,rtrim(s.synonym_c)
                        from synonym s, product p
                        where s.synonym_type_cd_c = 'RIC'
                        and s.syn_subtype_cd_c = '%s'
                        and  s.synonym_end_d is null
                        and s.product_id_i = p.product_id_i
                        and p.issue_status_cd_c in (NULL,'ISS')
                        and p.instr_type_cd_c = 'STOCK'""" % exch
                        #and p.instr_type_cd_c in ('BOND','WRNT','STOCK')""" % exch
            #print sql
            cur.execute(sql)

            #cache[exch] = [GSSYMBOL._make(r) for r in cur.fetchall()]

            data = [r for r in cur.fetchall()]
            #import pdb;pdb.set_trace()
            rdb.set(self.cache_key + exch, json.dumps(data))
            if not rdb.ttl(self.cache_key + exch):
                rdb.expireat(self.cache_key + exch, today + timedelta(days=1))
            cur.close()
        else:

            data = rdb.get(self.cache_key + exch)
            data = json.loads(data)


        return [GSSYMBOL._make(r) for r in data]

import atexit
# workaround pytest error on exit
atexit.register(GSSymbol.conn_.close)
atexit.register(GSSymbolAttr.conn_.close)
atexit.register(GSPrimeSymbols.conn_.close)

if __name__ == "__main__":
    """ unit test """
    import sys

    if len(sys.argv) != 2:
        print "usage gssymbol <symbol>"
        exit(1)

    symbol = sys.argv[1].upper()
    gssymbol = GSSymbol()

    import pdb;pdb.set_trace()
    print "productId", gssymbol.query_symbol(symbol)

    print "sedol", gssymbol.query_sedol(symbol)


    symbolAttr = GSSymbolAttr()

    print symbolAttr.query_symbol(symbol)
    print symbolAttr.query_symbol(symbol)

    prime = GSPrimeSymbols()
    #print len(prime.list_prime_symbols("CHA"))
    #print len(prime.list_prime_symbols())
