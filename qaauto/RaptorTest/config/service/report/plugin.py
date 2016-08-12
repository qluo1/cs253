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
from . send_email import send_email
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
           default="Raptor Test Report Page",help="pytest html report title.")

    group.addoption('--htmlreportdesc', action="store", dest="htmlreportdesc",
           default="description",help="pytest html report description.")

    group.addoption('--htmlreportapp', action="store", dest="htmlreportapp",
           default="JP RAW Raptor",help="pytest html report application name.")

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
            report,summary = self._generate_report(self.test_reports)
            report_attrs['total'] = summary['count']
            report_attrs['pass'] = summary['Pass']
            report_attrs['fail'] = summary['fail']
            report_attrs['error'] = summary['error']
            report_attrs['rate'] = float(summary['Pass']) / summary['count']
            heading = self._generate_heading(report_attrs)
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
            ## sendout the email report
            import base64
            send_email(report_attrs, summary, base64.b64encode(output))
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
        """ generate report -- class level .

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

        success_count = 0
        failure_count = 0
        skipped_count = 0
        error_count = 0

        # each result row item
        rows = []
        cls_summary = []
        for cid,rs in _reps.items():

            rows_module = []
            # report details
            np = nf = ne = ns = 0
            for tid,r in enumerate(rs):
                ret = self._generate_report_test(cid, tid, r)
                rows_module += ret['rows']
                np += ret['pass']
                nf += ret['fail']
                ne += ret['error']

            # clean up test_case name
            names = [x.replace(".py", "") for x in r.nodeid.split("::")[0:2] if x != '()']
            names[0] = names[0].replace("/", '.')

            row = self.REPORT_CLASS_TMPL % dict(
                style = ne > 0 and 'errorClass' or nf > 0 and 'failClass' or 'passClass',
                desc = names[0],
                count = np+nf+ne+ns,
                Pass = np,
                fail = nf,
                error = ne,
                skip = ns,
                #cid = 'c%s' % (cid+1),
                cid = cid,
                cls_count = len(rs),
            )
            cls_summary.append(
                {
                    'name': names[0],
                    'count': np+nf+ne+ns,
                    'pass': np,
                    'fail': nf,
                    'error': ne
                }
            )
            rows_module.insert(0, row)
            rows += rows_module

            success_count += np
            failure_count += nf
            skipped_count += ns
            error_count += ne

#            # report details
#            for tid,r in enumerate(rs):
#                self._generate_report_test(rows, cid, tid, r)

        import logging
        log = logging.getLogger()
        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
            count = str(success_count+failure_count+error_count+skipped_count),
            Pass = str(success_count),
            fail = str(failure_count),
            skip = str(skipped_count),
            error = str(error_count),
        )
        return (report,dict(class_summary=cls_summary,count=success_count+failure_count+error_count,Pass=success_count,fail=failure_count,error=error_count))

    def _generate_report_test(self, cid,tid,report):
        """ generate report -- function level

       i.e. row case

        """
        # e.g. 'pt1.1', 'ft1.1', etc, used by UI javascript
        rows = []

        tid = (report.outcome =='passed' and 'p' or 'f') + 't%s.%d' % (cid,tid+1)
        tname = report.nodeid.split("::")[-1]
        doc = ""
        desc = 'name: %s <br> line:%s, <br> duration(secs): %.3f' % \
            (tname, str(report.location[1]),hasattr(report,"duration") and report.duration or 0)

        ## capture error if any
        out = ''
        for name,content in report.get_sections("Captured stderr"):
            if content:
                out += content

        ## capture csv output
        csv_report = []
        teststep_num = 0
        npass = 0
        nfail = 0
        nskip = 0
        nerror = 0

        import StringIO
        import csv

        if hasattr(report, '_csv_report'):
            teststep_num = len(report._csv_report)
            for idx, line in enumerate(report._csv_report):
                s = StringIO.StringIO(line)
                reader = csv.reader(s, delimiter = ',') 
                for fields in reader:
                    sid = ('pt' if fields[4] == 'OK' else 'ft') + '_' + tid + '_' + str(idx)
                    row = self.REPORT_TEST_STEP_TMPL % dict (
                        teststep = fields[0],
                        requestmsg = fields[1],
                        receivedmsg = fields[2],
                        expectedmsg = fields[3],
                        passes = fields[4],
                        errormsg = fields[7],
                        Class = 'hiddenRow',
                        sid = sid,
                        style = 'passCase' if fields[4] == 'OK' else 'failCase'
                    )
                    if fields[4] == 'OK':
                        npass += 1
                    elif fields[4] == 'FAIL':
                        nfail += 1
                    rows.append(row)

        assert npass + nfail == teststep_num

        ## Error if test failed but all already executed test step succeeded
        if report.outcome != 'passed' and npass == teststep_num:
            nerror = 1

        tmpl = self.REPORT_TEST_WITH_OUTPUT_TMPL

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
            n_count = teststep_num,
            n_pass = npass,
            n_fail = nfail,
            n_error = nerror,
            n_skip = 0,
        )
        rows.insert(0, row)
        ret = {
            'rows': rows,
            'pass': npass,
            'fail': nfail,
            'count': teststep_num,
            'error': nerror
        }
        return ret



    def _generate_ending(self):
        return self.ENDING_TMPL
