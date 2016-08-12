""" query regulatory data out of trading_tech_common.


 CodeSet                      column2    
 ---------------------------  ---------- 
 ACCOUNT_NAME_AST             2470       
 CLIENT_OE_ID_AST             1415       
 INTERNAL_ACCOUNT_NUMBER_AST  15         
 IOS_ACCOUNT_AST              20770      
 STAR_CUSTOMER_ID_AST         1260       



 CodeSet          Code     Name                    Value    
 ---------------  -------  ----------------------  -------- 
 IOS_ACCOUNT_AST  123      ASICINTERMEDIARYID      0        
 IOS_ACCOUNT_AST  123      ASICORIGINOFORDER       43760    
 IOS_ACCOUNT_AST  123      ASICWHOLESALEINDICATOR  0        
 IOS_ACCOUNT_AST  123      PARTICIPANTCAPACITY     A        
 IOS_ACCOUNT_AST  123      UCPKEY                  0        


--- Standing Instruction  ------

SELECT 
    ci.description AS client_name, 
    cd.IOS_Org, 
    ca.IOS_Account, 
    ca.IOS_Xref, 
    cd.Default_SOR_Strategy 
FROM 
    ANZ_Client_Accounts ca 
        INNER JOIN ANZ_Client_Details cd 
        ON cd.client_id = ca.client_id 
            INNER JOIN ANZ_Client_Identity ci 
            ON ci.client_id = ca.client_id 
WHERE 
    cd.Has_Standing_Inst = 1 
GO 



"""
import logging 
from connection_info import DB_Conns, Sybase

import threading

log = logging.getLogger(__name__)
## name mapping
ref_map = {'xref': "IOS_ACCOUNT_AST",
           'oeid': "CLIENT_OE_ID_AST",
           'starid': "STAR_CUSTOMER_ID_AST",
           'tam': "ACCOUNT_NAME_AST",
           'acctnum': "INTERNAL_ACCOUNT_NUMBER_AST",
           }

