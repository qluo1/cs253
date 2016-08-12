""" report test results in html format
    Based on initial code from junit-xmll.
    reuse HTMLTestRunner html template
"""
__version__ = "0.0.2"

import py
import os
import re
import sys
import time
from datetime import datetime, timedelta, date
from collections import defaultdict
from xml.sax import saxutils
from . HTMLTestRunner import Template_mixin

## GS ETH api
from . helper import proxy,proxyBatch,URL

## split list into chunks
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def pytest_addoption(parser):
    """ pytest api hook. """
    group = parser.getgroup("terminal reporting")
    group.addoption('--htmlreport', action="store", dest="htmlpath",
           metavar="path", default="test_result.html",
           help="create html style report file at given path.")

    group.addoption('--htmlreporttitle', action="store", dest="htmlreporttitle",
           default="pytest html report title",help="pytest html report title.")

    group.addoption('--htmlreportdesc', action="store", dest="htmlreportdesc",
           default="pytest report description",help="pytest html report description.")

    group.addoption('--htmlreportapp', action="store", dest="htmlreportapp",
           default="app being tested",help="pytest html report application name.")

    group.addoption('--etch', action="store_true", dest="etch",
                    default=False,help="store test run to GS Etch.")

## configure/unconfigure htmlreport
def pytest_configure(config):
    """ pytest api hook. """
    htmlpath = config.option.htmlpath
    title = config.option.htmlreporttitle
    desc = config.option.htmlreportdesc
    app = config.option.htmlreportapp
    etch = config.option.etch
    # prevent opening xmllog on slave nodes (xdist)
    if htmlpath and not hasattr(config, 'slaveinput'):
        config._html = LogHTML(htmlpath,title,desc,app,etch)
        config.pluginmanager.register(config._html)

def pytest_unconfigure(config):
    """ pytest api hook. """
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


