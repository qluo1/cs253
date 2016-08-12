import os
import json
import sys
from datetime import datetime
from pprint import pprint
import gevent
import zerorpc


c = zerorpc.Client(heartbeat=30)
#c.connect("tcp://localhost:20195")
#c.connect("tcp://d153578-002.dc.gs.com:20195")
c.connect("tcp://d48965-004.dc.gs.com:20195")

def test_api_get_test_symbol():


    pid = os.getpid()
    quote,cha_quote = c.get_test_symbol(pid)
    print quote,cha_quote


def test_api_get_quote():
    """ """
    quotes = c.get_symbol_quote("BHP.AX")
    pprint(quotes)

def test_api_get_tradable_symbol():

    pid = os.getpid()
    ## style 2 asx/chia
    quotes = c.get_tradable_symbol(pid,state="OPEN",build=True,style=2)
    pprint(quotes)
    #import pdb;pdb.set_trace()
    quotes = c.get_tradable_symbol(pid,state="OPEN",build=True,style=2)
    pprint(quotes)

def test_api_get_tradable_symbol_with_mxq():
    pid = os.getpid()
    ## wiht mxq
    quotes = c.get_tradable_symbol(pid,state="OPEN",build=True,style=2, with_mxq=True)
    pprint(quotes)
    ## without mxq
    quotes = c.get_tradable_symbol(pid,state="OPEN",build=True,style=2, with_mxq=False)
    pprint(quotes)


def test_load_symbols():

    pid = os.getpid()
    for x in range(600):
        quotes = c.get_tradable_symbol(pid,state="OPEN",build=True,style=2)
        assert quotes


