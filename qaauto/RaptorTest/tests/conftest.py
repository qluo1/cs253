## setup python path
import os
import sys
import pytest
import inspect
import os.path

PROJ_DIR = os.getenv('BASE_DIR')
LOG_DIR = os.path.join(PROJ_DIR,"logs")

## 
for path in (PROJ_DIR,):
    if path not in sys.path:
        sys.path.append(path)

pytest_plugins = ['config.service.report.plugin']

from datetime import date
import logging
logging.basicConfig(filename=os.path.join(LOG_DIR,"tests_%s.log" % date.today()),
                    level =logging.INFO,
                    format = "%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s")

## setup GNS python path
GNS_PTH =os.path.join(PROJ_DIR,"config/gns.pth")
assert os.path.exists(GNS_PTH)
with open(GNS_PTH,"r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("/gns") and line not in sys.path:
            assert os.path.exists(line)
            sys.path.append(line)

###############################################
## test generator for class based test cases
##
###############################################
def pytest_generate_tests(metafunc):
    """ test generator for class based test scenarios.

    generate test cases based on scenarios configured inside test class

    scenarios is a list of dict, key must match test function parameters.

    """
    if metafunc.cls and hasattr(metafunc.cls,'scenarios'):
        #
        argnames = []
        argvalues = []
        for scenario in metafunc.cls.scenarios:
            argnames = scenario.keys()
            argvalues.append([scenario[name] for name in argnames])

        # import pytest;pytest.set_trace()
        if argnames and argvalues:
            metafunc.parametrize(argnames,argvalues,scope='class')
        else:
            pytest.skip("skip test")

@pytest.fixture
def expect(request):
    def do_expect(expr, msg=''):
        if not expr:
            _log_failure(request, msg)
            return False
        return True
    return do_expect

@pytest.fixture
def reporter(request):
    def append_to_report(line):
        if line is not None:
            node = request.node
            if not hasattr(node, '_csv_report'):
                node._csv_report = []
            node._csv_report.append(line)
    return append_to_report

def _log_failure(request, msg=''):
    import logging
    log = logging.getLogger()
    calling_function_name = request.function.__name__
    calling_stack = None
    for stack_trace in inspect.stack():
        (filename, line, funcname, contextlist) =  stack_trace[1:5]
        if funcname == calling_function_name:
            calling_stack = stack_trace
    if calling_stack is None:
        calling_stack = inspect.stack()[2]

    # get filename, line, and context
    (filename, line, funcname, contextlist) =  calling_stack[1:5]
    filename = os.path.basename(filename)
    context = contextlist[0]
    # format entry
    msg = '%s\n' % msg if msg else ''
    entry = '>%s%s%s:%s\n--------' % (context, msg, filename, line)
    log.error(entry)
    # add entry 
    node = request.node
    if not hasattr(node, '_failed_expect'):
        node._failed_expect = []
    node._failed_expect.append(entry)

@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    outcome = yield
    import logging
    log = logging.getLogger()
    report = outcome.get_result()
    if (call.when == 'call') and hasattr(item, '_csv_report'):
        report._csv_report = item._csv_report
#        report.sections.append(('CSV result', item._csv_report))
    if (call.when == "call") and hasattr(item, '_failed_expect'):
        summary = 'Failed Expectations:%s' % len(item._failed_expect)
        item._failed_expect.append(summary)
        if not report.longrepr:
#            report.longrepr = str(report.longrepr) + '\n--------\n' + ('\n'.join(item._failed_expect))
#        else:
#            report.longrepr = '\n'.join(item._failed_expect)
            report.longrepr = ''
        report.outcome = "failed"