class GSRegData:

    """ query REG Data."""

    conn_info = DB_Conns['COMMON_S']
    conn_  = Sybase.connect(conn_info['server'],
                            'rds_ro',
                            'rds_ro',
                            conn_info['database'])
    cache_xref_ = {}
    cache_oeid_= {}
    cache_starid_ = {}
    cache_tam_ = {}
    cache_acttnum_ = {}

    si_cache_ = {}

    def __init__(self):

        ## force initialisation
        if any(self.cache_xref_) == False:
            worker = threading.Thread(target=self.query_all_accounts)
            worker.start()
        if any(self.si_cache_) == False:
            worker = threading.Thread(target=self.query_si_details)
            worker.start()

    def query_all_accounts(self):
        """ query all ios account. """

        if any(self.cache_xref_) == False:

            cur = self.conn_.cursor()

            sql = "select CodeSet, Code, Name,Value from tbl_RegValueRDS"
            log.info("query all accounts: %s" % sql)
            cur.execute(sql)

            count = 0
            while True:
                res = cur.fetchmany(200)
                ## stop on empty list
                if len(res) ==0: break
                count += 1
                print("Process account batch: %d" % count)
                for r in res:
                    if r[0] == "IOS_ACCOUNT_AST":
                        if r[1] not in self.cache_xref_:
                            ## initialize item
                            self.cache_xref_[r[1]] = {}
                        ## update item with key=value
                        self.cache_xref_[r[1]][r[2]] = r[3]
                    elif r[0] == "CLIENT_OE_ID_AST":
                        if r[1] not in self.cache_oeid_:
                            ## initialize item
                            self.cache_oeid_[r[1]] = {}
                        ## update item with key=value
                        self.cache_oeid_[r[1]][r[2]] = r[3]
                    elif r[0] == "STAR_CUSTOMER_ID_AST":
                        if r[1] not in self.cache_starid_:
                            ## initialize item
                            self.cache_starid_[r[1]] = {}
                        ## update item with key=value
                        self.cache_starid_[r[1]][r[2]] = r[3]
                    elif r[0] == "ACCOUNT_NAME_AST":
                        if r[1] not in self.cache_tam_:
                            ## initialize item
                            self.cache_tam_[r[1]] = {}
                        ## update item with key=value
                        self.cache_tam_[r[1]][r[2]] = r[3]

                    elif r[0] == "INTERNAL_ACCOUNT_NUMBER_AST":
                        if r[1] not in self.cache_acttnum_:
                            ## initialize item
                            self.cache_acttnum_[r[1]] = {}
                        ## update item with key=value
                        self.cache_acttnum_[r[1]][r[2]] = r[3]

                    else:
                        assert "unknown CodeSet key: %s" % r[0]


            cur.close()
            log.info("finished query all rds account")
        return {
                'xref': self.cache_xref_,
                'oeid': self.cache_oeid_,
                'starid': self.cache_starid_,
                'tam': self.cache_tam_,
                ## internal default
                'acctnum': self.cache_acttnum_,
                }

    def get_firms(self,qualifier="xref"):
        """ return all xref with PARTICIPANTCAPACITY = P. """

        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]
        ret = []
        for k,v in accounts.iteritems():
            if v['PARTICIPANTCAPACITY'] == 'P':
                ret.append(k)

        return ret

    def get_mixed(self,qualifier="xref"):
        """ return all xref with PARTICIPANTCAPACITY = M. """

        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]
        ret = []
        for k,v in accounts.iteritems():
            if v['PARTICIPANTCAPACITY'] == 'M':
                ret.append(k)

        return ret

    def get_clients(self,qualifier="xref"):
        """ reteurn all xref with PARTICIPANTCAPACITY != P. """
        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]

        ret = []
        for k,v in accounts.iteritems():
            if v['PARTICIPANTCAPACITY'] != 'P':
                ret.append(k)
        return ret

    def get_wholeIndicator_flagged(self,qualifier="xref"):
        """ return xref with wholeSalesIncaditator flagged. """
        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]
        ret = []
        for k,v in accounts.iteritems():
            if v['ASICWHOLESALEINDICATOR'] != '0':
                ret.append(k)
        return ret

    def get_ordOrigin_flagged(self,qualifier="xref"):
        """ return xref with orderOrigin flagged. """
        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]
        ret = []
        for k,v in accounts.iteritems():
            if v['ASICORIGINOFORDER'] :
                ret.append(k)
        return ret

    def get_intermediary_flagged(self,qualifier="xref"):
        """ return xref with intermediary flagged."""
        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]
        ret = []
        for k,v in accounts.iteritems():
            if v['ASICINTERMEDIARYID'] != '0' :
                ret.append(k)
        return ret

    def get_regdata_byKey(self,key, **kw):
        """ return reg data for xref. """
        qualifier = kw.get("qualifier","xref")
        assert qualifier in self.query_all_accounts()
        accounts = self.query_all_accounts()[qualifier]

        if key in accounts:
            ## only xref has SI for now.
            if key not in self.si_cache_:
                return accounts[key]
            else:
                ret = accounts[key].copy()
                ret['SORSTRATEGYOVERRIDE'] = self.si_cache_[key]['sor']
                return ret
        else:
            return  {'ASICINTERMEDIARYID': '0',
                     'ASICORIGINOFORDER': 'GSJP',
                     'ASICWHOLESALEINDICATOR': '0',
                     'PARTICIPANTCAPACITY': 'A',
                     'ASICWHOLESALEINDICATOR': '0',
                     'UCPKEY':'0',}

    def query_si_details(self):
        """ query SI for all accounts. """

        if any(self.si_cache_) == False:

            cur = self.conn_.cursor()

            sql = " SELECT ca.IOS_Xref, ci.description AS client_name, cd.IOS_Org, ca.IOS_Account, cd.Default_SOR_Strategy \
                    FROM ANZ_Client_Accounts ca \
                    INNER JOIN ANZ_Client_Details cd \
                    ON cd.client_id = ca.client_id \
                    INNER JOIN ANZ_Client_Identity ci \
                    ON ci.client_id = ca.client_id \
                    WHERE cd.Has_Standing_Inst = 1 "

            cur.execute(sql)

            for r in cur.fetchall():
                if r[0] not in self.si_cache_:
                    self.si_cache_[r[0]] = {}
                self.si_cache_[r[0]]['ios_org'] = r[2]
                self.si_cache_[r[0]]['ios_account'] = r[3]
                self.si_cache_[r[0]]['sor'] = r[4]
            cur.close()
        return self.si_cache_

    def get_si_xrefs(self,uniqueSor=False):
        """ return all SI xrefs. """
        ret = []
        sidata = self.query_si_details()
        for  k,v in sidata.iteritems():
            if uniqueSor:
                ## check if v['sor'] already in ret
                if v['sor'] not in [sidata[d]['sor'] for d in ret]:
                    ret.append(k)
            else:
                ret.append(k)

        return ret

    def get_si_byXref(self,xref):
        """ return xref's SI details. """

        sidata = self.query_si_details()
        if xref in sidata:
            return sidata[xref]

