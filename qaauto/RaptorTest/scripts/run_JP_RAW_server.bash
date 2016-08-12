#!/bin/bash

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

echo "Raptor test server started"
$GNS_PYTHON $BASE_DIR/config/service/relay_boost.py $@ >> $BASE_DIR/logs/service.log 2>&1 &
sleep 3
$GNS_PYTHON $BASE_DIR/config/service/ahd_service.py $@ >> $BASE_DIR/logs/service.log 2>&1 &
$GNS_PYTHON $BASE_DIR/config/service/zcmd_service.py $@ >> $BASE_DIR/logs/service.log 2>&1 &
$GNS_PYTHON $BASE_DIR/config/service/dc_service.py $@ >> $BASE_DIR/logs/service.log 2>&1 &

