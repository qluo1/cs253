#!/bin/bash

CUR_DIR=${PWD##}

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python

## setup ORBIX env
source  /home/eqtdata/runtime/orbixServices/etc/bin/omaorbix_env

#export SETTINGS_MODULE=settings.oma

## cleanup cached seq num.
rm $CUR_DIR/tmp/*

exec $GNS_PYTHON $CUR_DIR/scripts/omaPyService.py $@

