#!/bin/bash

## generate rdsdata into local json snapshot file.

CUR_DIR=${PWD##}

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python
echo $CUR_DIR

exec $GNS_PYTHON $CUR_DIR/scripts/load_snapshot.py

