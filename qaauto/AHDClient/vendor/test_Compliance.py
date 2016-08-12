from scapy.all import *
import ahd_client
#import ahd_client_temporarily as ahd_client
#import ahd_client_temp as ahd_client
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
	self.A = ahd_client.getApp('sim_newVIRTU.py', 'sample.log')
        self.A.start()

    def test_1(self):
        symbol = '1301'
        qty = 1000
        price = 289
        
        side = '3'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'

#################################################################################
#######################COMPLIANCE RESTRICTIONS RTLR3- 9437.T ####################
#################################################################################

        #TESTCASENAME:1:New_RTL_R3_BUY:Reject:8014
        m = self.A.sendNewOrder('9437', 1, side, 11500, 
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceError', '8014', 'New_RTL_R3_BUY:Reject', 1)
        sleep(0.5)
        
        #TESTCASENAME:2:New_RTL_R3_Sell:Reject:8015
        m = self.A.sendNewOrder('9437', 1, 1, 11500,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceError', '8015', 'New_RTL_R3_Sell:Reject' ,2)
        sleep(0.5)

        #TESTCASENAME:3:New_RTL_R3_ShortSell:Reject:8016
        m = self.A.sendNewOrder('9437', 1, 1, 11500,
                       execCond, 5,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceError', '8016', 'New_RTL_R3_ShortSell:Reject', 3)
        sleep(0.5)


        #TESTCASENAME:4:New_RTL_R3_ShortSellExempt:Reject:8017
        m = self.A.sendNewOrder('9437', 1, 1, 11500,
                       execCond, 7,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceError', '8017', 'New_RTL_R3_ShortSellExempt:Reject', 4)
        sleep(0.5)

#################################################################################
#######################COMPLIANCE RESTRICTIONS RTLX- 6753.T ####################
#################################################################################

        #TESTCASENAME:5:New_RTL_X_BUY:Reject:8014
        m = self.A.sendNewOrder('6753', 1000, side, 165,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceError', '8014', 'New_RTL_X_BUY:Reject', 5) 
        sleep(0.5)

        #TESTCASENAME:6:New_RTL_X_Sell:Accept
        m=self.A.sendNewOrder('6753', 1000, 1, 165,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_RTL_X_Sell:Accept', 6)
        sleep(0.5)

        #TESTCASENAME:7:New_RTL_X_ShortSell:Accept
        m=self.A.sendNewOrder('6753', 1000, 1, 165,
                       execCond, 5,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_RTL_X_ShortSell:Accept', 7)
        sleep(0.5)


        #TESTCASENAME:8:New_RTL_X_ShortSellExempt:Accept
        m=self.A.sendNewOrder('6753', 1000, 1, 165,
                       execCond, 7,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_RTL_X_ShortSellExempt:Accept', 8)
        sleep(0.5)

#################################################################################
#######################COMPLIANCE RESTRICTIONS RTLQ- 1334.T ####################
#################################################################################

        #TESTCASENAME:9:New_RTL_Q_BUY:Reject:8014
        m = self.A.sendNewOrder('8175', 1000, side, 115,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceError', '8014', 'New_RTL_Q_BUY:Reject', 9)
        sleep(0.5)

        #TESTCASENAME:10:New_RTL_Q_Sell:Accept
        m=self.A.sendNewOrder('8175', 1000, 1, 115,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_RTL_Q_Sell', 10)
        sleep(0.5)

        #TESTCASENAME:11:New_RTL_Q_ShortSell:Accept
        m=self.A.sendNewOrder('8175', 1000, 1, 117,
                       execCond, 5,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_RTL_Q_ShortSell', 11)
        sleep(0.5)


        #TESTCASENAME:12:New_RTL_Q_ShortSellExempt:Accept
        m=self.A.sendNewOrder('8175', 1000, 1, 115,
                       execCond, 7,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
	m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_RTL_Q_ShortSellExempt:Accept', 12)
        sleep(0.5)

#################################################################################
#######################END OF TEST CASES ########################################
#################################################################################

        self.A.testReport()
        self.postTestVerification()
        

    def postTestVerification(self):
        self.assertEqual((self.A.msgSeqNumErrorsFound, self.A.acceptSeqNumErrorsFound, 
                          self.A.execSeqNumErrorsFound, self.A.numErrorsFound), 
                         (False, False, False, 0))        

       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
