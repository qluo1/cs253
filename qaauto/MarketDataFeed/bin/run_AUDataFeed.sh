#!/bin/bash
CUR_DIR=${PWD##}
echo $CUR_DIR

export SETTINGS_MODULE=settings.FTE

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python
exec $GNS_PYTHON $CUR_DIR/scripts/marketQuoteService.py "QA_FTE"


