
from scapy.all import *
import ahd_client_temporarily as ahd_client
from time import sleep
import unittest
import test_cfg
import random

# valid values, for reference
#for side in ['1','3']:
#for execCond in ['0', '2', '4', '6', '8']:
#for shortSellFlag in ['0','5','7']:
#for propBrokerageClass in ['0','9']:
#for cashMarginCode in ['0','2','4']:
#for stabArbCode in ['0','6','8']:
#for ordAttrClass in ['1','2']:
#for suppMemberClass in ['0','1']:


class ClientLimitTest(unittest.TestCase):
    side = ['1','3']:
    execCond = ['0', '2', '4', '6', '8']:
    shortSellFlag = ['0','5','7']:
    propBrokerageClass = ['0','9']:
    cashMarginCode = ['0','2','4']:
    stabArbCode = ['0','6','8']:
    ordAttrClass = ['1','2']:
    suppMemberClass = ['0','1']:

    def setUp(self):
        if not hasattr(self, 'beenHere'):
            #self.a=ahd_client.getApp('sim_Dummy.py', 'sample.log')
            self.a=ahd_client.getApp('sim_VIRTU.py', 'sample.log')
            self.a.start()
            self.beenHere = True
            
        self.baseTestCase = 'Client Limit Test'

    def test_clientLimits(self):

        self.setClientLimits('side')

        time.sleep(1.0)       
        baseTestCase = '%s - Limit BuyRestricted' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        if self.clientLimit.buyRestricted != 'Y' :
            self.a.info('BuyRestricted is not set to [Y] ... skipping') 
        else :
            self.sendRestrictedOrder('Buy', baseTestCase )

        time.sleep(1.0)       
        baseTestCase = '%s - Limit SellRestricted' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        if self.clientLimit.sellRestricted != 'Y' :
            self.a.info('SellRestricted is not set to [Y] ... skipping') 
        else :
            self.sendRestrictedOrder('Sell', baseTestCase )

        time.sleep(1.0)       
        baseTestCase = '%s - Limit ShortRestricted' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        if self.clientLimit.shortRestricted != 'Y' :
            self.a.info('ShortRestricted is not set to [Y] ... skipping') 
        else :
            self.sendRestrictedOrder('ShortSell', baseTestCase )

        time.sleep(1.0)
        baseTestCase = '%s - Limit ShortExemptRestricted' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        if self.clientLimit.shortExemptRestricted != 'Y' :
            self.a.info('ShortExemptRestricted is not set to [Y] ... skipping') 
        else :
            self.sendRestrictedOrder('ShortSellExempt', baseTestCase )


        time.sleep(1.0)
        baseTestCase = '%s - Limit MaxNV - New' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        if self.clientLimit.maxNV == 0 :
            self.a.info('maxNV is not set ... skipping') 
        else :
            for side in ['1','3']:
                for execCond in ['0', '2', '4', '6', '8']:
                    for shortSellFlag in ['0','5','7']:
                        symbol = ''
                        qty = 0
                        vQty = 0
                        price = 0
                        vPrice = 0
                        noBasePrice = 1
                        while noBasePrice == 1 :
                            pxLot = 0
                            symbol = random.choice(self.a.securities.keys())
                            basePrice = self.a.securities[symbol].basePrice
                            if self.a.securities[symbol].lastPrice != 0 :
                                basePrice = self.a.securities[symbol].lastPrice
                            lotSize = self.a.securities[symbol].lotSize
                            if basePrice != 0 :
                                if lotSize != 0 :
                                    pxLot = self.clientLimit.maxNV / lotSize
                                    lot = pxLot / basePrice
                                    qty = (lot - 1)  * lotSize
                                    vQty = (lot + random.choice(range(1, 10)))  * lotSize
                                    price = basePrice - self.a.getTickSize(basePrice) * random.choice(range(1,5))
                                    vPrice = basePrice + self.a.getTickSize(basePrice) * random.choice(range(1,5))
                                    noBasePrice = 0
                        for priceType in ['MarketViolation', 'Market', 'LimitViolation', 'Limit' ]:
                            # omit non sell                        
                            if side != '1' or shortSellFlag != '0' :
                                continue
                            # omit short sell, exempt / buy combo 
                            if not shortSellFlag == '0' and not side == '3':
                                continue
                            # omit funari / market combo
                            if execCond == '6' and priceType in [ 'Market', 'MarketViolation' ] :
                                continue
                            # omit short sell / market combo
                            if shortSellFlag == '5' and priceType in [ 'Market', 'MarketViolation' ] :
                                continue
                            testCase = '%s - Side=%s - ExecCond=%s - ShortSellFlag=%s - PriceType=%s' % (baseTestCase, side, execCond, shortSellFlag, priceType )
                            px = None
                            quantity = 0
                            if priceType == 'MarketViolation' :
                                px = ' 0           '
                                quantity = vQty
                            elif priceType == 'Market' :
                                px = ' 0           '
                                quantity = qty
                            elif priceType == 'LimitViolation' :
                                px = vPrice
                                quantity = vQty
                            elif priceType == 'Limit' :
                                px = price
                                quantity = qty
                                
                            m = self.a.sendNewOrder(symbol, quantity, side=side, price=px, execCond=execCond, shortSellFlag=shortSellFlag)
                            sleep(0.1)
                            if priceType in [ 'LimitViolation', 'MarketViolation' ] :
                                self.a.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                            else :
                                self.a.expect(m, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )
                            sleep(0.1)
        
        time.sleep(1.0)
        baseTestCase = '%s - Limit MaxNetValue - New' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        countMaxNetValue = 0
        if self.clientLimit.maxNetValue == 0 :
            self.a.info('maxNetValue is not set ... skipping') 
        else :
            while countMaxNetValue < 4 :
                for side in ['1','3']:
                    for execCond in ['0', '2', '4', '6', '8']:
                        for shortSellFlag in ['0','5','7']:
                            for priceType in ['Market', 'Limit' ]:
                                # omit not buy                        
                                if side != '3' or shortSellFlag != '0' :
                                    continue
                                # omit short sell, exempt / buy combo 
                                if not shortSellFlag == '0' and not side == '3':
                                    continue
                                # omit funari / market combo
                                if execCond == '6' and priceType == 'Market' :
                                    continue
                                # omit short sell / market combo
                                if shortSellFlag == '5' and priceType == 'Market' :
                                    continue
                                symbol = ''
                                qty = 0
                                price = None
                                noBasePrice = 1
                                nv = 0
                                testCase = '%s - Side=%s - ExecCond=%s - ShortSellFlag=%s - PriceType=%s' % (baseTestCase, side, execCond, shortSellFlag, priceType )
                                while noBasePrice == 1 :
                                    symbol = random.choice(self.a.securities.keys())
                                    basePrice = self.a.securities[symbol].basePrice
                                    if self.a.securities[symbol].lastPrice != 0 :
                                        basePrice = self.a.securities[symbol].lastPrice
                                    lotSize = self.a.securities[symbol].lotSize
                                    self.a.info('Symbol : %s' % symbol)
                                    if basePrice != 0 :
                                        if lotSize != 0 :
                                            while ( qty == 0 or self.a.securities[symbol].maxLot * lotSize < qty ) :
                                                qty = lotSize * random.choice(range(1,10))
                                                if self.a.securities[symbol].maxLot == 0:
                                                    continue
                                            if priceType == 'Market' :
                                                price = ' 0           '
                                                nv = basePrice * qty
                                            else :
                                                price = 0
                                                while ( self.a.securities[symbol].maxPrice < price or self.a.securities[symbol].minPrice > price ) :
                                                    self.a.info('symbol =%s, price = %d' % (symbol, price ) )
                                                    price = basePrice + self.a.getTickSize(basePrice) * (random.choice(range(5)) - random.choice(range(5)) )
                                                if basePrice > price :
                                                    nv = basePrice * qty
                                                else :
                                                    nv = price * qty
                                                
                                            noBasePrice = 0
                                    
                                m = self.a.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag)
                                sleep(0.1)
                                
                                if ( self.a.client.netMV + nv ) > self.clientLimit.maxNetValue :
                                    self.a.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                    countMaxNetValue += 1
                                else : 
                                    self.a.expect(m, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )
                                
                                sleep(0.1)
        
        time.sleep(1.0)
        baseTestCase = '%s - Limit MinNetValue - New' % self.baseTestCase
        self.a.info(baseTestCase)
        time.sleep(1.0)
        countMinNetValue = 0
        if self.clientLimit.minNetValue == 0 :
            self.a.info('minNetValue is not set ... skipping') 
        else :
            while countMinNetValue < 4 :
                for side in ['1','3']:
                    for execCond in ['0', '2', '4', '6', '8']:
                        for shortSellFlag in ['0','5','7']:
                            for priceType in ['Market', 'Limit' ]:
                                # omit not sell                        
                                if side == '3' and shortSellFlag == '0' :
                                    continue
                                # omit short sell, exempt / buy combo 
                                if not shortSellFlag == '0' and not side == '3':
                                    continue
                                # omit funari / market combo
                                if execCond == '6' and priceType == 'Market' :
                                    continue
                                # omit short sell / market combo
                                if shortSellFlag == '5' and priceType == 'Market' :
                                    continue
                                symbol = ''
                                qty = 0
                                price = None
                                noBasePrice = 1
                                nv = 0
                                testCase = '%s - Side=%s - ExecCond=%s - ShortSellFlag=%s - PriceType=%s' % (baseTestCase, side, execCond, shortSellFlag, priceType )
                                while noBasePrice == 1 :
                                    symbol = random.choice(self.a.securities.keys())
                                    basePrice = self.a.securities[symbol].basePrice
                                    if self.a.securities[symbol].lastPrice != 0 :
                                        basePrice = self.a.securities[symbol].lastPrice
                                    lotSize = self.a.securities[symbol].lotSize
                                    if basePrice != 0 :
                                        if lotSize != 0 :
                                            while ( qty == 0 or self.a.securities[symbol].maxLot < qty ) :
                                                qty = lotSize * random.choice(range(1,10))
                                            if priceType == 'Market' :
                                                price = ' 0           '
                                                nv = basePrice * qty
                                            else :
                                                price = 0
                                                while ( self.a.securities[symbol].maxPrice < price or self.a.securities[symbol].minPrice > price ) :
                                                    price = basePrice + self.a.getTickSize(basePrice) * (random.choice(range(5)) - random.choice(range(5)) )
                                                if basePrice > price :
                                                    nv = basePrice * qty
                                                else :
                                                    nv = price * qty
                                                
                                            noBasePrice = 0
                                    
                                m = self.a.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag)
                                sleep(0.1)
                                if ( ( self.a.client.netMV - nv ) < self.clientLimit.minNetValue ):
                                    self.a.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                    countMinNetValue += 1
                                else : 
                                    self.a.expect(m, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )
                                
                                sleep(0.1)
                            
                            
        self.a.testReport()
        self.a.showStats()
        self.postTestVerification()

    def sendRestrictedOrder (self, restriction, baseTestCase=''):

        restrictedSide = ''
        restrictedSSFlag = ''
        if restriction == 'Buy' :
            restrictedSide = '3'
            restrictedSSFlag = '0'
        elif restriction in ['Sell', 'ShortSell', 'ShortSellExempt' ] :
            restrictedSide = '1'
            if restriction == 'Sell' :
                restrictedSSFlag = '0'
            elif restriction == 'ShortSell' :
                restrictedSSFlag = '5'
            elif restriction == 'ShortSellExempt' :
                restrictedSSFlag = '7'

        for side in ['1','3']:
            for execCond in ['0', '2', '4', '6', '8']:
                for shortSellFlag in ['0','5','7']:
                    for priceType in ['Market', 'Limit' ]:
                        # omit non short sell                        
                        if side != restrictedSide or shortSellFlag != restrictedSSFlag :
                            continue
                        # omit funari / market combo
                        if execCond == '6' and priceType == 'Market' :
                            continue
                        # omit short sell / market combo
                        if shortSellFlag == '5' and priceType == 'Market' :
                            continue
                        symbol = ''
                        qty = 0
                        price = None
                        noBasePrice = 1
                        testCase = '%s - Side=%s - ExecCond=%s - ShortSellFlag=%s - PriceType=%s' % (baseTestCase, side, execCond, shortSellFlag, priceType )
                        while noBasePrice == 1 :
                            symbol = random.choice(self.a.securities.keys())
                            basePrice = self.a.securities[symbol].basePrice
                            lotSize = self.a.securities[symbol].lotSize
                            if basePrice != 0 :
                                if lotSize != 0 :
                                    while ( qty == 0 ) :
                                        qty = lotSize * random.choice(range(1,10))
                                    if priceType == 'Market' :
                                        price = ' 0           '
                                    else :
                                        price = 0
                                        while ( self.a.securities[symbol].maxPrice < price and self.a.securities[symbol].minPrice > price ) :
                                            price = basePrice + self.a.getTickSize(basePrice) * (random.choice(range(5)) - random.choice(range(5)) )
                                    noBasePrice = 0
                                    
                        m = self.a.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag)
                        sleep(0.1)
                        self.a.info('sent: %s' % testCase)
                        self.a.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                        sleep(0.1)
     
    def sendMessages (self, testCase ):

        if testCase in [ 'MaxNVNew', 'MaxNVMod' ] :
            for side in self.side :
                for execCond in self.execCond :
                    for shortSellFlag in self.shortSellFlag :
                        symbol = ''
                        noBasePrice = 1
                        marketPrice = 0
                        priceLots = 0
                        while noBasePrice == 1 :
                            symbol = random.choice(self.a.securities.keys())
                            marketPrice = self.a.securities[symbol].marketPrice
                            if marketPrice != 0 :
                                if self.a.securities[symbol].lotSize != 0 :
                                    if ( self.clientLimit.maxNV % lotSize == 0 ) :
                                        priceLots = self.clientLimit.maxNV / lotSize 
                                        noBasePrice = 0

                        for limitType in [ 'MarketViolation', 'Market', \
                                           'LimitViolation', 'Limit' ]:
                            qty = 0
                            price = None

                            # omit short sell market combo 
                            if shortSellFlag == '5' and \
                                    limitType in [ 'MarketViolation', 'Market' ]  :
                                continue

                            # omit omit funari / market combo
                            if execCond == '6' and \
                                    limitType in [ 'MarketViolation', 'Market' ]  :
                                continue

                            if limitType == 'MarketViolation'
                                price = ' 0           '
                                qty = ( priceLots / marketPrice + 1 ) * self.a.securities[symbol].lotSize

                            elif limitType == 'Market'
                                price = ' 0           '
                                qty = ( priceLots / marketPrice ) * self.a.securities[symbol].lotSize

                            elif limitType == 'LimitViolation' :
                                noPrice = 1
                               
                            
                            


    
        
    def postTestVerification(self):
        self.assertEqual((self.a.msgSeqNumErrorsFound, self.a.acceptSeqNumErrorsFound, 
                          self.a.execSeqNumErrorsFound, self.a.numErrorsFound), 
                         (False, False, False, 0))

    def getClientLimits (self) :
        rawIp = '10.100.193.40'
        rawzcmd = '/home/raptor/RAW_UAT_P/scripts/zcmd.sh'
        dataFolder = '/home/raptor/RAW_UAT_P/test_data'
        localDataFolder = '
        clientID = self.a.state['clientID'] 
        if clientID in self.a.limits.keys() :
            self.clientLimit = self.a.limits[clientID]
        else :
            self.a.info('Cannot find client limits info for %s' % clientID )
            self.tearDown()

    def setClientLimits(self, limitType) :

        if limitType == 'side' :
            self.a.info('Setting limits for side')
            self.sendCmds('clientSideLimits.csv')
            time.sleep(1.0)
            self.scpSodFile('clientSideLimits.csv')

        elif limitType == 'maxNV' :
            self.a.info('Setting limits for maxNV')
            self.sendCmds('clientMaxNV.csv')
            time.sleep(1.0)
            self.sendCmds('securityMaxNV.csv', 'securities')
            time.sleep(1.0)
            self.scpSodFile('clientMaxNV.csv')
            time.sleep(1.0)
            
        elif limitType == 'maxOrders' :
            self.a.info('Setting limits for maxOrders')
            self.sendCmds('clientMaxOrders.csv')
            time.sleep(1.0)
            self.sendCmds('securityMaxNV.csv', 'securities')
            time.sleep(1.0)

        elif limitType == 'maxNet' :
            self.a.info('Setting limits for maxNet')
            self.sendCmds('clientMaxNet.csv')
            time.sleep(1.0)
            self.sendCmds('securityMaxNV.csv', 'securities')
            time.sleep(1.0)
        
        elif limitType == 'minNet' :
            self.a.info('Setting limits for minNet')
            self.sendCmds('clientMinNet.csv')
            time.sleep(1.0)
            self.sendCmds('securityMaxNV.csv', 'securities')
            time.sleep(1.0)

        elif limitType == 'maxDaily' :
            self.a.info('Setting limits for maxDaily')
            self.sendCmds('clientMaxDaily.csv')
            time.sleep(1.0)
            self.sendCmds('securityMaxNV.csv', 'securities')
            time.sleep(1.0)

    def scpSodFile (self, file) :
        rawIp = '10.100.193.40'
        dataFolder = '/home/raptor/RAW_UAT_P/test_data'
        localDatafolder = '/home/raptor/ahd-client/ref_data'
        self.a.info('Copying file:%s from Raw Server' % file )
        subprocess.Popen(['scp', rawIp + ':' + dataFolder + '/' + file, dataFolder])

    def sendCmds (self, file, type='limits' ):
        rawIp = '10.100.193.40'
        rawzcmd = '/home/raptor/RAW_UAT_P/scripts/zcmd.sh'
        dataFolder = '/home/raptor/RAW_UAT_P/test_data'
        cmd = rawzcmd + ' %s "< %s"' % ( type, dataFolder + '/' + file)
        self.a.info('Sending limits command to load a file :%s' % file )
        subprocess.Popen(['ssh', '-t', rawIp, "%s" % cmd])
        
    def tearDown(self):
        self.a.stop()

if __name__ == '__main__':
    unittest.main()
