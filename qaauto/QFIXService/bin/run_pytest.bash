#!/bin/bash
## source sybase
source /gns/mw/dbclient/sybase/oc/openclient-15.5.0.ESD9.v01/SYBASE.sh

CUR_DIR=${PWD##}

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python
#echo $CUR_DIR

exec $GNS_PYTHON $CUR_DIR/libs/pytest_boot.py "$@"

