""" GS Sybase connection info

collection of GS sybase connection
all connection info exposed as DB_Conns

"""
import copy
import sys
sys.path.insert(0,"/gns/mw/lang/python/modules/2.7.2/sybase-0.39/lib/python2.7/site-packages")
import Sybase

QA_source = {
    'server': 'APEQTSQ1',
    'user': 'regmap_dbo',
    'pwd': 'regmap_db0',
    #'user': 'rds_ro',
    #'pwd': 'rds_ro',
}

QA_target_primary = {
    'server': 'APEQTQ01',
#    'user': 'rds_ro',
#    'pwd': 'rds_ro',
    'user': 'rds_dbo',
    'pwd': 'rds_dbo',
}

QA_target_secondary = {
    'server': 'APEQTQ02',
    'user': 'rds_ro',
    'pwd': 'rds_ro',
}

DB_names = {
    'PRODUCT': 'product',
    'CONTROL': 'TradingControls',
    'COMMON' : 'trading_tech_common',
    'CLIENT' : 'qa_client_db',
}


## build up db connections
##
DB_Conns = {}

for k,v in DB_names.items():

    conn_name = k + "_S"
    DB_Conns[conn_name] = copy.deepcopy(QA_source)
    DB_Conns[conn_name]['database'] =v

    conn_name = k + "_T1"
    DB_Conns[conn_name] = copy.deepcopy(QA_target_primary)
    DB_Conns[conn_name]['database'] =v

    conn_name = k + "_T2"
    DB_Conns[conn_name] = copy.deepcopy(QA_target_secondary)
    DB_Conns[conn_name]['database'] =v


__all__ = ['DB_Conns']

if __name__ == "__main__":
    import pprint
    pprint.pprint(DB_Conns)