## workaround pytest error on exist
##Exception AttributeError: "'NoneType' object has no attribute 'debug_msg'" in <bound method Connection.__del__ of <Sybase.Connection instance at 0x22c8050>> ignored
import atexit
atexit.register(GSRegData.conn_.close)

if __name__ == "__main__":
    """ unittest. """

    #regdata, name = GSRegData(), "xref"
    #regdata, name = GSRegData("oeid"),"oeid"
    #regdata, name = GSRegData("starid"), "starid"
    #regdata, name = GSRegData("tam"), "tam"
    regdata = GSRegData()

    accounts = regdata.query_all_accounts()
    assert "xref" in accounts
    assert "starid" in accounts
    assert "oeid" in accounts
    assert "tam" in accounts

    print "firm by xref"
    print len(regdata.get_firms("xref"))
    print "client by xref"
    print len(regdata.get_clients("xref"))
    print "wholeSaleIndicator flagged by xref"
    print len(regdata.get_wholeIndicator_flagged("xref"))
    print "orderOrigin flagged by xref"
    print len(regdata.get_ordOrigin_flagged("xref"))
    print "intermediary flagged by xref"
    print len(regdata.get_intermediary_flagged("xref"))


    print " ========== OEID ============"
    print "firm "
    print len(regdata.get_firms("oeid"))
    print "client "
    print len(regdata.get_clients("oeid"))
    print "wholeSaleIndicator flagged "
    print len(regdata.get_wholeIndicator_flagged("oeid"))
    print "orderOrigin flagged "
    print len(regdata.get_ordOrigin_flagged("oeid"))
    print "intermediary flagged "
    print len(regdata.get_intermediary_flagged("oeid"))


    print " ========== STARID ============"
    print "firm "
    print len(regdata.get_firms("starid"))
    print "client "
    print len(regdata.get_clients("starid"))
    print "wholeSaleIndicator flagged "
    print len(regdata.get_wholeIndicator_flagged("starid"))
    print "orderOrigin flagged "
    print len(regdata.get_ordOrigin_flagged("starid"))
    print "intermediary flagged "
    print len(regdata.get_intermediary_flagged("starid"))

    print " ========== TAM ============"
    print "firm "
    print len(regdata.get_firms("tam"))
    print "client "
    print len(regdata.get_clients("tam"))
    print "wholeSaleIndicator flagged "
    print len(regdata.get_wholeIndicator_flagged("tam"))
    print "orderOrigin flagged "
    print len(regdata.get_ordOrigin_flagged("tam"))
    print "intermediary flagged "
    print len(regdata.get_intermediary_flagged("tam"))


    print "query regdata by oeid"
    for i in regdata.get_wholeIndicator_flagged("oeid"):
        print i, regdata.get_regdata_byKey(i,qualifier="oeid")


    print "query OP6"
    print regdata.get_regdata_byKey("FC1")

    print "si data by xref "
    for xref in  ('ZI8','DL72', 'FC3','D02'):
        print regdata.get_si_byXref(xref)

