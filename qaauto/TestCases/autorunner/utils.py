import shutil
import os
import logging
from datetime import datetime, date

log = logging.getLogger(__name__)

def check_resultlog(filepath):
    """ """
    assert os.path.exists(filepath)
    ##F tests/om2/order_trade_maq.py::Test_Order_Trade_MXQ_Lit::()::test_new_order_mxq_trade[True-chia-Buy]

    res = {'p': 0,
           'f': 0,
           'e': 0,
           'r': 0,
           ## collect all failed test cases.
           'failed': [],
           }
    with open(filepath,"r") as f:
        for line in f:
            if line.strip() == "": continue
            if line.startswith("."):
                res['p'] +=1
            elif line.startswith("R"):
                res['p'] +=1
                res['r'] +=1
            elif line.startswith("F"):
                res['f'] +=1
                res['failed'].append(line.split()[1])
            elif line.startswith("E"):
                res['e'] +=1
            elif line.startswith(" "):
                continue
            elif line.startswith("s"):
                continue
            else:
                raise ValueError("unknown line: %s" % line)
    return res

def extract_htmlreport(out):
    """ extract htmlreport name out of pytest terminal report/stdout. """
    lines = out.split(os.linesep)
    for line in lines:
        line = line.strip()
        if line.startswith("generated html"):
            return line.split(":")[1].strip()

def parse_test_cases(out):
    """ extract test cases out of pytest --collectonly """

    lines = out.split(os.linesep)
    res = []
    collected = 0
    for line in lines:
        if line.startswith("==="): continue
        if line.startswith("platform"): continue
        if line == "": continue
        if line.startswith("---"): continue
        if line.startswith("collected"):
            collected = int(line.split()[1])
            continue

        res.append(line.strip())

    return (collected,res)

def archive_resultlog(resultlog,run_dir):
    """ """
    assert os.path.exists(resultlog)
    today = date.today().isoformat()
    archive_dir = os.path.join(run_dir)
    if not os.path.exists(archive_dir):
       os.makedirs(archive_dir)

    target_dir = os.path.join(archive_dir,today)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    shutil.move(resultlog,target_dir)

from localcfg import OM2RULE_SERVICE_ENDPOINT
import zerorpc
import atexit

om2rule_service = zerorpc.Client(OM2RULE_SERVICE_ENDPOINT,heartbeat=30)
## cleanup at exit
atexit.register(om2rule_service.close)

def get_current_om_version(settings):
    """ query om2 release by local settings. """
    cur_setting = settings.split(".")[-1]
    res = om2rule_service.get_om2_version()
    assert res
    assert 'QAE' in res
    assert 'PPE' in res
    assert 'PME' in res

    for k,v in res.iteritems():
        if cur_setting.startswith(k):
            items = v.split("/")
            if items[8] == "omengineBin":
                assert items[7] == "hk"
                assert items[-1] == "omengine"
                return items[9]


from plumbum import local
fuser = local['fuser']

def current_running_test(runtime_dir, today=date.today().isoformat()):
    """ query runtime folder for today's running testcases.

    use lsof to check which is running python process.


    {'test1': {'runner': [1,2,3],
               'result': {'p': 1, 'f':3'}
                }
    """

    test_today = {}
    runtime_dir = os.path.abspath(runtime_dir)
    files = [f for f in os.listdir(runtime_dir)
                if os.path.isfile(os.path.join(runtime_dir,f))]

    completed_files = []
    if os.path.exists(os.path.join(runtime_dir,today)):
        completed_files = [f for f in os.listdir(os.path.join(runtime_dir,today))
                        if os.path.isfile(os.path.join(runtime_dir,today,f))]
    for file in files:
        #print file
        ref = file[len(today)+1:-4]
        if file.startswith(today):
            test_file = os.path.join(runtime_dir,file)
            test_today[ref] = {'runner': None}
            try:
                res = fuser[test_file]()
                test_today[ref]['runner'] = [int(i) for i in res.split()]
            except Exception,e:
                log.debug("fuser failed: %s" %e)

            test_today[ref]['result']  = check_resultlog(test_file)

    for file in completed_files:
        ref = file[len(today)+1:-4]
        test_file = os.path.join(runtime_dir,today,file)
        test_today[ref] = check_resultlog(test_file)

    return test_today




if __name__ == "__main__":
    """ unittest. """
    print get_current_om_version("settings.PPEAUCEA")

