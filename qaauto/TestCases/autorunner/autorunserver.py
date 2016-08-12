import os
import sys
import signal
import logging
## setup local env
import localcfg
from concurrent.futures import ThreadPoolExecutor as Executor ,Future
import gevent
import zerorpc

log = logging.getLogger("autorunserer")

from runner import AutoRunner

from plumbum import local


class AutoRunnerServer(object):
    """

    - register runner and test cases folder.
    -
    """

    runners_ = {}

    executor_ = Executor(5)

    collected_tests_ = {}
    ## individual test run result
    test_result_ = {}

    ## test suites results
    testsuite_result_ = {}

    def __init__(self):
        self.worker_ =  gevent.spawn(self._check_results)

    def register_runner(self,name,test_dir,**kw):
        """ register a named test runner and test case folder."""

        env_setting = kw.get("env_settings")
        if name not in self.runners_:
            self.runners_[name] = AutoRunner(localcfg.LOCAL_TMP,
                                             localcfg.LOCAL_RESULT,
                                             test_dir,
                                             env_setting)

    def collect_tests(self,name,**kw):
        """ collect test results for the runner."""
        ret = False
        if name in self.runners_ and name not in self.collected_tests_:
            future = self.executor_.submit(self.runners_[name].collect_testcases)
            self.collected_tests_[name] = future
        else:
            log.warn("runner not registered or tests already collected: %s" % self.collected_tests_)

        return ret

    def run_testcases(self,name,test_name,**kw):
        """ run individual test cases by file name.
        test_name like 'order_sor.py', not a full path, but must be found in os.path.join(test_dir,test_name)
        """
        ret = False

        if name not in self.runners_:
            raise ValueError("runner :%s not registerd! " % name)


        if name not in self.test_result_:
            self.test_result_[name] = {}

        if test_name not in self.test_result_[name]:
            runner = self.runners_[name]
            nums = kw.get("nums",0)
            future  = self.executor_.submit(runner.run_testcases,test_name,nums=nums)
            self.test_result_[name][test_name] = future
            ret = True

        return ret

    def run_testsuites(self,name,**kw):
        """ run entire testsuites.

        """
        exclude = kw.get("exclude",localcfg.OM2_EXCLUDE_TESTS)
        log.info("exclude: %s" % exclude)
        ret = False
        if name not in self.runners_:
            raise ValueError("runner :%s not registerd! " % name)

        if name not in self.testsuite_result_:
            runner = self.runners_[name]
            future = self.executor_.submit(runner.run_testsuites,
                                            noxdist=localcfg.OM2_NO_XDIST_TESTS,
                                            exclude=exclude
                                             )
            self.testsuite_result_[name] = future
            ret = True

        return ret

    def _check_results(self):
        """ """
        try:
            while True:

                for name,res in self.collected_tests_.iteritems():
                    if isinstance(res,Future) and res.done():
                        self.collected_tests_[name] = res.result()
                        #print self.collected_tests_[name]
                        print "collected: %s" % name

                for name,res in self.test_result_.iteritems():

                    if isinstance(res,Future) and res.done():
                        self.test_result_[name] = res.result()
                        print self.test_result_[name]

                for name, res in self.testsuite_result_.items():
                    if isinstance(res,Future) and res.done():
                        self.testsuite_result_[name] = res.result()
                        log.info("test suite completed: %s" % name)
                        print  "testsuite: %s done" % name
                        ## remove completed test suites
                        self.testsuite_result_.pop(name)

                gevent.sleep(1)
        except Exception,e:
            log.exception(e)


    def stop(self):
        """ """
        self.executor_.shutdown()
        self.worker_.kill()


def run_as_service():
    """ """

    runserver = AutoRunnerServer()
    ###########################
    ## register runner

    #runserver.register_runner("om2_qae",localcfg.OM2_TEST_DIR,env_settings="settings.QAEAUCEA")
    runserver.register_runner("om2_ppe",localcfg.OM2_TEST_DIR,env_settings="settings.PPEAUCEA")
    #runserver.register_runner("om2_pme",localcfg.OM2_TEST_DIR,env_settings="settings.PMEAUCEA")

    #runserver.run_testsuites("om2_ppe")
    #runserver.run_testsuites("om2_ppe")

    service = zerorpc.Server(runserver)
    service.bind(localcfg.AUTORUNNER_SERVICE_ENDPOINT)
    #runserver.collect_tests("om2_qae")
    #runserver.run_testcases("om2_qae","order_audark.py")

    def trigger_shutdown():
        """ shutdown event loop."""
        log.info("signal INT received, stop event loop.")
        service.close()
        runserver.stop()
        log.info("stopped")

    log.info("setup signal for INT/QUIT")
    ## register signal INT/QUIT for proper shutdown
    gevent.signal(signal.SIGINT,trigger_shutdown)
    service.run()


if __name__ == "__main__":
    """ """
    run_as_service()
