""" setup fixture for GSET.

i.e. - AU Symbol service.
     - AU market depth/price service.

"""
import os
import pytest
import atexit

## setup local python path
import cfg
import zerorpc
import gevent

