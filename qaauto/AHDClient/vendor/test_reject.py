
from scapy.all import *
import ahd_client
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


class Reject_Scenarios(unittest.TestCase):

    def setUp(self):
        if not hasattr(self, 'beenHere'):
            self.A = ahd_client.getApp()
            self.A.start()
            self.beenHere = True

            self.symbol = '1301'
            self.price = None
            self.qty = 1000

            if 'symbol' in test_cfg.CFG:
                self.symbol = test_cfg.CFG['symbol']
            if 'price' in test_cfg.CFG:
                self.symbol = test_cfg.CFG['price']
            if 'qty' in test_cfg.CFG:
                self.symbol = test_cfg.CFG['qty']


            print 'Input: symbol=%s, price=%s, qty=%d' %(self.symbol, self.price, self.qty)


    def test_1_rejects(self):
        # wrong cash margin
        m = self.A.sendNewOrder(self.symbol, self.qty, cashMarginCode='2')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # invalid cash margin
        m = self.A.sendNewOrder(self.symbol, self.qty, cashMarginCode='3')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # wrong prop brokerage class (prop)
        m = self.A.sendNewOrder(self.symbol, self.qty, propBrokerageClass='9')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # invalid prop brokerage class
        m = self.A.sendNewOrder(self.symbol, self.qty, propBrokerageClass='8')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # wrong stabArbCode
        m = self.A.sendNewOrder(self.symbol, self.qty, stabArbCode='6')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # invalid stabArbCode
        m = self.A.sendNewOrder(self.symbol, self.qty, stabArbCode='5')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # wrong ordAttrClass
        m = self.A.sendNewOrder(self.symbol, self.qty, ordAttrClass='2')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # invalid ordAttrClass
        m = self.A.sendNewOrder(self.symbol, self.qty, ordAttrClass='3')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # wrong suppMemberClass
        m = self.A.sendNewOrder(self.symbol, self.qty, suppMemberClass='1')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # invalid suppMemberClass
        m = self.A.sendNewOrder(self.symbol, self.qty, suppMemberClass='2')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # wrong short sell = 5 but no price
        m = self.A.sendNewOrder(self.symbol, self.qty, shortSellFlag='5')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # invalid short sell
        m = self.A.sendNewOrder(self.symbol, self.qty, shortSellFlag='8')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # funari no price
        m = self.A.sendNewOrder(self.symbol, self.qty, execCond='6')
        self.A.expect(m, 'NewOrderAcceptanceError', None)
        sleep(0.5)
        

        # wrong exchClass fukuoka
        #m = self.A.sendNewOrder(self.symbol, self.qty, exchClass='6')
        #self.A.expect(m, 'NewOrderAcceptanceError', None)
        #sleep(0.5)
        

        # invalid exchClass 
        #m = self.A.sendNewOrder(self.symbol, self.qty, exchClass='9')
        #self.A.expect(m, 'NewOrderAcceptanceError', None)
        #sleep(0.5)
        

        # wrong mktClass (convertible bond market)
        #m = self.A.sendNewOrder(self.symbol, self.qty, mktClass='12')
        #self.A.expect(m, 'NewOrderAcceptanceError', None)
        #sleep(0.5)
        

        # invalid mktClass (convertible bond market)
        #m = self.A.sendNewOrder(self.symbol, self.qty, mktClass='13')
        #self.A.expect(m, 'NewOrderAcceptanceError', None)
        #sleep(0.5)
        
        self.A.showStats()
        self.foundResponseErrors = self.A.testReport()
        self.postTestVerification()
        

    def postTestVerification(self):
        self.assertEqual(self.A.msgSeqNumErrorsFound, False)
        self.assertEqual(self.A.acceptSeqNumErrorsFound, False)
        self.assertEqual(self.A.execSeqNumErrorsFound, False)
        self.assertEqual(self.A.numErrorsFound, 0)
        self.assertEqual(self.foundResponseErrors, False)
       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
