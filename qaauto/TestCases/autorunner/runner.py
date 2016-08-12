""" auto test runner.

TODO:

    - track how many rerun.
    - track failed test run number.
    - generate test report  for each testsuites.
"""
import os
import shutil
import ntpath
import gevent
from datetime import datetime,date,timedelta
import multiprocessing
from concurrent.futures import ThreadPoolExecutor as Executor

## setup local python path
import localcfg
## setup logging
import logging
import logging.config
logging.config.dictConfig(localcfg.LOG_CFG)
log = logging.getLogger(__name__)
## local utils
from utils import *

from plumbum import local, BG
## local pytest command
pytest = local[os.path.join(localcfg.PROJ_DIR,"bin","run_pytest.bash")]

## internal helper
def _collect_test_cases(testfile,**kw):
    """ internal helper to collect test cases."""
    cmd = pytest["--collectonly",testfile, "-p no:report.plugin"]
    res = None
    try:
        out = cmd()
        res =  parse_test_cases(out)
    except Exception,e:
        log.warn("collect test case failed: %s, error:%s" %(testfile,e))
        return (0,None)
    log.info("collected: %s, count: %d" % (testfile,res[0]))
    return res


class AutoRunner(object):
    """ """

    def __init__(self,tmpdir,resultdir,testdir,env_settings):
        """
        input:
            tmpdir : local tmpdir for track running test resultlog
            resultdir : where release html report will be copied to
              resultdir/release/good - capture good test run results
              resultdir/release/bad  -- capture failed test run results
            testdir : where test case file can be found.
            env_settings : om2 test env settings.

        """
        assert os.path.exists(tmpdir)
        assert os.path.exists(resultdir)
        assert os.path.exists(testdir)

        self.tmpdir_ = os.path.abspath(tmpdir)
        self.resultdir_ = os.path.abspath(resultdir)
        self.testdir_ = os.path.abspath(testdir)
        ## query om2 instance
        self.release = get_current_om_version(env_settings)
        if not self.release:
            raise ValueError("release tag not avialable: %s, %s" % (get_current_om_version(env_settings), env_setting))
        local.env["SETTINGS_MODULE"] = env_settings
        ##
        self.release_dirs_ = self._build_result_folders(self.release)
        ##
        self.num_cup = multiprocessing.cpu_count()

        #######################################
        ##  internal cached collected testcases
        self.collected_testcases_ = []
        ## track num of run
        self.run_id_ = -1

    def _build_result_folders(self,release_name):
         """ create default folder structure for a release."""
         release_dir = os.path.join(self.resultdir_,release_name)
         good_dir = os.path.join(release_dir,"gold")
         bad_dir = os.path.join(release_dir,"brown")

         if not os.path.exists(release_dir):
             os.makedirs(release_dir)
             assert os.path.exists(release_dir)
             os.makedirs(good_dir)
             assert os.path.exists(good_dir)
             os.makedirs(bad_dir)
             assert os.path.exists(bad_dir)

         return {'good': good_dir,
                 'bad': bad_dir,}

    def _execute_test_cases_with_pytest(self, test_file,**kw):
        """
        execute test cases in background with pytest.
        input: test case filename
        """
        assert os.path.exists(test_file)
        filename = ntpath.basename(test_file)
        assert filename.endswith(".py")
        module_name =filename.split(".")[0]
        ## running parameters
        reruns = kw.get("reruns",localcfg.DEFAULT_RERUNS)
        maxfail = kw.get("maxfail",localcfg.DEFAULT_MAXFAIL)
        debug = kw.get("debug",False)

        today = date.today().isoformat()
        htmlreport = "%s_%s_%d.html" %(today,module_name,self.run_id_)
        resultlog = "%s_%s_%d.log" % (today,module_name,self.run_id_)
        ## full path to test report and result
        resultlog = os.path.join(self.tmpdir_,resultlog)
        htmlreport = os.path.join(self.tmpdir_,htmlreport)
        ## nums
        nums = int(kw.get("nums",0))
        if nums > 0:
            if debug:
                f = pytest[test_file,"--maxfail=%s"% maxfail,
                             "--reruns=%s" % reruns,
                             "--resultlog=%s" % resultlog,
                             "--htmlreport=%s" % htmlreport,
                             "--debug",
                             "--trace-config",
                             "-n%d" % nums] & BG
            else:
                f = pytest[test_file,"--maxfail=%s"% maxfail,
                             "--reruns=%s" % reruns,
                             "--resultlog=%s" % resultlog,
                             "--htmlreport=%s" % htmlreport,
                             "-n%d" % nums] & BG
        else:
            if debug:
                f = pytest[test_file,"--maxfail=%s"% maxfail,
                             "--reruns=%s" % reruns,
                             "--htmlreport=%s" % htmlreport,
                             "--resultlog=%s" % resultlog,
                             "--debug",
                             "--trace-config"] & BG


            else:
                f = pytest[test_file,"--maxfail=%s"% maxfail,
                             "--reruns=%s" % reruns,
                             "--htmlreport=%s" % htmlreport,
                             "--resultlog=%s" % resultlog] & BG

        return {'future': f,
                'resultlog': resultlog,
                'htmlreport': htmlreport,
                }

    def run_testcases(self,testfile,**kw):
        """
        run individual testfile by pytest.

        """
        if not os.path.exists(testfile):
            if not os.path.exists(os.path.join(self.testdir_,testfile)):
                raise ValueError("test file can't be located: %s" % testfile)
            else:
                testfile = os.path.join(self.testdir_,testfile)
        today = date.today().isoformat()
        ## number of procesor
        nums = kw.get("nums",0)
        debug = kw.get("debug",False)
        test_file = os.path.abspath(testfile)
        test_name = ntpath.basename(test_file)
        log.debug("test_name: %s test_file: %s" % (test_name,test_file))

        ## check test name already had good result here 
        if os.path.exists(os.path.join(self.release_dirs_['good'],"%s_%s.html" % (test_name,today))):
            log.info("test run already passed for today: %s" % test_name)
            return

        res = self._execute_test_cases_with_pytest(test_file,nums=nums,debug=debug)
        assert 'future' in res
        f = res['future']
        assert 'resultlog' in res
        ## wait for finish
        passed = None
        try:
            log.debug("wait for run test cases: %s" % testfile)
            f.wait()
            assert f.ready()
            log.info("run test case completed: %s" % testfile)
            passed = True
            out = f.stdout
        except Exception,e:
            passed = False
            out = e.stdout
            log.info("run test case failed: %s" % testfile)

        result = check_resultlog(res['resultlog'])
        #htmlreport = extract_htmlreport(out)
        htmlreport = res['htmlreport']
        assert os.path.exists(htmlreport)
        log.info("html report generated:%s" % htmlreport)

        if not passed:
            log.error("test run [%s] failed: %s, log: %s" %  (test_name,result,res['resultlog']))
            new_report = os.path.join(self.release_dirs_['bad'],"%s_%s_%d.html" % (test_name,today,result['f']))
        else:
            log.info("test run [%s] passed: %s" % (test_name,result))
            new_report = os.path.join(self.release_dirs_['good'],"%s_%s.html" % (test_name,today))
            ## move resultlog to runtime archive
            archive_resultlog(res['resultlog'],self.tmpdir_)

        shutil.move(htmlreport,new_report)
        result['htmlreport'] = new_report

        return result

    def run_testsuites(self,**kw):
        """ """
        no_xdist = kw.get("noxdist",[])
        exclude = kw.get("exclude",[])

        start = datetime.now()
        self.run_id_ +=1
        print "run testsuite: %s" % self.run_id_
        log.info("run test cases[%d]: %s" % (self.run_id_,start))

        ## collect test cases
        final_collected = self.collect_testcases()
        log.info("finally collected: %s" % len(final_collected))
        run_results = {}

        with Executor(5) as p:
            ## submit concurrent jobs
            for test in final_collected:
                test_file = test[0]
                collected = test[1]
                if test_file in exclude: continue
                print "process job: %s" % test_file
                log.info("submitting job for :%s" % test_file)
                if test_file in no_xdist:
                    run_results[test_file] = p.submit(self.run_testcases,os.path.join(self.testdir_,test_file))
                else:
                    if collected > 1000:
                        run_results[test_file] = p.submit(self.run_testcases,os.path.join(self.testdir_,test_file),nums=self.num_cup * 3)
                    elif collected > 200:
                        run_results[test_file] = p.submit(self.run_testcases,os.path.join(self.testdir_,test_file),nums=self.num_cup * 2)
                    else:
                        run_results[test_file] = p.submit(self.run_testcases,os.path.join(self.testdir_,test_file),nums=self.num_cup)

            ##collect job result
            log.info("collect jobs results")
            for k,v in run_results.iteritems():
                res = v.result()
                log.debug("got result for :%s" % k)
                run_results[k] = res

        end = datetime.now()
        log.info("end run :%s" % str(end - start))
        log.info("run results: %s" % run_results)

        return run_results

    def collect_testcases(self):
        """ collect all test cases from testdir_.
        - if collected_testcases_ is empty
        - collect python file from testdir_
        - filter out any successful run
        - run concurrent "pytest --collectonly" on each of python test file.
        - remove python file without test cases.

        """

        if len(self.collected_testcases_) == 0:
            log.info("collecting test cases: %s" % self.testdir_)
            results = {}
            start = datetime.now()
            today = date.today().isoformat()
            with Executor(5) as p:
                #for root,dirs,files in os.walk(self.testdir_):
                for item in os.listdir(self.testdir_):
                    if os.path.isfile(os.path.join(self.testdir_,item))\
                            and item.endswith(".py") and not item.startswith("_"):
                            """ process each file"""
                            test_file = os.path.join(self.testdir_,item)
                            ##filter out already passed test file.
                            test_name = ntpath.basename(test_file)
                            ## check test name already had good result here 
                            if os.path.exists(os.path.join(self.release_dirs_['good'],"%s_%s.html" % (test_name,today))):
                                log.info("test run already passed for today: %s" % test_name)
                                continue

                            ## only loop root folder
                            if os.path.exists(test_file):
                                print "collect: %s" % test_file
                                job = p.submit(_collect_test_cases,test_file)
                                results[test_name] = job

                log.info(" === collecting test cases === ")
                for k,v in results.iteritems():
                    print "collecting: ", k
                    collected,tests = v.result()
                    if collected > 0:
                        self.collected_testcases_.append([k,collected,tests])

            report = [(i[0],i[1]) for i in self.collected_testcases_]
            print "report: %s" % report
            end = datetime.now()
            log.info("collect :%s, results: %s" % (end - start,report))

        return self.collected_testcases_

