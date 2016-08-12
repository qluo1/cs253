
from scapy.all import *
import ahd_client
from time import sleep
import unittest

# valid values, for reference
#for side in ['1','3']:
#for execCond in ['0', '2', '4', '6', '8']:
#for shortSellFlag in ['0','5','7']:
#for propBrokerageClass in ['0','9']:
#for cashMarginCode in ['0','2','4']:
#for stabArbCode in ['0','6','8']:
#for ordAttrClass in ['1','2']:
#for suppMemberClass in ['0','1']:


class BadOrderValues(unittest.TestCase):

    def setUp(self):
        self.A = ahd_client.getApp()
        self.A.start()

    def test_1(self):
        symbol = '1301'
        qty = 1000
        price = None
        
        side = '3'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'

        # bad symbol
        self.A.sendNewOrder('BADD', qty, side, price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad qty                                           
        self.A.sendNewOrder(symbol, 9999999999999, side, price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad side                                           
        self.A.sendNewOrder(symbol, qty, '2', price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad price
        self.A.sendNewOrder(symbol, qty, side, 999999999, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad execCond                                
        self.A.sendNewOrder(symbol, qty, side, price, 
                       '1', shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad shortSellFlag
        self.A.sendNewOrder(symbol, qty, side, price, 
                       execCond, '2',
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
                     
        # bad propBorkerClass                      
        self.A.sendNewOrder(symbol, qty, side, price, 
                       execCond, shortSellFlag,
                       '4',
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad cashMarginCode              
        self.A.sendNewOrder(symbol, qty, side, price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       '1', stabArbCode,
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad stabArbCode              
        self.A.sendNewOrder(symbol, qty, side, price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, '3',
                       ordAttrClass, suppMemberClass)
        sleep(0.5)
        
        # bad ordAttrClass
        self.A.sendNewOrder(symbol, qty, side, price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       '3', suppMemberClass)
        sleep(0.5)
        
        # bad suppMemberClass
        self.A.sendNewOrder(symbol, qty, side, price, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, '2')
        sleep(0.5)
        
        self.assertEqual(self.A.msgSeqNumErrorsFound, False)
        self.assertEqual(self.A.acceptSeqNumErrorsFound, False)
        self.assertEqual(self.A.execSeqNumErrorsFound, False)
        self.assertEqual(self.A.numErrorsFound, 0)
       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
