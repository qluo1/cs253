from scapy.all import *
import ahd_client
#import ahd_client_temporarily as ahd_client
#import ahd_client_temp as ahd_client
import ahd_client as ahd_client
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
        price = None

        side = '3'
        execCond = '0'
        shortSellFlag = '0'
        propBrokerageClass = '0'
        cashMarginCode = '0'
        stabArbCode = '0'
        ordAttrClass = '1'
        suppMemberClass = '0'
#####################################New Orders######################################
        #TESTCASENAME:1:New_Buy_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, side, 310,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Buy_Limit:Accept', 1)
        sleep(0.5)

        #TESTCASENAME:2:New_Buy_Market:Accept
        m=self.A.sendNewOrder(symbol, qty, side, price,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Buy_Market:Accept', 2)
        sleep(0.5)

        #TESTCASENAME:3:New_Sell_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Sell_Limit:Accept', 3)
        sleep(0.5)

        #TESTCASENAME:4:New_Sell_Market:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, price,
                       execCond, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Sell_Market:Accept', 4)
        sleep(0.5)

        #TESTCASENAME:5:New_ShortSell_Market:Reject:8023
        m=self.A.sendNewOrder(symbol, qty, 1, price,
                       execCond, 5,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceError', '8023', 'New_ShortSell_Market:Reject', 5)
        sleep(0.5)

        #TESTCASENAME:6:New_ShortSell_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       execCond, 5,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_ShortSell_Limit:Accept', 6)
        sleep(0.5)

        #TESTCASENAME:7:New_ShortSellExempt_Market:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, price,
                       execCond, 7,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_ShortSellExempt_Market:Accept', 7)
        sleep(0.5)

        #TESTCASENAME:8:New_ShortSell_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       execCond, 7,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_ShortSell_Limit:Accept', 8)
        sleep(0.5)
#########################################################################
##########################Various TIFs###################################
#########################################################################

        #TESTCASENAME:9:New_MarketOnClose:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, price,
                       4, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_MarketOnClose:Accept', 9)
        sleep(0.5)

        #TESTCASENAME:10:New_LimitOnClose:Accept
        m=self.A.sendNewOrder(symbol, qty, side, 310,
                       4, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_LimitOnClose:Accept', 10)
        sleep(0.5)

        #TESTCASENAME:11:New_Day_Order:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       0, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Day_Order:Accept', 11)
        sleep(0.5)

        #TESTCASENAME:12:New_Funari_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       6, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Funari_Limit:Accept', 12)
        sleep(0.5)

        #TESTCASENAME:13:New_Funari_Market:Reject
        m=self.A.sendNewOrder(symbol, qty, side, price,
                       6, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceError', '8024', 'New_Funari_Market:Reject', 13)
        sleep(0.5)

        #TESTCASENAME:14:New_Open_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       2, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Open_Limit:Accept', 14)
        sleep(0.5)

        #TESTCASENAME:15:New_Open_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, side, price,
                       2, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_Open_Limit:Accept', 15)
        sleep(0.5)

        #TESTCASENAME:16:New_IOC_Limit:Accept
        m=self.A.sendNewOrder(symbol, qty, 1, 310,
                       8, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_IOC_Limit:Accept', 16)
        sleep(0.5)

        #TESTCASENAME:17:New_IOC_Market:Accept
        m=self.A.sendNewOrder(symbol, qty, side, price,
                       8, shortSellFlag,
                       propBrokerageClass,
                       cashMarginCode, stabArbCode,
                       ordAttrClass, suppMemberClass)
        m = self.A.expect(m, 'NewOrderAcceptanceNotice', '0000','New_IOC_Market:Accept', 17)
        sleep(0.5)

#########################################################################
##########################Various TIFs###################################
#########################################################################

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
