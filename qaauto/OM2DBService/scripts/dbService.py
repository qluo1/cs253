"""

"""
import sys
import traceback
from datetime import datetime,timedelta
from collections import namedtuple
from connection_info import DB_Conns, Sybase
from pprint import pprint

import logging

log = logging.getLogger(__name__)
GSSYMBOL = namedtuple("GSSYMBOL","GSID,SYMBOL,TYPE")

class GSSymbol(object):

    ## internal cache
    cache_ = {}
    conn_info = DB_Conns['PRODUCT_T1']
    conn_  = Sybase.connect(conn_info['server'],
                            'rds_ro',
                            'rds_ro',
                            conn_info['database'])

    def load_symbols_from_sybase(self):
        """ load gs symbol from PRIME and cached within memory."""

        log.info("load symbol from sybase %s" % GSSymbol.conn_info)
        cur = self.conn_.cursor()

        sql = """ select s.product_id_i ,rtrim(s.synonym_c),rtrim(p.instr_type_cd_c)
                  from synonym s, product p
                  where s.syn_market_cd_c in ('SYDE','CHIA')
                  and s.synonym_type_cd_c = 'RIC'
                  and s.product_id_i = p.product_id_i
                  and p.instr_type_cd_c IN ('STOCK','WRNT')
                  and p.issue_market_cd_c = 'AU'
                  and p.issue_status_cd_c NOT IN ('NAM','NAC','INV','MER','CLD','MAT','BKT','WI','DLS')
                  """

        cur.execute(sql)
        res = [GSSYMBOL._make(r) for r in cur.fetchall()]

        GSSymbol.cache_= {}
        for item in res:
            GSSymbol.cache_[item.SYMBOL] = (item.GSID, item.TYPE)

    def query_symbol(self,symbol):
        """ query single symbol for GSID and TYPE."""

        symbol = symbol.upper()

        if symbol.split(".")[-1] not in ("AX","CHA"):
            raise ValueError("symbol must for AX or CHA: %s" % symbol)

        if symbol not in self.cache_:
            raise ValueError("symbol not found: %s in cache: %d" % (symbol,len(self.cache_.keys())))

        return GSSymbol.cache_[symbol]

    def list_symbols(self,**kw):
        """ list all available symbol for exchange."""

        exch = kw.get("exchange","SYDE")
        assert exch in ("SYDE","CHIA")
        inst_type = kw.get("instType")
        assert inst_type in (None, "STOCK","WRNT")

        assert len(GSSymbol.cache_.keys()) > 0
        ret = []
        for item in GSSymbol.cache_.keys():
            if exch == "SYDE" and item.endswith("AX"):
                ret.append(item)
            elif exch == "CHIA" and item.endswith("CHA"):
                ret.append(item)
            else:
                pass
        ## filter on inst_type
        if inst_type is not None:
            return [i for i in ret if GSSymbol.cache_[i][1] == inst_type]
        ## no filter inst_type
        return ret

class GSSymbolAttrs(object):
    """ query darpan for symbol attributes. """

    ## internal cache
    cache_ = {}
    conn_info = DB_Conns['CLIENT_T1']
    conn_  = Sybase.connect(conn_info['server'],
                            'rds_ro',
                            'rds_ro',
                            conn_info['database'])

    def __init__(self, gssymbol):
        """ """
        self.gssymbol_ = gssymbol
        log.info("query symbol attrs from sybase: %s" % GSSymbolAttrs.conn_info)

    def query_symbol_attrs(self,symbol):
        """ query symbol for attributes. """

        if symbol in GSSymbolAttrs.cache_:
            return GSSymbolAttrs.cache_[symbol]

        _res = self.gssymbol_.query_symbol(symbol)
        primeId = _res[0]
        cur = self.conn_.cursor()
        sql = "select property_name, property_value from product_property where product_id = '%s' " % primeId
        #print sql
        cur.execute(sql)
        ret = dict([(r[0], r[1]) for r in cur.fetchall()])
        ret['GSID'] = primeId
        cur.close()

        ## keep the result
        GSSymbolAttrs.cache_[symbol] = ret
        return GSSymbolAttrs.cache_[symbol]


