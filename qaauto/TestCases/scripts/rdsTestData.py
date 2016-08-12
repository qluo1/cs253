"""  query sybase for random test regulatory test data.

"""
import os
from datetime import datetime

import cfg
import zerorpc
from conf import settings

class RDSTestData:
    """ rds test data from sybase i.e. OM2DBService. """

    def __init__(self):
        """ load rds reference data. """
        self.dbService_ = zerorpc.Client(settings.OM2DB_SERVICE_ENDPOINT)

    def si_xrefs(self,unique=True):
        """ return all xrefs with si override.

        only xref has SI override for now.
        """
        return self.dbService_.get_si_xrefs(uniqueSor=unique)

    def get(self,key,**kw):
        """ return reg data based xref. """
        qualifier = kw.get("qualifier","xref")
        return  self.dbService_.get_regdata_byKey(key,qualifier=qualifier)

    def sample_test_xrefs(self,**kw):
        """ workout sample test xrefs.

        - house xrefs
        - client xrefs
        - mixed xrefs
        - client_si xrefs

        - intermediary exist
        - wholesales  exist
        - unknown -- default
        """
        ##default sample 3 item
        size = kw.get("size",3)
        with_si = kw.get("with_si",True)

        HOUSE_XREFS = self.dbService_.get_firms(qualifier="xref")
        CLIENT_XREFS = self.dbService_.get_clients(qualifier="xref")
        MIXED_XREFS = self.dbService_.get_mixed(qualifier="xref")

        ## load test xrefs based on reg data
        INTERMED_XREFS = self.dbService_.get_intermediary_flagged(qualifier="xref")
        WHOLESALES_XREFS = self.dbService_.get_wholeIndicator_flagged(qualifier="xref")

        ## reg data should be default
        UNKNOWN_XREF = ['UNKNOWN',]

        ## execution venue not checked in GSI, need implemented with GSA with wxsinfo
        test_xrefs = MIXED_XREFS[:size] + \
                     HOUSE_XREFS[:size] + \
                     CLIENT_XREFS[:size] + \
                     INTERMED_XREFS[:size] + \
                     WHOLESALES_XREFS[:size] +\
                     UNKNOWN_XREF

        if with_si:
            ## only get unique sor per xref, False will list all SI xref
            CLIENT_SI_XREFS = self.dbService_.get_si_xrefs(uniqueSor=True)
            test_xres += CLIENT_SI_XREFS

        return test_xrefs

    def sample_tests(self,**kw):
        """ workout sample test oeid.

        - house xrefs
        - client xrefs
        - mixed xrefs

        - intermediary exist
        - wholesales  exist
        - unknown -- default
        """
        qualifier = kw.get("qualifier","xref")
        assert qualifier in ('xref','starid','oeid','tam')

        size = kw.get("size",3)
        with_si = kw.get("with_si",True)

        CLIENT_SI_XREFS = []
        ## only xref has SI override
        if qualifier == "xref" and with_si:
            CLIENT_SI_XREFS = self.si_xrefs(True)

        HOUSE_XREFS = self.dbService_.get_firms(qualifier=qualifier)
        CLIENT_XREFS = self.dbService_.get_clients(qualifier=qualifier)
        MIXED_XREFS = self.dbService_.get_mixed(qualifier=qualifier)

        ## load test xrefs based on reg data
        INTERMED_XREFS = self.dbService_.get_intermediary_flagged(qualifier=qualifier)
        WHOLESALES_XREFS = self.dbService_.get_wholeIndicator_flagged(qualifier=qualifier)

        ## reg data should be default
        UNKNOWN_XREF = ['UNKNOWN',]
        test_xrefs = []
        for item in (HOUSE_XREFS,CLIENT_XREFS,MIXED_XREFS, INTERMED_XREFS, WHOLESALES_XREFS,CLIENT_SI_XREFS):
            if len(item) > 0:
                if len(item) > size:
                    test_xrefs += item[:size]
                else:
                    test_xrefs += item
        test_xrefs += UNKNOWN_XREF
        return test_xrefs

