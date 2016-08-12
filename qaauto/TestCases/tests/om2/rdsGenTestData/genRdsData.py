""" generate RDS test data for rds related testing.

this module generate RDS test dta. there are two ways for it to be used:

    - 1) run dynamically
    - 2) run based on local snapshot i.e.Test_Data.pk, Test_Data.pk, Test_RdsAccountPropertyInfo.out
      Test_RdsAccountPropertyInfo need to be manually loaded into PME/OM2/RDS.
     ./start_rdeshmfeeder.ksh --exit-after-load --input-data-file /home/eqtdata/runtime/preprod/asia/aucesmf/d48965-004.dc.gs.com/prodmirror/Test_RdsAccountPropertyInfo.out

for QAE/PPE, as RDS is running, there is no need to manual load test data. test run should insert RDS data during test run.

To generate a new set of test data, run the script standalone as main.

Note: RDS Hermes command can only insert/update, no delete.
"""
import os
CUR_DIR = os.path.dirname(os.path.abspath(__file__))

from rdsRepositoryCatalog import rdsRepositoryCatalog
from rdsHelper import *

RdsAccountPropertyInfo = rdsRepositoryCatalog["tables"]["RdsAccountPropertyInfo"]

test_data_template = {
        'subMarket': "N/A",
        'instrumentClass': "UNKNOWN_IC",
        'instrumentSubClass': "UNKNOWN_ISC",
        'serviceOfferingEnum': "INSTITUTIONAL_SO",
    }

""" test data for rds reference data.

1) test_data will be used for populate rds reference data via Hermes command.
2) test_data will be used for test cases for validation.
3) test_data key will be used for for test case as a reference for validation data.

"""
import json
import cPickle as pickle
## generate random value for reg data
## 'A' or 'P'
import random
rand_capacity = lambda: random.choice(["A","P"])
## bool '0', '1'
rand_wholesale = lambda: random.choice(["0","1"])
## numeric string
rand_str = lambda: str(random.randint(1000,5000))
## firm orderOrigin can be None
rand_str_none = lambda: random.choice([None, rand_str()])

## try to load from local snapshot or generate a new one
try:
    test_data = json.load(open(os.path.join(CUR_DIR,"Test_Data.json")))
