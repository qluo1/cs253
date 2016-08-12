""" extract rds snapshot into json data.

convert Account, Control, Product into json data.

using multiprocessing to speedup.

"""
import logging
import os
from collections import defaultdict
from datetime import datetime
from pprint import pprint

import cfg
## local settings
from conf import settings
import pyparsing

import ujson as json
from concurrent.futures import ProcessPoolExecutor as Executor
## local 
from rds_record_parser import parse_rds_line

log = logging.getLogger("extract_snapshot")

KNOWN_RDS_FILES = [
                   'RdsAccountPropertyInfo',
                   'RdsTransactionalProduct',
                   'RdsFlowTradingControlLimit',
                  ]

def _parse_file(root, file):
    """ parsing individual rds file."""
    ret = []
    log.info("parsing file: %s" % file)

    try:
        with open(os.path.join(root,file),"r") as f:
            for ln in f:
                ln = ln.strip()
                if ln == "": continue
                try:
                    ret.append(parse_rds_line(ln))
                except pyparsing.ParseException,e:
                    log.error("line: %s" % ln)
                    log.exception(e)
                    continue
        return ret
    except Exception,e:
        print e
        log.exception(e)

class RDSSnapshotGenerator:

    def __init__(self,input,output):
        """ """
        assert os.path.isdir(input) and os.path.isdir(output)
        self.root_ = input
        self.out_ = output

        self.executor_ = Executor(5)

        self.folders_ = [f for f in os.listdir(self.root_) \
                            if f.startswith("Snapshot_") and \
                            os.path.isdir(os.path.join(self.root_,f))]

    def load_snapshots(self):
        """ """
        for folder in self.folders_:
            ## skip already generated snapshot
            out_file = os.path.join(self.out_,folder) + ".json"
            if os.path.exists(out_file):
                continue
            print "generating :%s" % folder
            data = {}
            files = os.listdir(os.path.join(self.root_,folder))
            for file in files:
                rds_name = file.split("_")[0]
                if rds_name in KNOWN_RDS_FILES:
                    future = self.executor_.submit(_parse_file, os.path.join(self.root_,folder),file)
                    data[rds_name] = future

            ## wait for result 
            for k,v in data.iteritems():
                data[k] = v.result()

            with open(out_file,"w") as f:
                json.dump(data, f)
        ## shutdown
        self.executor_.shutdown()


from datetime import datetime
def gen_snapshot(env="PME_RDS"):
    """ generate snapshot for env."""
    ## find the snapshot folder
    assert env in settings.OM2_PATHS

    _root = os.path.join(settings.OM2_PATHS[env],"snapshot")

    _output = os.path.join(settings.GENRATED_SNAPSHOTS,env)
    if not os.path.exists(_output):
        os.makedirs(_output)

    start = datetime.now()
    generator = RDSSnapshotGenerator(_root,_output)
    generator.load_snapshots()

    end = datetime.now()
    print("completed generate %s in %s" % (env, end-start))


if __name__ == "__main__":
    """ run daily snapshot generating."""

    logging.basicConfig(filename = os.path.join(settings.LOG_DIR,"extract_snapshot.log"),
                        level = logging.INFO)

    ### generate snapshot for PME.
    print "gen PME_RDS"
    gen_snapshot("PME_RDS")

    ### generate snapshot for PPE.
    print "gen PPE_RDS"
    gen_snapshot("PPE_RDS")
