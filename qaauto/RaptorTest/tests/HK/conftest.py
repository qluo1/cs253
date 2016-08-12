""" setup fixture for RAPTOR.

"""
import os
import pytest

## setup local python path
import config.service.cfg

from tests.fix_util import FIXMsgListener
from tests.dc_util import DCMsgListener
from tests.HK.zcmd_util import Zcmd

dc_session = 'DC_RAPTOR'

@pytest.fixture(scope='session')
def fix(request):
    return FIXMsgListener()


@pytest.fixture(scope='session')
def dc(request):
    return DCMsgListener(dc_session)

@pytest.fixture(scope='session')
def zcmd(request):
    return Zcmd()
