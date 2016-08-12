import sys
from connection_info import DB_Conns, Sybase
from datetime import datetime


def test_query_regdata():
    """ """
    conn_info = DB_Conns['COMMON_S']
    conn_  = Sybase.connect(conn_info['server'],
                            'rds_ro',
                            'rds_ro',
                            conn_info['database'])

    print conn_info
    cur = conn_.cursor()

    start = datetime.now()

    sql = "select CodeSet, Code, Name,Value from tbl_RegValueRDS"
    cur.execute(sql)
    count = 0
    while True:
        ret =  cur.fetchmany(5)
        #print len(ret)
        sys.stdout.write(".")
        sys.stdout.flush()
        if len(ret) ==0:
            break

        count +=1

    cur.close()
    end =datetime.now()
    print count , end-start



if __name__ == "__main__":
    test_query_regdata()

