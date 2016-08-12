
from scapy.all import *
#import ahd_client_temp as ahd_client
import ahd_client as ahd_client
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


class TickSizeRandomOrders(unittest.TestCase):

    def setUp(self):
        self.baseTestName = 'TickSize Test Case (Random): '
        self.baseTestCase = 'TickSize_Random'
        self.loadSeqNum = False
        self.saveSeqNum = True
        self.modRepeat = 10
        self.testSequenceNum = 1 
        self.symbolForGroup0 = '7920'
        self.symbolForGroup1 = '4114'
        self.symbolForGroup2 = '4523'
 
        if not hasattr(self, 'beenHere'):
            #fileName = 'sample.log/seqNum-DUMMY.csv'
            fileName = 'sample.log/seqNum-VIRTU.csv'
            #self.A = ahd_client.getApp('sim_Dummy.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_VIRTU.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_colo2.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_VIRTU1g.py', 'sample.log')
            self.A = ahd_client.getApp('sim_newVIRTU.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_VIRTU10g.py', 'sample.log')
            self.A.start()
            self.beenHere = True

    def test_tickSizeRandom_orders(self):

        time.sleep(1.0)
        if self.symbolForGroup0 :
            testCaseName = '%s - Group0 - New' % self.baseTestName
            testCase = self.baseTestCase + 'ForGroup0New'
            self.A.info(testCaseName )
            time.sleep(1.0)
            self.sendMessages(testCase, self.symbolForGroup0, 0)

        time.sleep(1.0)
        if self.symbolForGroup1 :
            testCaseName = '%s - Group1 - New' % self.baseTestName
            testCase = self.baseTestCase + 'ForGroup1New'
            self.A.info(testCaseName)
            time.sleep(1.0)
            self.sendMessages(testCase, self.symbolForGroup1, 1)

        time.sleep(1.0)
        if self.symbolForGroup2 :
            testCaseName = '%s - Group2 - New' % self.baseTestName
            testCase = self.baseTestCase + 'ForGroup2New'
            self.A.info(testCaseName)
            time.sleep(1.0)
            self.sendMessages(testCase, self.symbolForGroup2, 2)

        time.sleep(1.0)
        if self.symbolForGroup0 :
            testCaseName = '%s - Group0 - Mod' % self.baseTestName
            testCase = self.baseTestCase + 'ForGroup0Mod'
            self.A.info(testCaseName)
            time.sleep(1.0)
            self.sendMessages(testCase, self.symbolForGroup0, 0)

        time.sleep(1.0)
        if self.symbolForGroup1 :
            testCaseName = '%s - Group1 - Mod' % self.baseTestName
            testCase = self.baseTestCase + 'ForGroup1Mod'
            self.A.info(testCaseName)
            time.sleep(1.0)
            self.sendMessages(testCase, self.symbolForGroup1, 1)

        time.sleep(1.0)
        if self.symbolForGroup2 :
            testCaseName = '%s - Group2 - Mod' % self.baseTestName
            testCase = self.baseTestCase + 'ForGroup2Mod'
            self.A.info(testCaseName)
            time.sleep(1.0)
            self.sendMessages(testCase, self.symbolForGroup2, 2)

        self.A.testReport()
        self.A.showStats()
        self.postTestVerification()

        self.A.getNotional()

    def sendMessages ( self, testCase, symbol, group ) :
        # testCase : TickSize_SimpleForGroup0New
        # testCase : TickSize_SimpleForGroup1New
        # testCase : TickSize_SimpleForGroup0Mod
        # testCase : TickSize_SimpleForGroup1Mod

        self.A.info(testCase)
        orderid = None
        qty = 1000
        no_to_repeat = 10
        # for side in ['1','3']:
        for side in ['1']:
            # for origExecCond in ['0', '2', '4', '6', '8']:
            for execCond in ['0']:
                # for shortSellFlag in ['0','5','7']:
                for shortSellFlag in ['0']:
                    # omit short sell, exempt / buy combo 
                    if not shortSellFlag == '0' and \
                            side == '3':
                        continue

                    self.A.info('Request type:' + testCase[len(testCase)-3:len(testCase)])
                    if ( testCase[len(testCase)-3:len(testCase)] == 'Mod' ):
                        origPrice = 1000
                        new = self.A.sendNewOrder(symbol, qty, side=side, price=origPrice, execCond= execCond, shortSellFlag=shortSellFlag)
                        self.A.expect(new, 'NewOrderAcceptanceNotice', '0000', testCase + '-Pricefloor = n/a -price = %d' %  origPrice, self.testSequenceNum )
                        orderid = new.getfieldval('IntProcessing')
                        self.testSequenceNum += 1

                    # determine price Range
                    if group == 0 : 
                        for priceFloor in [ 0, 3000, 5000, 30000, 50000, 300000, 500000, 3000000, 5000000, 30000000, 50000000 ] :
                            priceRange = []
                            if ( priceFloor == 0 ):
                                priceRange = range(1,3000)
                            elif ( priceFloor == 3000 ):
                                priceRange = range(3000, 5000)
                            elif ( priceFloor == 5000 ):
                                priceRange = range(5000, 30000)
                            elif ( priceFloor == 30000 ):
                                priceRange = range(30000, 50000)
                            elif ( priceFloor == 50000 ):
                                priceRange = range(50000, 300000) 
                            elif ( priceFloor == 300000 ):
                                priceRange = range(300000, 500000) 
                            elif ( priceFloor == 500000 ):
                                priceRange = range(500000, 3000000) 
                            elif ( priceFloor == 3000000 ):
                                priceRange = range(3000000, 5000000) 
                            elif ( priceFloor == 5000000 ):
                                priceRange = range(5000000, 30000000) 
                            elif ( priceFloor == 30000000):
                                priceRange = range(30000000, 50000000) 
                            elif ( priceFloor == 50000000 ):
                                priceRange = range(50000000, 99999999) 

                            for i in range(no_to_repeat) :
                                price = random.choice(priceRange)
                                time.sleep(0.1)
                                if orderid :
                                    req = self.A.sendMod(orderid, symbol, price=price)
                                    self.checkExpect('Modify', req, testCase + '-Pricefloor = %s -price = %d' % ( priceFloor, price ), price, 0)
                                else :
                                    req = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )
                                    self.checkExpect('New', req, testCase + '-Pricefloor = %s -price = %d' % ( priceFloor, price ), price, 0)

                    elif group == 1 :
                        for priceFloor in [ 0, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000 ] :
                            for i in range(no_to_repeat) :
                                price = 0
                                if ( priceFloor == 0 ):
                                    price = random.randint(1, 10000)
                                elif ( priceFloor == 10000 ):
                                    price = random.randint(100000, 500000)
                                elif ( priceFloor == 50000 ):
                                    price = random.randint(500000, 1000000)
                                elif ( priceFloor == 100000 ):
                                    price = random.randint(1000000, 5000000)
                                elif ( priceFloor == 500000 ):
                                    price = random.randint(5000000, 10000000)
                                elif ( priceFloor == 1000000 ):
                                    price = random.randint(10000000, 50000000)
                                elif ( priceFloor == 5000000 ):
                                    price = random.randint(50000000, 100000000)
                                elif ( priceFloor == 10000000 ):
                                    price = random.randint(100000000, 500000000)
                                elif ( priceFloor == 50000000 ):
                                    price = random.randint(500000000, 1000000000)

                                price = price * 0.1
                                if i > (no_to_repeat * 0.8 ) :
                                    while ( int ( price * 10000 ) % int ( self.A.tickSize[group].checkTickSize(price) * 10000 ) != 0  ) :
                                        self.A.info('before: i=%s,price=%f' % (i, price))
                                        price = price - ( ( price * 10000 ) % ( self.A.tickSize[group].checkTickSize(price) * 10000 ) / 10000 )
                                        self.A.info('after: i=%s,price=%f' % (i, price))
                                time.sleep(0.5)
                                if orderid :
                                    req = self.A.sendMod(orderid, symbol, price=price)
                                    self.checkExpect('Modify', req, testCase + '-Pricefloor = %s -price = %d' % ( priceFloor, price ), price, group)
                                else :
                                    req = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )
                                    self.checkExpect('New', req, testCase + '-Pricefloor = %s -price = %d' % ( priceFloor, price ), price, group)

                    elif group == 2 :
                        for priceFloor in [ 0, 1000, 3000, 10000, 30000, 100000, 300000, 1000000, 3000000, 10000000, 30000000 ] :
                            for i in range(no_to_repeat) :
                                price = 0
                                if ( priceFloor == 0 ):
                                    price = random.randint(1, 10000)
                                elif ( priceFloor == 1000 ):
                                    price = random.randint(10000, 30000)
                                elif ( priceFloor == 3000 ):
                                    price = random.randint(30000, 100000)
                                elif ( priceFloor == 10000 ):
                                    price = random.randint(100000, 300000)
                                elif ( priceFloor == 30000 ):
                                    price = random.randint(300000, 1000000)
                                elif ( priceFloor == 100000 ):
                                    price = random.randint(1000000, 5000000)
                                elif ( priceFloor == 300000 ):
                                    price = random.randint(3000000, 10000000)
                                elif ( priceFloor == 1000000 ):
                                    price = random.randint(10000000, 50000000)
                                elif ( priceFloor == 3000000 ):
                                    price = random.randint(30000000, 100000000)
                                elif ( priceFloor == 10000000 ):
                                    price = random.randint(100000000, 500000000)
                                elif ( priceFloor == 30000000 ):
                                    price = random.randint(300000000, 1000000000)

                                price = price * 0.1
                                if i > (no_to_repeat * 0.8 ) :
                                    while ( int ( price * 10000 ) % int ( self.A.tickSize[group].checkTickSize(price) * 10000 ) != 0  ) :
                                        self.A.info('before: i=%s,price=%f' % (i, price))
                                        price = price - ( ( price * 10000 ) % ( self.A.tickSize[group].checkTickSize(price) * 10000 ) / 10000 )
                                        self.A.info('after: i=%s,price=%f' % (i, price))
                                time.sleep(0.5)
                                if orderid :
                                    req = self.A.sendMod(orderid, symbol, price=price)
                                    self.checkExpect('Modify', req, testCase + '-Pricefloor = %s -price = %d' % ( priceFloor, price ), price, group)
                                else :
                                    req = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )
                                    self.checkExpect('New', req, testCase + '-Pricefloor = %s -price = %d' % ( priceFloor, price ), price, group)


    def checkExpect(self, msgType, request, testCaseName, price, group ):
        #self.A.info('%s,%s,%f,%d' % ( msgType, testCaseName, price, group ));
        rejectResponse = 'NewOrderAcceptanceError'
        acceptResponse = 'NewOrderAcceptanceNotice'
        if msgType == 'Modify' :
            rejectResponse = 'ModRegistrationError'
            acceptResponse = 'ModResultNotice'

        if ( ( int( price * 10000) % int( self.A.tickSize[group].checkTickSize(price) * 10000 ) ) == 0 ):
            self.A.info('Accept-Remainder: %f' % ( ( price * 10000) % ( self.A.tickSize[group].checkTickSize(price) * 10000 ) ))
            self.A.expect(request, acceptResponse, '0000', testCaseName, self.testSequenceNum )
        else :
            self.A.info('Reject-Remainder: %f' % ( ( price * 10000) % ( self.A.tickSize[group].checkTickSize(price) * 10000 ) ))
            self.A.expect(request, rejectResponse, '8011', testCaseName, self.testSequenceNum )
        self.testSequenceNum += 1
                              
    def postTestVerification(self):
        self.assertEqual((self.A.msgSeqNumErrorsFound, self.A.acceptSeqNumErrorsFound,
                          self.A.execSeqNumErrorsFound, self.A.numErrorsFound),
                         (False, False, False, 0))
       
    def tearDown(self):
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
