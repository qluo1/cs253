#!/bin/bash

## generate rdsdata into local json snapshot file.

CUR_DIR=${PWD##}

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python
echo $CUR_DIR
## source sybase env
source  /gns/mw/dbclient/sybase/oc/openclient-15.5.0.ESD9.v01/SYBASE.sh

exec $GNS_PYTHON $CUR_DIR/scripts/ruleServer.py

