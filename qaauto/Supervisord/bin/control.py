#!/gns/mw/lang/python/python-2.7.2-gns.03/bin/python

""" controled daily jobs

-- daily restart
-- cleanup logs

"""
## source gns supervisord
from common import *
from pprint import pprint
import supervisor.xmlrpc
import xmlrpclib
import urllib
import sys
import os
import time
from datetime import datetime,timedelta
import subprocess

home = "/home/eqtdata/runtime/qaauto"

p = xmlrpclib.ServerProxy('http://127.0.0.1',
        transport=supervisor.xmlrpc.SupervisorTransport(
            None, None,
            'unix:///tmp/supervisor.sock'))


def restart_process(name, **kw):
    """ """
    desc = kw.get("desc")
    sleep = kw.get("sleep",10)

    ## logging desc and time
    if desc:
        print "restart prodcess:%s at:%s, desc:%s" % (name,datetime.now(),desc)

    cur_state = p.supervisor.getProcessInfo(name)

    if cur_state['statename'] == "RUNNING":
        p.supervisor.stopProcess(name)

    p.supervisor.startProcess(name)
    ## wait for process start complete
    time.sleep(sleep)

def purge_session_cache():
    """ purge web session cookie """
    print "purge session."
    db = redis.Redis(host="localhost",port=6379,db=10)
    db.flushdb()

def purge_mongo_db():
    """ """

    run_purge = os.path.join(home,"TestCases","bin","run_purge_mongo.bash")
    if os.path.exists(run_purge):
        subprocess.call([run_purge])

def cleanup_old_logs(days=3):
    """ clean up logs order than """
    folders = [
                os.path.join(home,"IvComService","logs"),
                os.path.join(home,"IvComService","tmp"),
                os.path.join(home,"OM2DBService","logs"),
                os.path.join(home,"TestSymbolManager","logs"),
                os.path.join(home,"MarketDataFeed","logs"),
                os.path.join(home,"OM2RuleService","logs"),
                os.path.join(home,"QFIXService","logs"),
               ]

    now = datetime.now()
    for folder in folders:
        for root,dirs,files in os.walk(folder):
            for file in  files:
                fn =os.path.join(root,file)
                if os.path.isfile(fn):
                    timestamp = datetime.fromtimestamp(os.path.getmtime(fn))
                    if now - timedelta(days=days) > timestamp:
                        try:
                            print "delete file: ",fn
                            os.remove(fn)
                        except OSError,e:
                            print "failed to remove file",fn, e

if __name__ == "__main__":

    print "start at: %s " % datetime.now()
    cleanup_old_logs()
    print p.supervisor.getState()

    ############################
    ## restart sybase service.
    restart_process("OM2DBService", desc="restart OM2DBService", sleep=60)
    ## restart market data, wait 15 mins for prime instrument cached.  
    restart_process("AU_MarketData", desc="restart market data", sleep=60*5)
    ## restart market data, wait 15 mins for prime instrument cached.  
    restart_process("AU_LiveMarketData", desc="restart market data", sleep=60*5)

    ###########################
    ## restart IvComService
    restart_process("QAEAUCEA", desc="restart QAE IvComServie", sleep=60)
    restart_process("PPEAUCEA", desc="restart PPE IvComServce", sleep=60)
    restart_process("PMEAUCEA", desc="restart PME IvComServce", sleep=60)

    ## restart imagelive servcie
    restart_process("QAEAUCEA_app", desc="restart QAE app")
    restart_process("PPEAUCEA_app", desc="restart PPE app")
    restart_process("PMEAUCEA_app", desc="restart PME app")

    ## restart symbolManager, wait for 5 mins 
    restart_process("SymbolManager", desc="restart symbol manager",sleep=60)
    ## restart symbolManager
    restart_process("RuleService", desc="restart rule service")

    pprint(p.supervisor.getProcessInfo("AU_MarketData"))
    pprint(p.supervisor.getProcessInfo("SymbolManager"))
    print "end at : %s" % datetime.now()

    purge_mongo_db()