## logging
class LogHTML(Template_mixin):

    """ main logging class. """

    def __init__(self, logfile, title=None,desc=None,appName=None,etch=False):
        # logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.title = title or "pytest HTML test report"
        self.desc = desc or "pytest run generated HTML test report"
        self.appName = appName or "test app"

        self.test_reports = []
        self.internal_error = False
        self.etch = etch
        self.etch_results = []

    # pytest hooks
    def pytest_runtest_logreport(self, report):
        """
            process a test setup/call/teardown report relating to
            the respective phase of executing a test.
        """
        # ignore setup/teardown
        if report.when == "call":
            report.start = time.time()
            self.test_reports.append(report)

    def pytest_collectreport(self, report):
        """
            collector finished collecting.
            for each test case run.
        """
        # add failed on collection
        if not report.passed:
            self.test_reports.append(report)

    def pytest_internalerror(self, excrepr):
        """ called for internal errors. """
        data = py.xml.escape(excrepr)
        # unhandled
        # self.tests.append("internal error: %s" % data)
        self.internal_error = True

    def pytest_sessionstart(self, session):
        """ before session.main() is called. """
        self.suite_start_time = datetime.now()

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        """ whole test run finishes. """
        self.suite_stop_time = datetime.now()

        self.generateReport()

    def pytest_terminal_summary(self, terminalreporter):
        """ add additional section in terminal summary reporting. """
        if self.test_reports:
            terminalreporter.write_sep("-", "generated html file: %s" % (self.logfile))
        else:
            terminalreporter.write_sep("-", "no test report generated for the run!")

    # new implementation
    def generateReport(self):
        """ entry code for generating html report.  """

        # on error, test_reports is empty
        if not self.test_reports:
            return
        # write out test report to file
        with py.std.codecs.open(self.logfile,'w', encoding='utf-8') as out:

            report_attrs = self.getReportAttributes(self.test_reports)
            generator = 'HTMLReporter %s' % __version__
            stylesheet = self._generate_stylesheet()
            heading = self._generate_heading(report_attrs)
            report,summary = self._generate_report(self.test_reports)
            ending = self._generate_ending()
            output = self.HTML_TMPL % dict(
                title = saxutils.escape(self.title),
                generator = generator,
                stylesheet = stylesheet,
                heading = heading,
                report = report,
                ending = ending,
            )
            out.write(output.encode('utf8'))
            #import pdb;pdb.set_trace()
            start = time.time()

            if self.etch and len(self.etch_results) > 0:
                ## save to etch in batch
                batchName = str(datetime.now())
                batchTags = ['AUCEL',date.today().strftime("%Y%m%d")]
                batchId = proxy.createBatch(batchName,"Just Testing2",batchTags,len(self.etch_results))

                for items in chunks(self.etch_results,100):
                    for item in items:
                        item[-3] = batchId
                        proxyBatch.createTestResult(*item)

                    proxyBatch()
                print "total duration: ", time.time() - start


    def getReportAttributes(self,reports):
        """ Return report attributes as a list of (name, value).

        Override this to add custom attributes.

        """
        assert(reports)
        assert(type(reports) == list)

        startTime = str(self.suite_start_time)[:19]
        duration = str(self.suite_stop_time - self.suite_start_time)
        status = []
        success_count = len([i for i in reports if i.outcome=="passed"])
        failure_count = len([i for i in reports if i.outcome=="failed"])
        skipped_count = len([i for i in reports if i.outcome=="skipped"])
        error_count = 0

        rate = float(success_count * 100)/(success_count+failure_count) if (success_count+failure_count) else 0

        return {
            'title': self.title,
            'app'  : self.appName,
            'total': success_count + failure_count + skipped_count,
            'rate' : "{0:.0f}%".format(rate),
            'pass' : success_count,
            'fail' : failure_count,
            'skip' : skipped_count,
            'dtime': startTime,
            'duration': duration,
            'style': 'failClass' if failure_count > 0  else "passClass"
        }

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):

        report_attrs['description'] = saxutils.escape(self.desc)
        heading = self.SUMMARY_TMPL % dict(
            report_attrs
            )
        return heading

    def _generate_report(self, reports):
        """ generate report rows.

        i.e. row class

        """
        assert(reports)
        assert(type(reports) == list)

        # group by class level
        _reps = defaultdict(list)
        for i in reports:
            #import pdb;pdb.set_trace()
            cid = i.nodeid.split("::")[1] if len(i.nodeid.split("::")) > 1 else i.nodeid
            _reps[cid].append(i)

        # each result row item
        rows = []
        for cid,rs in _reps.items():

            ## for each class/func
            np = nf = ne = ns = 0
            for tid,r in enumerate(rs):
                if r.outcome == "passed": np += 1
                elif r.outcome == "failed": nf +=1
                elif r.outcome =="skipped": ns +=1
                else:
                    pass

            # clean up test_case name
            names = [x.replace(".py", "") for x in r.nodeid.split("::")[0:2] if x != '()']
            names[0] = names[0].replace("/", '.')

            row = self.REPORT_CLASS_TMPL % dict(
                style = ne > 0 and 'errorClass' or nf > 0 and 'failClass' or 'passClass',
                desc = "->".join(names),
                count = np+nf+ne+ns,
                Pass = np,
                fail = nf,
                error = ne,
                skip = ns,
                #cid = 'c%s' % (cid+1),
                cid = cid
            )
            rows.append(row)

            # report details
            for tid,r in enumerate(rs):
                self._generate_report_test(rows, cid, tid, r)


        success_count = len([i for i in reports if i.outcome=="passed"])
        failure_count = len([i for i in reports if i.outcome=="failed"])
        skipped_count = len([i for i in reports if i.outcome=="skipped"])
        error_count = 0

        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
            count = str(success_count+failure_count+error_count+skipped_count),
            Pass = str(success_count),
            fail = str(failure_count),
            skip = str(skipped_count),
            error = str(error_count),
        )
        return (report,dict(count=success_count+failure_count+error_count,Pass=success_count,fail=failure_count,error=error_count))

    def _generate_report_test(self, rows, cid,tid,report):
        """ generate row under each top level class or func.

       i.e. row case

        """
        # e.g. 'pt1.1', 'ft1.1', etc, used by UI javascript

        tid = (report.outcome =='passed' and 'p' or 'f') + 't%s.%d' % (cid,tid+1)
        tname = report.nodeid.split("::")[-1]
        doc = ""
        desc = 'name: %s <br> line:%s, <br> duration(secs): %.3f' % \
            (tname, str(report.location[1]),hasattr(report,"duration") and report.duration or 0)

        out = ''
        ## capture stdout, error if any
        #sec = dict(report.sections)
        #import pdb;pdb.set_trace()
        for capname in ('out', 'err'):
            for name,content in report.get_sections("Captured std%s" % capname):
                if content:
                    out += content
        if report.longrepr:
            out += str(report.longrepr)
        ## store test report to GS ETCH
        #if self.etch and report.outcome != "skipped":
        #    ## log test results to gs ETH
        #    store_result = [
        #        cid + "." + tname,      ## test name
        #        "Just Testing2",    ## namespace
        #        1,                  ## tests
        #        0,                  ## error
        #        1 if report.outcome == 'failed' else 0, ## failure
        #        report.start * 1000 ,                     #start
        #        (report.start + report.duration) * 1000 , #stop
        #        out, #stdout
        #        '',  #stderr
        #        '__SLang__NUll__String',
        #        '__SLang__NUll__String',
        #        '__SLang__NUll__String',
        #        '__SLang__NUll__String',
        #        '__SLang__NUll__String',
        #        '__SLang__NUll__String', # batchId
        #        [get_om_buildId(),],     #buildid
        #        ['pytest',get_current_om_version()] #tags
        #    ]
        #    self.etch_results.append(store_result)

        tmpl = len(out) > 0 and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id = tid,
            output = saxutils.escape(out),
        )
        # pytest.set_trace()
        n = 0 if report.outcome =='passed' else 1 if report.outcome == "failed" else 3 if report.outcome =="skipped" else 2

        row = tmpl % dict(
            tid = tid,
            Class = (n == 0 and 'hiddenRow' or 'none'),
            style = n == 2 and 'errorCase' or (n == 1 and 'failCase' or (n ==3 and 'skipCase' or 'passCase')),
            desc = desc,
            script = script,
            status = self.STATUS[n],
        )
        rows.append(row)


    def _generate_ending(self):
        return self.ENDING_TMPL
