import os
import sys
import time
from pprint import pprint

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.join(CUR_DIR,"..")

if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from QuoteManager import QuoteManager

def test_one():

    manager =QuoteManager()

    assert manager.init()

    time.sleep(3)
    manager.subscribe("BHP.AX")
    manager.subscribe("3PL.AX")
    manager.subscribe("WOW.AX")
    time.sleep(3)

    bhp =  manager.getQuote("BHP.AX")
    assert bhp and 'bid' in bhp and 'ask' in bhp
    pprint(bhp)
    wow = manager.getQuote("WOW.AX")
    assert wow and 'bid' in wow and 'ask' in wow
    pprint(wow)

    csl =  manager.getQuote("CSL.AX")
    assert csl and 'error' in csl 
    pprint(csl)

    pl = manager.getQuote("3PL.AX")
    assert pl and 'bid' in pl and 'ask' in pl
    pprint(pl)
    manager.shutdown()

