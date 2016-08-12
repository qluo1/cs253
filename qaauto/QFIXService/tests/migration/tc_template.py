""" convert apollo test case into unittest test case.
"""
import traceback
import os
import sys
import unittest
from pprint import pprint
import logging
import ujson as json
import time
import pdb
import pytest
import pyfix42

from tc_validation import validate_er
from tc_helper import patch_fix_order

log = logging.getLogger(__name__)
## from messageId lookup clOrdId
_id_maps = {}

next_clOrdId = lambda nextId: "%s_%d:%d" % (os.getlogin(),os.getpid(),nextId)

def generate_test(test,test_name):
    """ using closure for test generation. """

    def _template(self):
        """ test cases. """

        log.info("====== start test: %s =======" % test_name)
        assert 'actions' in test and 'expectedResults' in test
        testCaseName = test['testCaseName']
        actions = test['actions']
        expectedResults = test["expectedResults"]
        ## skip no action test
        if not isinstance(actions,list):
            return pytest.skip("no action list")
        log.info("test: %s testCase: %s" % (test_name,testCaseName))
        ## clean up for  better logging
        for action in actions:
            if 'trace' in action: action.pop("trace")
        for result in expectedResults:
            if 'trace' in result: result.pop("trace")

        log.debug("actions[%d]: %s" % (len(actions),actions))
        log.debug("expected: %s" % expectedResults)
        print test_name, "==> " , testCaseName
        ## debug test case
        #if test_name == "test_6":
        #import pdb;pdb.set_trace()

        for action in actions:
            serviceType = action['serviceType']
            assert serviceType=="fix-line"
            serviceName = action['serviceName']
            message = action['message']
            fields = message['fields']
            messageId = message['messageId']
            table = message['table']

            if table  == "Logout":
                return pytest.skip("skip logout. messageId: %s" % messageId)

            if table == "Logon":
                status = self.session_.check_session()
                assert isinstance(status,dict)
                assert status['enabled'] == True
                assert status['loggedon'] == True
                print "logon", status
                return

            print "action: %s" % action

            log.info("serviceType: %s, servcieName: %s, table: %s" \
                    % (serviceType, serviceName, table))

            if 'Text' in fields:
                fields.pop('Text')
            ## generate a new clOrdId
            test_clOrdId = next_clOrdId(self.session_.nextId)
            ## save to map
            _id_maps[messageId] = test_clOrdId
            ## enrich origClOrdID
            if 'OrigClOrdID' in fields:
                if fields['OrigClOrdID'] in _id_maps:
                    fields['OrigClOrdID'] = _id_maps[fields['OrigClOrdID']]
                else:
                    raise ValueError("origClOrdID:%s not found in internal map" %  fields['OrigClOrdID'])

            fields['ClOrdID'] = test_clOrdId
            ##  patch inconsistent
            patch_fix_order(table,fields)
            log.info("sending FIX order: %s" % fields)
            print "sending FIX Order: ", fields
            self.session_.send_apollo_order(fields)

        if isinstance(expectedResults,list):
               ## extract er(s)
               recv_res = self.session_.get_results(test_clOrdId,expected=len(expectedResults))
               log.info(" --- received: %d ---"  % len(recv_res))
               pprint(recv_res)
               assert validate_er(recv_res, expectedResults)

        log.info(" ====== end test: %s ========= \n" % test_name )

    return _template

