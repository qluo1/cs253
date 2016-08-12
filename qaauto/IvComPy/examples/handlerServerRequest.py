'''
    Author: Luiz Ribeiro (Melbourne Technology Division)
    December, 2015
'''

from IvComPy import *
from utils import convert
from handlerServerRequestInterface import HandlerServerRequestInterface
import random

class HandlerServerRequest(HandlerServerRequestInterface):
    '''
        Simple handler for the server that prints the inbound message and responds it
        with a different text and incremented number on field [int1]. This handler expecsts
        to always receive a TextMessage table
    '''

    def onWork(self, table, msg, msgId, posDup):
        print '%s received request message as table %s' % (self.name, table)
        print 'Message: %s ' % str(msg)

        rsp = {
            'text' : 'server response.',
            'text1': 'server text 1',
            'int1': msg['int1'],
        }

        return ('TextMessage', rsp)

