#!/bin/bash

CUR_DIR=${PWD##}

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python

exec $GNS_PYTHON $CUR_DIR/scripts/query_imagelive.py $@