class GSClientDb(object):
    """ """

    cache_ = {}
    conn_info = DB_Conns['CLIENT_S']
    conn_  = Sybase.connect(conn_info['server'],
                            'qa_client_db',
                            'qa_client_db',
                            conn_info['database'])

    def list_client_starId(self):
        """ """
        cur = self.conn_.cursor()
        sql = """
        select b.access_id,a.client_id ,a.market ,a.service_offering
        from client_account a, client_mapping b
        where a.market = b.market
        and a.market in ('SYDE','CHIA')
        and a.client_id = b.client_id
        and a.product_type = 0
        and a.product_sub_type = 4
        and a.legal_entity in (9, 0,1)
        and a.account_syn_type = 5
        and a.service_offering in (4,3)
        and b.access_id_type = 1 
        """

        if not any(self.cache_):
            #print sql
            cur.execute(sql)
            for r in cur.fetchall():
                starId = r[1]
                if starId not in self.cache_:
                    self.cache_[starId] = []

                item = (r[0],r[2],r[3])
                if item not in self.cache_[starId]:
                    self.cache_[starId].append(item)

            cur.close()

        #pprint(self.cache_)
        return self.cache_.keys()
    def query_access(self,starId):
        """ """
        if  not any(self.cache_):
            self.list_client_starId()

        if starId in self.cache_:
            return self.cache_[starId]



from regdata import GSRegData

import threading

