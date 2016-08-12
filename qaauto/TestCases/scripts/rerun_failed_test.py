###############################################
## re-run on failed test cases for pytest 
## note: this is a pytest plugin
## 
###############################################
from _pytest.runner import runtestprotocol

def pytest_runtest_protocol(item, nextitem):
    """
    """
    # pytest.set_trace()
    item.ihook.pytest_runtest_logstart(
        nodeid=item.nodeid, location=item.location,
    )

    if item.session.config.option.reruns is not None:
        reruns = item.session.config.option.reruns
    else:
        reruns = 0
    for i in range(reruns+1): # ensure at least one run of each item
        reports = runtestprotocol(item, nextitem=nextitem, log=False)
        # break if setup and call pass
        if reports[0].passed and reports[1].passed:
            break

        # break if test marked xfail
        evalxfail = getattr(item, '_evalxfail', None)
        if evalxfail:
            break

    for report in reports:
        if report.when in ("call"):
            if i > 0:
                report.rerun = i
        item.ihook.pytest_runtest_logreport(report=report)

    # pytest_runtest_protocol returns True
    return True

def pytest_report_teststatus(report):
    """ adapted from
        https://bitbucket.org/hpk42/pytest/src/a5e7a5fa3c7e/_pytest/skipping.py#cl-170
    """
    # pytest.set_trace()
    if report.when in ("call"):
        if hasattr(report, "rerun") and report.rerun > 0:
            if report.outcome == "failed":
                return "failed", "F", "FAILED"
            if report.outcome == "passed":
                return "rerun", "R", "RERUN"

# command line options
def pytest_addoption(parser):
    group = parser.getgroup("rerunfailures", "re-run failing tests to eliminate flakey failures")
    group._addoption('--reruns',
        action="store",
        dest="reruns",
        type="int",
        default=0,
        help="number of times to re-run failed tests. defaults to 0.")

