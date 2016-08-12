#!/bin/bash
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BIN_DIR/.."
CUR_DIR=$PWD

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python

#echo $CUR_DIR
## purge all order older than number of days.
DAYS=24

export SETTINGS_MODULE=settings.QAEAUCEA
$GNS_PYTHON $CUR_DIR/scripts/query_dss.py delete -d ${DAYS}

export SETTINGS_MODULE=settings.PPEAUCEA
$GNS_PYTHON $CUR_DIR/scripts/query_dss.py delete -d ${DAYS}

export SETTINGS_MODULE=settings.PMEAUCEA
$GNS_PYTHON $CUR_DIR/scripts/query_dss.py delete -d ${DAYS}

