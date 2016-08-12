""" run migrated apollo test cases out of JSON test cases file.

- first spreadsheet test cases should be migrated into JSON test file.
- then run pytest on this file.

"""
import os
import sys
import logging
import json
import time

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(os.path.dirname(CUR_DIR))
MIGRATED_DIR = os.path.join(PROJ_ROOT,"migrated")

from qfix_client import QFIX_ClientSession

from conf import settings

log = logging.getLogger(__name__)
##############################
## core test case generate here
from tc_template import generate_test

class Test_ApolloSimulator():
    """ om2 simulator test cases

    test cases shall be generated based on omsimulator test scripts.

    """
    @classmethod
    def setup_class(cls):
        """ """
        log.info("setUpClass")
        Test_ApolloSimulator.session_ = QFIX_ClientSession(settings.TEST_SESSION)

    @classmethod
    def teardown_class(cls):
        """ """
        Test_ApolloSimulator.session_.close()
        print "exit ok"

#####################################
## generate test run start here.

if "TEST_CASE" not in os.environ:
    raise EnvironmentError("TEST_CASE not found in envionment variables")
## check test case in migrated folder
test_case = os.path.join(MIGRATED_DIR,"%s.json" % os.environ["TEST_CASE"])

if not os.path.exists(test_case):
    raise EnvironmentError("test case: %s not found in migrated folder" % test_case)

tests = json.load(open(test_case,"r"))
log.info("start processing tests: %s" % test_case)

## generate each pyabner test step into test case
for idx, test in enumerate(tests):
    ## line up test id  with test case
    test_name = "test_%d" %  (idx + 1)
    #print test_name
    _test_method = generate_test(test,test_name)
    setattr(Test_ApolloSimulator,test_name,_test_method)


