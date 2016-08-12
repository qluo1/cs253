import os
import sys

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CUR_DIR)

if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)


import localcfg
