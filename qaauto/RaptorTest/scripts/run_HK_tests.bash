#!/bin/bash

# Get the current directory through local_vars
# Setting_module also through dir

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $CUR_DIR/../env/local_vars.qfixservice

if [[ ! -d $BASE_DIR/logs ]];
then
    mkdir $BASE_DIR/logs
fi
if [[ ! -d $BASE_DIR/data ]];
then
    mkdir $BASE_DIR/data
fi

exec $GNS_PYTHON $BASE_DIR/lib/pytest_boot.py ../tests/HK/  -v 

