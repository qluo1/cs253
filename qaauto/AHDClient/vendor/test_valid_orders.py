
from scapy.all import *
#import ahd_client
import ahd_client_temporarily
from time import sleep
import unittest
import test_cfg

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
        if not hasattr(self, 'beenHere'):
            self.A = ahd_client.getApp('sim_cfg21.py', 'sample.log')
            self.A.start()
            self.beenHere = True

            self.symbol = '1301'
            self.price = None
            self.qty = 1000

            if 'symbol' in test_cfg.CFG:
                self.symbol = test_cfg.CFG['symbol']
            if 'price' in test_cfg.CFG:
                self.price = test_cfg.CFG['price']
            if 'qty' in test_cfg.CFG:
                self.qty = test_cfg.CFG['qty']


            print 'Input: symbol=%s, price=%s, qty=%d' %(self.symbol, self.price, self.qty)


    def test_1_valid_orders(self):
        #symbol = '1301'
        #qty = 1000
        #price = None

        for side in ['1','3']:
            for execCond in ['0', '2', '4', '6', '8']:
                for shortSellFlag in ['0','5','7']:
                    for propBrokerageClass in ['0', '9']:
                        for cashMarginCode in ['0', '2', '4']:
                            for stabArbCode in ['0', '6', '8']:
                                for ordAttrClass in ['1', '2']:
                                    for suppMemberClass in ['0', '1']:

                                        # omit short sell, exempt / buy combo 
                                        if not shortSellFlag == '0' and \
                                                side == '3':
                                                # not side == '3':
                                            continue

                                        # omit funari / market combo
                                        if execCond == '6' and \
                                                self.price in [None, ' 0           ']:
                                            continue

                                        # omit short sell / market combo
                                        if shortSellFlag == '5' and \
                                                self.price in [None, ' 0           ']:
                                            continue

                                        m = self.A.sendNewOrder(self.symbol, self.qty, side, 
                                                                self.price, 
                                                                execCond, shortSellFlag,
                                                                propBrokerageClass,
                                                                cashMarginCode, stabArbCode,
                                                                ordAttrClass, suppMemberClass)

                                        if not propBrokerageClass == '0':
                                            m = self.A.expect(m, 'NewOrderAcceptanceError', None)

                                        elif not cashMarginCode == '0':
                                            m = self.A.expect(m, 'NewOrderAcceptanceError', None)

                                        elif not stabArbCode == '0':
                                            m = self.A.expect(m, 'NewOrderAcceptanceError', None)

                                        elif not ordAttrClass == '1':
                                            m = self.A.expect(m, 'NewOrderAcceptanceError', None)

                                        elif not suppMemberClass == '0':
                                            m = self.A.expect(m, 'NewOrderAcceptanceError', None)

                                        #elif execCond=='2':
                                        #    m = self.A.expect(m, 'NewOrderAcceptanceError', None)

                                        sleep(0.1)

        self.A.testReport()
        self.A.showStats()
        self.postTestVerification()
        

    def postTestVerification(self):
        self.assertEqual((self.A.msgSeqNumErrorsFound, self.A.acceptSeqNumErrorsFound, 
                          self.A.execSeqNumErrorsFound, self.A.numErrorsFound), 
                         (False, False, False, 0))

       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