except IOError:
    print "generating new rds test data"
    test_data = {
            ## oeid without SI
            'oeid':
                {
                "accountSynonym": "1001",
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": "P",
                "ASICORIGINOFORDER":"1001",
                "ASICWHOLESALEINDICATOR":rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'oeid_a':
                {
                "accountSynonym": "1001A",
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": "0",
                "PARTICIPANTCAPACITY": 'A',
                "ASICORIGINOFORDER":"1001A",
                "ASICWHOLESALEINDICATOR":rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            ## oeid with SI override
            'si_oeid_asx':
                {
                "accountSynonym": '1002',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "ASXDirect",
                "ASICORIGINOFORDER":"1002",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_asxonly':
                {
                "accountSynonym": '1003',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "ASXOnly",
                "ASICORIGINOFORDER":"1003",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_bp':
                {
                "accountSynonym": '1004',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPrice",
                "ASICORIGINOFORDER":"1004",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_bpmq':
                {
                "accountSynonym": '1005',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQty",
                "ASICORIGINOFORDER":"1005",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_bpmquni':
                {
                "accountSynonym": '1006',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyUni",
                "ASICORIGINOFORDER":"1006",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_bpmqnolit':
                {
                "accountSynonym": '1007',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyNoLit",
                "ASICORIGINOFORDER":"1007",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_bpmqnolituni':
                {
                "accountSynonym": '1008',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyNoLitUni",
                "ASICORIGINOFORDER":"1008",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            'si_oeid_bpmv':
                {
                "accountSynonym": '1009',
                "accountSynonymType": 'CLIENT_OE_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinValue",
                "ASICORIGINOFORDER":"1009",
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID":rand_str(),
                },
            ## starid
            'starid':
                {
                "accountSynonym": '2001T',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY":rand_capacity(),
                "ASICORIGINOFORDER":rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            ## startId look back to OEID
            'starid_oeid':
                {
                "accountSynonym": '3001T',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "GSOEALIAS": 1001,
               },

            'si_starid_asx':
                {
                "accountSynonym": '2002',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "ASXDirect",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_asxonly':
                {
                "accountSynonym": '2003',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "ASXOnly",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_bp':
                {
                "accountSynonym": '2004',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPrice",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_bpmq':
                {
                "accountSynonym": '2005',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQty",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_bpmquni':
                {
                "accountSynonym": '2006',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyUni",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_bpmqnolit':
                {
                "accountSynonym": '2007',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQytNoLit",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_bpmqnolituni':
                {
                "accountSynonym": '2008',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyNolitUni",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_starid_bpmv':
                {
                "accountSynonym": '2009',
                "accountSynonymType": 'STAR_CUSTOMER_ID_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinValue",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },

            'xref':
                {
                "accountSynonym": 'SAM',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_xref_asx':
                {
                "accountSynonym": 'SAM2',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "ASXDirect",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },

            'si_xref_asxonly':
                {
                "accountSynonym": 'SAM3',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "ASXOnly",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_xref_bp':
                {
                "accountSynonym": 'SAM4',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPrice",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },

            'si_xref_bpmq':
                {
                "accountSynonym": 'SAM5',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQty",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_xref_bpmquni':
                {
                "accountSynonym": 'SAM6',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyUni",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },

            'si_xref_bpmqnolit':
                {
                "accountSynonym": 'SAM7',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyNoLit",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_xref_bpmqnolituni':
                {
                "accountSynonym": 'SAM8',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQtyNoLitUni",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },

            'si_xref_bpmv':
                {
                "accountSynonym": 'SAM9',
                "accountSynonymType": 'IOS_ACCOUNT_AST',
                "UCPKEY": "1003",
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinValue",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },

            'tam':
                {
                "accountSynonym": 'TAMSAM',
                "accountSynonymType": 'ACCOUNT_NAME_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            'si_tam_bpmq':
                {
                "accountSynonym": 'TAMSAMBP',
                "accountSynonymType": 'ACCOUNT_NAME_AST',
                "UCPKEY": rand_str(),
                "PARTICIPANTCAPACITY": rand_capacity(),
                "SORSTRATEGYOVERRIDE": "BestPriceMinQty",
                "ASICORIGINOFORDER": rand_str(),
                "ASICWHOLESALEINDICATOR": rand_wholesale(),
                "ASICINTERMEDIARYID": rand_str(),
                },
            ## GSET bucket agency
            "bucket_xref_gsv":
                {
                "accountSynonym": "GSV",
                "accountSynonymType": "IOS_ACCOUNT_AST",
                "UCPKEY": "0",
                "PARTICIPANTCAPACITY": "A",
                "ASICORIGINOFORDER": "105689",
                "ASICWHOLESALEINDICATOR": "0",
                "ASICINTERMEDIARYID": "0",
                },
            ## GSET bucket principal
            "bucket_xref_gpr":
                {
                "accountSynonym": "GPR",
                "accountSynonymType": "IOS_ACCOUNT_AST",
                "UCPKEY": "1111",
                "PARTICIPANTCAPACITY": "P",
                "ASICORIGINOFORDER": None,
                "ASICWHOLESALEINDICATOR": "0",
                "ASICINTERMEDIARYID": "0",
                },

            ## default
            'default': {
                        "PARTICIPANTCAPACITY": 'A',
                       },
            'default_oeid_junk': {
                        "PARTICIPANTCAPACITY": 'A',
                        'ASICORIGINOFORDER': 'junk',
                       },

            'default_p': {
                        "PARTICIPANTCAPACITY": 'P',
                        "UCPKEY": "1111",
                       }
            }

## data used for insert into rds db
try:
    rds_data = json.load(open(os.path.join(CUR_DIR,"Test_Data_RDS.json")))
except IOError:
    print "generating new rds test data"

    rds_data = {}
    ## load exisitn snapshot or generate one            
    for k,v in test_data.iteritems():
        ## ignore default
        if k.startswith("default"): continue

        if 'GSOEALIAS' not in v.keys():
            ## enrich asicOrderOrigin for client if no OEID
            if v['PARTICIPANTCAPACITY'] == 'A' and v["accountSynonymType"] != 'CLIENT_OE_ID_AST':
                v['ASICORIGINOFORDER'] = rand_str()
            else:
                v['UCPKEY'] == rand_str_none()

        rds_data[k] = []
        for _k,_v in v.iteritems():
            ## ignore  
            if _k in ("accountSynonym", "accountSynonymType"): continue
            ## for CHIA being removed on IS:6010-1616062,Bondarava, Tanya,[AUCEL] Remove redundant Reg Data for CHIA market
            for market in ('SYDE',):
                test = test_data_template.copy()
                ## duplicate for each records
                test['accountSynonym'] = v['accountSynonym']
                test['accountSynonymType'] = v['accountSynonymType']
                test['market'] = market
                test['propertyName'] = _k
                if _v != None: test['propertyValue'] = _v
                rds_data[k].append(test)


def data_to_command(action, data, session):
    """ convert test data into df command. """

    assert action in ("Insert","Update","Delete")
    #import pdb;pdb.set_trace()
    assert isinstance(data,dict)
    cmd = "%s df AccountPropertyInfo " % action
    for k,v in data.iteritems():
        assert k in data, "key: %s not found in data: %s" % (k,data)
        assert k in RdsAccountPropertyInfo["columns"] , "key not in RdsAccountPropertyInfo: :%s" % k
        col = RdsAccountPropertyInfo["columns"][k]
        v = data[k]

        if col['type'] == 'string':
            cmd += "[ %s String \"%s\" ] " %(k,str(v))
        elif col['type'] == "ubyte" and  'enum' in col:
            enum = col['enum']
            cmd += "[ %s Int \"%s\" ] " % (k, lookup_enum(enum,v))
        else:
            assert False, "unexpected k: %s, %s" % (k,v)

    command = {
        'cmd': 'updateSharedMemoryFeederRecord',
        'handle': 'updateSharedMemoryFeederRecord',
        'argumentVector': [
            {'arg': cmd },
        ]
        }
    return command



__all__ = [
        'rds_data',
        'data_to_command',
        'test_data',
]


if __name__ == "__main__":
    """ persist rds_data into local file, which can be loaded into OM2/RDS. """
    import os
    import sys
    CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJ_ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(CUR_DIR)))
    print PROJ_ROOT
    SCRIPT_DIR = os.path.join(PROJ_ROOT,"scripts")
    if SCRIPT_DIR not in sys.path:
        sys.path.append(SCRIPT_DIR)
    import cfg
    from conf import settings

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--rds", help="update rds",action="store_true")
    args = parser.parse_args()

    if args.rds:
        print "persist generated and update rds"
    else:
        print "presist generated rds data. no update. "
    ## persist test data
    json.dump(test_data,open(os.path.join(CUR_DIR,"Test_Data.json"),"wb"),indent=4,sort_keys=True)
    json.dump(rds_data,open(os.path.join(CUR_DIR,"Test_Data_RDS.json"),"wb"),indent=4,sort_keys=True)
    ## 
    import zerorpc
    server = zerorpc.Client(settings.ORDER_API_URL)

    ## persist rds data
    with open(os.path.join(CUR_DIR,"Test_RdsAccountPropertyInfo.out"),"w") as f:
        for k, data in rds_data.iteritems():
            assert isinstance(data,list)
            for test in data:
                cmd = data_to_command("Insert",test,settings.RDS_REQ)
                if args.rds:
                    ack = server.hermes_cmd(**cmd)
                    assert "Success" == ack['status']
                #import pdb;pdb.set_trace() 
                f.write(cmd['argumentVector'][0]['arg'] + "\n")


