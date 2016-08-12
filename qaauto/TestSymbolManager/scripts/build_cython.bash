#!/bin/bash 
## compile viking depth service into so.
cython vikingDepthService.pyx
cython vikingOrder.pyx
cython vkOrderTracker.pyx


PYTHON_INCLUDE=/gns/mw/lang/python/python-2.7.2-gns.03/include/python2.7
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -o vikingOrder.so vikingOrder.c -I$PYTHON_INCLUDE
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -o vkOrderTracker.so vkOrderTracker.c -I$PYTHON_INCLUDE
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -o vikingDepthService.so vikingDepthService.c -I$PYTHON_INCLUDE
