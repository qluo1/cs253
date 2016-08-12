# PYTHON_ARGCOMPLETE_OK
"""
pytest: unit and functional testing with Python.
"""
__all__ = ['main']


import sys

## setup pytest
GNS_PATHS = ("/gns/mw/lang/python/modules/2.7.2/py-1.4.25/lib/python2.7/site-packages",
"/gns/mw/lang/python/modules/2.7.2/pytest-2.7.1/lib/python2.7/site-packages")
for path in GNS_PATHS:
    if path not in sys.path:
        sys.path.append(path)


if __name__ == '__main__': # if run as a script or by 'python -m pytest'
    # we trigger the below "else" condition by the following import
    import pytest
    raise sys.exit( pytest.main())

## import 
from _pytest.config import main, UsageError, _preloadplugins, cmdline
from _pytest import __version__

_preloadplugins() # to populate pytest.* namespace so help(pytest) works
