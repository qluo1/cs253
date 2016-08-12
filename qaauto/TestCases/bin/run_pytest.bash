#!/bin/bash
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BIN_DIR/.."

PROJ_DIR=${PWD}

GNS_PYTHON=/gns/mw/lang/python/python-2.7.2-gns.03/bin/python

exec $GNS_PYTHON $PROJ_DIR/libs/pytest.py "$@"

