
from scapy.all import *
import ahd_client
#import ahd_client_temp as ahd_client
from time import sleep
import unittest
import test_client_cfg
import csv

# valid values, for reference
#for side in ['1','3']:
#for execCond in ['0', '2', '4', '6', '8']:
#for shortSellFlag in ['0','5','7']:
#for propBrokerageClass in ['0','9']:
#for cashMarginCode in ['0','2','4']:
#for stabArbCode in ['0','6','8']:
#for ordAttrClass in ['1','2']:
#for suppMemberClass in ['0','1']:


class CancelOrders(unittest.TestCase):

    def setUp(self):
        self.baseTestName = 'Cancel Test Case: '
        self.baseTestCase = 'Cancel'
        self.loadSeqNum = False
        self.saveSeqNum = True
        self.testSequenceNum  = 1
        if not hasattr(self, 'beenHere'):
            fileName = 'sample.log/seqNum-VIRTU.csv'
            #fileName = 'sample.log/seqNum-DUMMY.csv'
            #self.A = ahd_client.getApp('sim_Dummy.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_Dummy1.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_colo1.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_VIRTU.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_newDUMMY.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_newJPXCLIENT.py')
            self.A = ahd_client.getApp('sim_newVIRTU.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_newCOLOCO1', 'sample.log')
            #self.A = ahd_client.getApp('sim_VIRTU10g.py', 'sample.log')
            if self.loadSeqNum :
                self.A.start(fileName)
            else :
                self.A.start()
            self.beenHere = True

    def test_Cancel(self):

        time.sleep(1.0)
        testCaseName = '%s - From New' % self.baseTestName
        testCase = self.baseTestCase + 'FromNew'
        self.A.info(testCaseName)
        time.sleep(1.0)
        self.sendMessages(testCase)

        time.sleep(1.0)
        testCaseName = '%s - From New-Mod' % self.baseTestName
        testCase = self.baseTestCase + 'FromNewMod'
        self.A.info(testCaseName)
        time.sleep(1.0)
        self.sendMessages(testCase)

        self.A.showStats()
        self.A.testReport()
        self.postTestVerification()

        if self.saveSeqNum : 
            self.A.saveSeqNum()

    def sendMessages ( self, testCase ) :

        for side in ['1','3']:
            for origExecCond in ['0', '2', '4', '6', '8']:
                for shortSellFlag in ['0','5','7']:
                    for origPriceType in ['Market', 'Limit'] :
                        # omit short sell, exempt / buy combo
                        if not shortSellFlag == '0' and \
                                side == '3':
                            continue
                        # omit funari / market combo
                        if origExecCond == '6' and \
                                origPriceType == 'Market' :
                            continue

                        # omit short sell / market combo
                        if shortSellFlag == '5' and \
                                origPriceType == 'Market' :
                            continue
                        # omit IOC order for new > mod > cxl
                        if origExecCond == '8' and testCase == 'CancelFromNewMod' :
                            continue

                        noBasePrice = 1
                        origPrice = None
                        origQty = 0
                        symbol = ''
                        basePrice = 0
                        while noBasePrice == 1:
                            symbol = random.choice(self.A.securities.keys())
                            basePrice = self.A.securities[symbol].basePrice
                            if basePrice != 0 :
                                if self.A.securities[symbol].minPrice > basePrice or\
                                        self.A.securities[symbol].maxPrice < basePrice :
                                    continue
                                if self.A.securities[symbol].lotSize != 0 and self.A.securities[symbol].maxLot != 0:
                                    if self.A.securities[symbol].maxLot > 50 :
                                        origQty = self.A.securities[symbol].lotSize * ( random.choice( range( 50, ( self.A.securities[symbol].maxLot  ) ) ) )
                                        if origPriceType == 'Market' :
                                            origPrice = ' 0           '
                                            noBasePrice = 0
                                        else :
                                            origPrice = basePrice + self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(basePrice) * ( random.choice(range(-10, 10)))
                                            if self.A.securities[symbol].minPrice > origPrice or\
                                                    self.A.securities[symbol].maxPrice < origPrice :
                                                origPrice = basePrice
                                            noBasePrice = 0

                        new = self.A.sendNewOrder(symbol, origQty, side=side, price=origPrice, execCond=origExecCond, shortSellFlag=shortSellFlag )
                        time.sleep(0.1)
                        self.A.expect(new, 'NewOrderAcceptanceNotice', 0000, 
                                testCaseName=testCase + 'NewOrder(symbol=%s/qty=%d/side=%s/price=%s/execCond=%s/shortSellFlag=%s)' % (symbol, origQty, side, origPriceType, origExecCond, shortSellFlag ) , serialNum=self.testSequenceNum )
                        # set intProcessing
                        orderid = new.getfieldval('IntProcessing')

                        # set current execCond, price, qty        
                        currentExecCond = origExecCond
                        currentPriceType = origPriceType
                        # set price = 0 for market price = price for limit
                        currentPrice = 0
                        if origPriceType == 'Limit' :
                            currentPrice = origPrice
                        currentQty = origQty
                        time.sleep(0.1)

                        self.testSequenceNum += 1
                                
                        currentPriceQtyExecCond='(%s/%d/%s)' % ( currentPriceType, currentQty, currentExecCond)
                        
                        # in case of new > mod > cxl
                        if testCase == 'CancelFromNewMod' :
                            # send multiple modifies                    
                            for i in range(10):
                                currentPriceQtyExecCond='(%s/%d/%s)' % ( currentPriceType, currentQty, currentExecCond)
                                newPrice = None
                                newQty = 0
                                newExecCond=''
                                
                                while newQty == 0 :
                                    newQty = self.A.securities[symbol].lotSize * random.choice(range(1,10))
                                    newPriceType = random.choice(['Market', 'LimitMinus', 'LimitPlus'])
                                    newExecCond=random.choice(['0', '2', '4', '6', ' ']) # no IOC

                                if newPriceType == 'Market' :
                                    newPrice = ' 0           '
                                else :
                                    newPrice = 0
                                    if currentPriceType == 'Market' :
                                        newPrice = basePrice + self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(basePrice) * ( random.choice(range(-10, 10)))
                                        if newPrice < 0:
                                            newPrice = basePrice

                                    elif newPriceType == 'LimitMinus' :
                                        newPrice = currentPrice - self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(origPrice) * random.choice(range(1, 10))
                                        if newPrice < 0:
                                            newPrice = currentPrice 

                                    elif newPriceType == 'LimitPlus' :
                                        newPrice = currentPrice + self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(origPrice) * random.choice(range(1, 10))

                                sleep(0.1)

                                mod = self.A.sendMod(orderid, symbol, qty=newQty, price=newPrice, execCond=newExecCond )

                                newPriceQtyExecCond='(%s/%d/%s)' % ( newPriceType, newQty, newExecCond)

                                # check funari with no price
                                if newExecCond == '6' and \
                                        newPriceType == 'Market' :
                                    self.A.expect(mod, 'ModRegistrationError', None, testCaseName=testCase + 'Modify %s  -> %s' % ( currentPriceQtyExecCond, newPriceQtyExecCond ), serialNum=self.testSequenceNum )

                                # check funari order with no price
                               # ( case execCond no change from last time (funari)

                                elif newExecCond == ' ' and \
                                        currentExecCond == '6' and \
                                        newPriceType == 'Market' :
                                    self.A.expect(mod, 'ModRegistrationError', None, testCaseName=testCase + 'Modify %s  -> %s' % ( currentPriceQtyExecCond, newPriceQtyExecCond ), serialNum=self.testSequenceNum )

                                ## check if IOC (currently Raw accepts modify to IOC)
                                # elif newExecCond == '8' :
                                #    self.A.expect(mod, 'ModRegistrationError', None, testCaseName=testCase )
                                # check if price is out of range
                                elif ( newPriceType != 'Market' and \
                                        ( newPrice > self.A.securities[symbol].maxPrice or \
                                          newPrice < self.A.securities[symbol].minPrice)):
                                    self.A.expect(mod, 'ModRegistrationError', '8018', testCaseName=testCase + 'Modify %s  -> %s' % ( currentPriceQtyExecCond, newPriceQtyExecCond ), serialNum=self.testSequenceNum  )

                                # check if qty is less than 0
                                elif newQty >= currentQty :
                                    self.A.expect(mod, 'ModRegistrationError', '8048', testCaseName=testCase + 'Modify %s  -> %s' % ( currentPriceQtyExecCond, newPriceQtyExecCond ), serialNum=self.testSequenceNum  )

                                # check short sell with no price
                                elif shortSellFlag == '5' and \
                                        newPriceType == 'Market' :
                                    self.A.expect(mod, 'ModRegistrationError', '8023',testCaseName=testCase + 'Modify %s  -> %s' % ( currentPriceQtyExecCond, newPriceQtyExecCond ), serialNum=self.testSequenceNum  )

                                else :
                                    self.A.expect(mod, 'ModResultNotice', None, testCaseName=testCase + 'Modify %s  -> %s' % ( currentPriceQtyExecCond, newPriceQtyExecCond ), serialNum=self.testSequenceNum  )
                                    currentQty -= newQty
                                    currentExecCond = newExecCond
                                    currentPriceType = newPriceType
                                    if newPriceType != 'Market' :
                                        currentPrice = newPrice
                                    else :
                                        currentPrice = 0

                                self.testSequenceNum += 1
                       
                        # send cancel 
                        cxl = self.A.sendCancel(orderid, symbol)
                        # expect cxl reject in case of IOC
                        if currentExecCond == '8' :
                            self.A.expect(cxl,'CancelRegistrationError', None, testCaseName=testCase + 'Cancel %s' % currentPriceQtyExecCond, serialNum=self.testSequenceNum )
                        else :
                            self.A.expect(cxl,'CancelResultNotice', None, testCaseName=testCase + 'Cancel %s' % currentPriceQtyExecCond, serialNum=self.testSequenceNum )

                        self.testSequenceNum +=1

    def postTestVerification(self):
        self.assertEqual((self.A.msgSeqNumErrorsFound, self.A.acceptSeqNumErrorsFound, 
                          self.A.execSeqNumErrorsFound, self.A.numErrorsFound), 
                         (False, False, False, 0))

       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
