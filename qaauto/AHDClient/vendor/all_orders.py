
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


class AllOrderParams(unittest.TestCase):

    def setUp(self):
        self.A = ahd_client.getApp()
        self.A.start()


    def test_1_all_orders(self):
        symbol = '1301'
        qty = 1000
        price = None

        for side in ['1','3']:
            for execCond in ['0', '2', '4', '6', '8']:
                for shortSellFlag in ['0','5','7']:
                    for propBrokerageClass in ['0','9']:
                        for cashMarginCode in ['0','2','4']:
                            for stabArbCode in ['0','6','8']:
                                for ordAttrClass in ['1','2']:
                                    for suppMemberClass in ['0','1']:
                                        
                                        self.A.sendNewOrder(symbol, qty, side, price, 
                                                       execCond, shortSellFlag,
                                                       propBrokerageClass,
                                                       cashMarginCode, stabArbCode,
                                                       ordAttrClass, suppMemberClass)
                                        sleep(0.5)


        self.postTestVerification()
        

    def postTestVerification(self):
        self.assertEqual(self.A.msgSeqNumErrorsFound, False)
        self.assertEqual(self.A.acceptSeqNumErrorsFound, False)
        self.assertEqual(self.A.execSeqNumErrorsFound, False)
        self.assertEqual(self.A.numErrorsFound, 0)
       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
