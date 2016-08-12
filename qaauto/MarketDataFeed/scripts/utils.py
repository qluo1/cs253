import csv
import os
import sys
import cfg
import logging
from conf import settings

log = logging.getLogger(__file__)

work_dir = os.path.dirname(os.path.abspath(__file__))

log.info(os.environ)

def get_asx_listed_symbols(res={}):
    """ get asx listed symbol from csv, return list of symobls.

    load offical asx listed symbols based on http://www.asx.com.au/asx/research/ASXListedCompanies.csv

    """
    if 'symbols' not in res:

        with open(settings.ASX_LISTED_COMPANY , "r") as f:
            reader = csv.reader(f)
            next(reader)
            next(reader)
            next(reader)
            res['symbols'] = [row[1] for row in reader]

    return res['symbols']


def get_chia_listed_symbols(res={}):
    """ list chia symbol from csv. return listed symbols.

    load offical chix listed symbols based on http://au.chi-x.com/TRADINGONCHI-X/TRADEABLESECURITIES.aspx

    """
    if 'symbols' not in res:
        with open(settings.CHIX_LISTED_SYMBOLS,"r") as f:
            symbols = []
            for line in f:
                l = line.strip()
                if l.endswith("AVAILABLE"):
                    symbols.append(l.split(",")[0])
            res['symbols'] = symbols
    return res['symbols']


## GS symbols
sys.path.insert(0,"/gns/mw/lang/python/modules/2.7.2/sybase-0.39/lib/python2.7/site-packages")
import Sybase
from  collections import namedtuple

from db_connection import DB_Conns

conn = DB_Conns['PRODUCT_S']
log.info("connect to db: %s" % conn['database'])
connection = Sybase.connect(conn['server'],conn['user'],conn['pwd'],conn['database'])

GSSYMBOL = namedtuple("GSSYMBOL","gsid,symbol,type")

def gs_prime_symbols(exch='AX',cache={}):
    """ query GS for ASX symbols.

    input: exch = AX, CHA
    return list of GSSYMBOL

    """
    exch = exch.upper()
    if exch in cache:
        return cache[exch]

    cur= connection.cursor()

    log.info("query prime db for :%s" % exch)
    ## only select STOCK, load prime take too long to load
    sql = """ select s.product_id_i,rtrim(s.synonym_c),rtrim(p.instr_type_cd_c)
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

    cache[exch] = [GSSYMBOL._make(r) for r in cur.fetchall()]
    cur.close()

    return cache[exch]


if __name__ == "__main__":
    """
    unit test
    """
    #print get_asx_listed_symbols()

    gs_prime_symbols(exch="CHA")
    print "done chia"
    gs_prime_symbols()
    print "done asx"