class DBService(object):
    """ """

    def __init__(self):
        """ """
        start = datetime.now()
        self.symbols_ = GSSymbol()
        log.info("loading symbol from sybase.")
        self.symbols_.load_symbols_from_sybase()
        end = datetime.now()
        log.info("loaded GS %d symbols in : %s" % (len(GSSymbol.cache_.keys()),end-start))

        self.symbolAttrs_ = GSSymbolAttrs(self.symbols_)

        log.info("loading regdata")
        self.regdata_ = GSRegData()
        log.info("finished dbservice constructor")

        ## local cache 
        self._symbols_with_mxq = {}
        self._symbols_without_mxq = {}
        log.info("caching stock with mxq")

        self._clientdb = GSClientDb()
        ids = self._clientdb.list_client_starId()
        log.info("cached clientId: %sd" % len(ids))

        ## workout top 200/300 symbols

        self.symbol_ranking = {}
        self.symbol_50_ = []
        self.symbol_100_ = []
        self.symbol_200_ = []
        self.symbol_300_ = []

        worker = threading.Thread(target=self.list_symbol_with_mxq)
        worker.start()

    ## prime symbol
    def list_asx_symbols(self):
        """ """
        return self.symbols_.list_symbols(exchange="SYDE")

    def list_chia_symbols(self):
        """ """
        return self.symbols_.list_symbols(exchange="CHIA")

    def list_asx_stocks(self):
        """ """
        return self.symbols_.list_symbols(exchange="SYDE",instType="STOCK")

    def list_asx_warrants(self):
        """ """
        return self.symbols_.list_symbols(exchange="SYDE",instType="WRNT")

    ## darkpan symbol attrs
    def query_symbol_attrs(self,symbol):
        """ """
        return self.symbolAttrs_.query_symbol_attrs(symbol)

    ## list symbol with mxq or no_mxq
    def list_symbol_with_mxq(self,flag=True):
        """ """

        if flag and any(self._symbols_with_mxq):
            return self._symbols_with_mxq.keys()
        elif not flag and any(self._symbols_without_mxq):
            return self._symbols_without_mxq.keys()
        else:
            ## load and build up cache.
            for symbol in self.list_asx_stocks():
                try:
                    attrs = self.query_symbol_attrs(symbol)
                except Exception,e:
                    log.warn("%s" % e)
                    continue
                if 'MINEXECUTABLEQTY' in attrs:
                    self._symbols_with_mxq[symbol] = None
                else:
                    self._symbols_without_mxq[symbol] = None

            log.info("finished caching stock with mxq")

            self._load_top_symbol()
            if flag:
                return self._symbols_with_mxq.keys()
            else:
                return self._symbols_without_mxq.keys()

    def _load_top_symbol(self):
        """ """
        try:
            ### work out top 200/300
            if len(self.symbol_200_) ==0 and len(self.symbol_300_) == 0:
                for symbol in self.list_asx_stocks():
                    print symbol
                    try:
                        attrs = self.symbolAttrs_.query_symbol_attrs(symbol)
                        if "CLOSEPRICE" in attrs and "OUTSTANDINGSHARES" in attrs:
                            rank = int(float(attrs["OUTSTANDINGSHARES"]) * float(attrs["CLOSEPRICE"]) / 100000)
                            self.symbol_ranking[symbol] = rank
                    except ValueError:
                        pass

                ## 
                assert len(self.symbol_ranking) > 300
                _market_cap = sorted(self.symbol_ranking.values(),reverse=True)
                _top_50  = _market_cap[50]
                _top_100 = _market_cap[100]
                _top_200 = _market_cap[200]
                _top_300 = _market_cap[300]

                self.symbol_50_  = [o for o in self.symbol_ranking if self.symbol_ranking[o] >= _top_50]
                self.symbol_100_ = [o for o in self.symbol_ranking if self.symbol_ranking[o] >= _top_100]
                self.symbol_200_ = [o for o in self.symbol_ranking if self.symbol_ranking[o] >= _top_200]
                self.symbol_300_ = [o for o in self.symbol_ranking if self.symbol_ranking[o] >= _top_300]

                log.info("top 50 market cap: {0:,}m".format(_top_50))
                log.info("top 100 market cap: {0:,}m".format(_top_100))
                log.info("top 200 market cap: {0:,}m".format(_top_200))
                log.info("top 300 market cap: {0:,}m".format(_top_300))

        except Exception,e:
            log.exception(e)

    def list_top_200(self):
        """ helper. """
        return self.symbol_200_
    def list_top_300(self):
        """ helper. """
        return self.symbol_300_
    def list_top_100(self):
        """ helper. """
        return self.symbol_100_
    def list_top_50(self):
        """ helper. """
        return self.symbol_50_

    ### regdata pass call to call regdata.
    def get_firms(self,**kw):
        """ """
        qualifier = kw.get("qualifier","xref")
        return self.regdata_.get_firms(qualifier=qualifier)

    def get_clients(self,**kw):
        """ """
        qualifier = kw.get("qualifier","xref")
        return self.regdata_.get_clients(qualifier=qualifier)
    def get_mixed(self,**kw):
        """ """
        qualifier = kw.get("qualifier","xref")
        return self.regdata_.get_mixed(qualifier=qualifier)

    def get_wholeIndicator_flagged(self,**kw):
        """ """
        qualifier = kw.get("qualifier","xref")
        return self.regdata_.get_wholeIndicator_flagged(qualifier=qualifier)

    def get_intermediary_flagged(self,**kw):
        """ """
        qualifier = kw.get("qualifier","xref")
        return self.regdata_.get_intermediary_flagged(qualifier=qualifier)

    def get_ordOrigin_flagged(self,**kw):
        """ """
        qualifier = kw.get("qualifier","xref")
        return self.regdata_.get_ordOrigin_flagged(qualifier=qualifier)

    def get_regdata_byKey(self,key, **kw):
        """ """
        return self.regdata_.get_regdata_byKey(key,**kw)

    def query_si_details(self):
        """ """
        return self.regdata_.query_si_details()

    def get_si_xrefs(self, **kw):
        """ """
        uniqueSor = kw.get("uniqueSor",False)
        return self.regdata_.get_si_xrefs(uniqueSor)

    def get_si_byXref(self,xref):
        """ """
        return self.regdata_.get_si_byXref(xref)

    def list_client_starId(self):
        return self._clientdb.list_client_starId()

    def get_client_access(self,clientId):
        return self._clientdb.query_access(clientId)

def run_as_service():
    """ """
    ## local libs
    import cfg
    from singleton import SingleInstance
    from conf import settings
    import gevent
    import zerorpc
    import signal
    ## setup logging
    import logging.config
    logging.config.dictConfig(settings.LOGGING)

    try:
        me = SingleInstance("DBService")
        s = zerorpc.Server(DBService())
        message = "start DBService at %s " % settings.API_URL
        log.info(message)
        s.bind(settings.API_URL)
        def trigger_shutdown():
            """ shutdown event loop."""
            log.info("signal INT received, stop event loop.")
            s.stop()
            log.info("RPC server stopped")
            sys.exit(0)

        message = "setup signal for INT/QUIT"
        log.info(message)
        ## register signal INT/QUIT for proper shutdown
        gevent.signal(signal.SIGINT,trigger_shutdown)
        print "running"
        s.run()
        log.info("finished cleanly.")
    except Exception,e:
        error = "run failed on exception: %s" % e
        print error
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error("%s, tb: %s" % (error, traceback.extract_tb(exc_traceback)))


def unittest():
    """ """

    client = GSClientDb()

    print client.list_client_starId()

if __name__ == "__main__":
    """ """
    run_as_service()

    #unittest()




