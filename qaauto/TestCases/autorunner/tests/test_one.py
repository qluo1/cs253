import os
import localcfg
from localcfg import LOCAL_TMP, LOCAL_RESULT,OM2_TEST_DIR,PROJ_DIR
from pprint import pprint

from runner import AutoRunner

import multiprocessing


def test_run_om2_testcases():
    """ """

    test_runner  =AutoRunner(LOCAL_TMP,LOCAL_RESULT,OM2_TEST_DIR,"settings.PPEAUCEA")

    result = test_runner.run_testcases("order_trade.py",nums=5)
    assert result
    print result
    assert os.path.exists(result['htmlreport'])


TEST_AUTORUN_DIR = os.path.join(PROJ_DIR,"tests","testautorunner")


def test_autorun_testcases():
    """ """
    test_runner  =AutoRunner(LOCAL_TMP,LOCAL_RESULT,TEST_AUTORUN_DIR,"settings.PPEAUCEA")

    result = test_runner.run_testcases("test_cases.py",nums=1)
    assert result
    print result
    assert os.path.exists(result['htmlreport'])

def test_autorun_collect():
    """ """
    test_runner  =AutoRunner(LOCAL_TMP,LOCAL_RESULT,OM2_TEST_DIR,"settings.PPEAUCEA")

    collected = test_runner.collect_testcases()
    print collected


def test_autorun_testsuites():
    """ """
    test_runner  =AutoRunner(LOCAL_TMP,LOCAL_RESULT,OM2_TEST_DIR,"settings.PPEAUCEA")

    result = test_runner.run_testsuites(noxdist=localcfg.OM2_NO_XDIST_TESTS,
                                        exclude=localcfg.OM2_EXCLUDE_TESTS,
                                        )
    assert result
    print result


def test_list_current_run():
    """ """
    from utils import current_running_test

    res = current_running_test(LOCAL_TMP)
    pprint(res)


import zerorpc
service = zerorpc.Client(localcfg.AUTORUNNER_SERVICE_ENDPOINT)

def test_api_run_testcase():
    """ """
    res = service.run_testcases("om2_ppe","order_audark.py")

    assert res == True

    res = service.run_testcases("om2_ppe","order_trade.py")
    assert res == True

def test_api_run_testsuites():
    """ """
    res = service.run_testsuites("om2_ppe")

    assert res == True

