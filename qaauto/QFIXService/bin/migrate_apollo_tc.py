#!/gns/mw/lang/python/python-2.7.2-gns.03/bin/python
""" migrate apollo test cases to json.  """
import os
import sys
import argparse
import traceback
## local 
import importlib
from pprint import pprint
import json
import subprocess
import logging

logging.basicConfig(filename="generate_test.log",
                    level=logging.INFO,
                    format='%(levelname)s %(asctime)s %(module)s %(process)d %(threadName)s %(message)s')

## local path
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CUR_DIR)
WORK_DIR  = os.path.join(CUR_DIR,"works")
MIGRATED_DIR = os.path.join(PROJ_DIR,"migrated")
OM2_DIR = os.path.join(CUR_DIR,"om2")

def _exec_script(script,**kw):
    """ """
    log = kw.get("log",False)
    proc = subprocess.Popen(script,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    )
    stdout_val,stderr_val = proc.communicate()
    if log:
        print stdout_val
        print stderr_val

def run_autogen_perl(perl_script, workdir):
    """ """
    assert os.path.exists(perl_script)
    _exec_script("%s %s" % (perl_script, workdir))

def run_combined_bash(bash_script,tc_name):
    """ """
    assert os.path.exists(bash_script)
    _exec_script("%s %s" % (bash_script,tc_name))

from FetchMarketData import run_gen_price
import Sybase

def list_of_tc():
    """list of test case spreadsheet should be working. """

    tcs = []
    with open(os.path.join(CUR_DIR,"list_of_tc.txt"),"r") as f:
       for line in f:
           ln = line.strip()
           if ln.startswith("#"): continue
           tcs.append(ln)
    return tcs



def gen_tc_name(indir):
    """ """
    indir = os.path.abspath(indir)

    tcs = list_of_tc()

    for root,dirs,files in os.walk(indir):
        #for file in files:
        #    #if file.startswith("TC_") and file.endswith(".xls"):
        #    print file
        #    if file in tcs:
        #        print "yield",file
        #        yield (file, file.split(".")[0][3:])

        for tc in tcs:
            if tc in files:
                yield(tc,tc.split(".")[0][3:])
            else:
                print "tc: %s not found" % tc


def gen_apollo_test_cases(indir,outdir,tc):
    """
    indir is where TC_xxx.xls can be found.
    outdir is where python test cases being generated.
    """
    tc_root = os.path.abspath(indir)
    output = os.path.abspath(outdir)
    if not os.path.exists(tc_root):
        print "input dir not found: %s" % tc_root
        exit(1)
    tc_file = os.path.join(tc_root,"TC_%s.xls" % tc)
    if not os.path.exists(tc_file):
        print "tc not found: %s" % tc_file
        exit(1)

    print "processing tc file: %s" % tc_file
    if run_gen_price(tc_file,output):
        ## link this spradsheet for generating tests
        symbol_link_file = os.path.join(output,"TC.xls")
        #print symbol_link_file,os.path.islink(symbol_link_file)
        if os.path.exists(symbol_link_file) and os.path.islink(symbol_link_file):
            os.unlink(symbol_link_file)
        os.symlink(tc_file,symbol_link_file)

        run_autogen_perl(os.path.join(CUR_DIR,"AutoGenerate.pl"),output)

        run_combined_bash(os.path.join(CUR_DIR,"generateTestPlan_migrated.bash"),tc)

def migrate_test_cases(indir,outdir,targetId,compId):
    """ """
    ## validation
    apollo_path=os.path.abspath(indir)
    output_path = os.path.abspath(outdir)

    assert os.path.exists(apollo_path)
    assert os.path.exists(output_path)


    for root,dirs,files in os.walk(apollo_path):
        print root, dirs
        if root not in sys.path:
            sys.path.append(root)

        for file in files:
            if file.startswith("CombinedUnitTests_") and file.endswith(".py"):
                #print file

                ## import module
                module_name = file.split(".")[0]
                os.environ['targetId'] = targetId
                os.environ['compId'] = compId

                try:
                    mod = importlib.import_module(module_name)
                except Exception,e:
                    print "import error: %s" % e
                    continue
                tests =  mod.create("mytest","myengine",1)
                json.dump(tests,open(os.path.join(output_path,"%s.json"%module_name.split("_")[-1]),"w"),indent=4)
                #pprint(tests)
                print "migrated:%s" % file


def cleanup_folder(folder):
    """ """
    folder = os.path.abspath(folder)
    assert os.path.exists(folder)
    for root,dirs,files in os.walk(folder):

        for file in files:
            if os.path.islink(file):
                os.unlink(os.path.join(folder,file))
            else:
                os.remove(os.path.join(folder,file))

if __name__ == "__main__":
    """ """

    if OM2_DIR not in sys.path:
        sys.path.append(OM2_DIR)

    parser = argparse.ArgumentParser()
    ## generate apollo python test cases from spreadsheet
    parser.add_argument("--input",help="TC spreadsheet input dir")
    parser.add_argument("--output",default=WORK_DIR,help="output dir")
    parser.add_argument("--tc",default="None",type=str,help="spread sheet test case.")

    ## migrate python test case into JSON
    parser.add_argument("--targetId",default="APOLLO",type=str,help="session targetId")
    parser.add_argument("--senderId",default="TEST",type=str,help="session senderId")
    parser.add_argument("--migrated", default=MIGRATED_DIR,type=str,help="migrated output path")

    args = parser.parse_args()

    if args.input:
        ## run migration
        if 'SenderCompID' not in os.environ:
            os.environ['SenderCompID'] = args.senderId
        if 'TargetCompID' not in os.environ:
            os.environ['TargetCompID'] = args.targetId

        if args.tc  != "None":
            ## clean up everything
            gen_apollo_test_cases(args.input,args.output,args.tc)
            migrate_test_cases(args.output,args.migrated,args.targetId,args.senderId)
        else:
            ## looping input to migrate all spreadsheet
            for file, tc in gen_tc_name(args.input):
                try:
                    ## clean up everything
                    cleanup_folder(args.output)
                    gen_apollo_test_cases(args.input,args.output,tc)
                    migrate_test_cases(args.output,args.migrated,args.targetId,args.senderId)
                except Exception as e:
                    print "skip: %s, error: %s" % (tc,e)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print "%s, tb: %s" % (e, traceback.extract_tb(exc_traceback))

    else:
        parser.print_help()




