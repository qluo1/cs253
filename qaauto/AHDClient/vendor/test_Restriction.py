
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


class RestrictionSymbolOrders(unittest.TestCase):

    def setUp(self):
        if not hasattr(self, 'beenHere'):
            #self.A = ahd_client.getApp('sim_newDUMMY.py', 'sample.log')
            self.A = ahd_client.getApp('sim_newVIRTU.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_VIRTU10g.py', 'sample.log')
            #self.A = ahd_client.getApp('sim_colo3.py', 'sample.log')
            self.A.start()
            self.beenHere = True

        time.sleep(5.0)
        self.baseTestName = 'Restriction-Symbol Test Case: '

    def test_restirction_orders(self):

        self.getRestrictedSymbols()

        time.sleep(1.0)
        testCaseName = '%s - Buy Restricted' % self.baseTestName
        testCase = 'BuyRestricted'
        self.A.info(testCaseName)
        self.sendMessages(testCase)
        time.sleep(1.0)

        time.sleep(1.0)
        testCaseName = '%s - Sell Restricted' % self.baseTestName
        testCase = 'SellRestricted'
        self.A.info(testCaseName)
        self.sendMessages(testCase)
        time.sleep(1.0)

        time.sleep(1.0)
        testCaseName = '%s - ShortSell Restricted' % self.baseTestName
        testCase = 'ShortRestricted'
        self.A.info(testCaseName)
        self.sendMessages(testCase)
        time.sleep(1.0)

        time.sleep(1.0)
        testCaseName = '%s - ShortSellExempted Restricted' % self.baseTestName
        testCase = 'ShortExemptedRestricted'
        self.A.info(testCaseName)
        self.sendMessages(testCase)
        time.sleep(1.0)

        time.sleep(1.0)
        for testCase in [ 'BelowMinPrice', 'AtMinPrice', \
                          'AboveMinPrice', 'BelowMaxPrice', \
                          'AtMaxPrice',    'AboveMaxPrice' ]:
             testCaseName = '%s - %s' % ( self.baseTestName, testCase )
             self.A.info(testCaseName)
             self.sendMessages(testCase)
             time.sleep(1.0)

        time.sleep(1.0)
        for testCase in [ 'ModBelowMinPrice', 'ModAtMinPrice', \
                          'ModAboveMinPrice', 'ModBelowMaxPrice', \
                          'ModAtMaxPrice',    'ModAboveMaxPrice' ]:
             testCaseName = '%s - %s' % ( self.baseTestName, testCase )
             self.A.info(testCaseName)
             self.sendMessages(testCase)
             time.sleep(1.0)


        time.sleep(1.0)
        for testCase in [ 'BelowMaxLots', 'AtMaxLots', 'AboveMaxLots' ] :
            testCaseName = '%s - New' % testCase
            self.A.info(testCaseName)
            self.sendMessages(testCase)
            time.sleep(1.0)


        self.getLotSizes()

        time.sleep(1.0)
        testCaseName = '%s -  LotSize' % self.baseTestName
        testCase = 'LotSize'
        self.A.info(testCaseName)
        self.sendMessages(testCase)
        time.sleep(1.0)

        time.sleep(1.0)
        testCaseName = '%s -  LotSize' % self.baseTestName
        testCase = 'ModLotSize'
        self.A.info(testCaseName)
        self.sendMessages(testCase)
        time.sleep(1.0)

        self.A.info('Done!...')


    def sendMessages ( self, testCase ) :
        # testCase : BuyRestricted
        # testCase : SellRestricted
        # testCase : ShortRestricted
        # testCase : ShortExemptRestricted

        # check if case is to test for restricted symbol
        if testCase in ['BuyRestricted', 'SellRestricted', \
                        'ShortRestricted', 'ShortExemptedRestricted' ]:

            for symbol in ( self.RestrictedSymbols.keys()) :
                for side in ['1', '3']:
                    for execCond in ['0', '2', '4', '6', '8']:
                        for shortSellFlag in ['0', '5', '7']:
                            for priceType in [ 'Limit', 'Market' ]: 
                                # omit side with not expected 
                                if ( testCase == 'BuyRestricted' and \
                                    ( side != '3' or shortSellFlag != '0' ) ) :
                                    continue
                                if ( testCase == 'SellRestricted' and \
                                    ( side != '1' or shortSellFlag != '0' ) ) :
                                    continue
                                if ( testCase == 'ShortRestricted' and \
                                    ( side != '1' or shortSellFlag != '5' ) ) :
                                    continue
                                if ( testCase == 'ShortExemptedRestricted' and \
                                    ( side != '1' or shortSellFlag != '7' ) ) :
                                    continue
                                # omit short sell, exempt / buy combo
                                if not shortSellFlag == '0' and \
                                        side == '3':
                                    continue
                                # omit funari / market combo
                                if execCond == '6' and \
                                        priceType == 'Market' :
                                    continue
                                # omit short sell / market combo
                                if shortSellFlag == '5' and \
                                        priceType == 'Market' :
                                    continue
                                
                                price = None
                                qty = 0
                                if symbol in self.A.securities :
                                    basePrice = self.A.securities[symbol].basePrice
                                    qty = self.A.securities[symbol].lotSize + self.A.securities[symbol].lotSize  * random.choice(range(0,10))
                                else :
                                    basePrice =0
                                    qty = 1000
                                if basePrice != 0 :
                                    if self.A.securities[symbol].lotSize != 0 :
                                        qty = self.A.securities[symbol].lotSize + self.A.securities[symbol].lotSize  * random.choice(range(0,10))
                                        if priceType == 'Market' :
                                            price = ' 0           '
                                        else :
                                            price = basePrice + self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(basePrice) * (random.choice(range(0,5)) - random.choice(range(0,5)))
                                            if (symbol =="8630") :
                                                self.A.info('xue  basePrice = %d' % ( self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(basePrice)  ) )
                                    else :
                                        self.A.info('Cannot find lotSize .. skipping' )
                                        continue
                                else :
                                    if priceType == 'Market' :
                                        price = ' 0           '
                                    else :
                                        self.A.info('Cannot find BasePrice for Limit order .. skipping' )
                                        continue
                                m = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )
                                if ( testCase == 'BuyRestricted' and \
                                     self.RestrictedSymbols[symbol].buy == 'N' ) :
                                    self.A.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                elif ( testCase == 'SellRestricted' and \
                                       self.RestrictedSymbols[symbol].sell == 'N' ) :
                                    self.A.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                elif ( testCase == 'ShortRestricted' and \
                                       self.RestrictedSymbols[symbol].shortSell == 'N' ) :
                                    self.A.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                elif ( testCase == 'ShortExemptedRestricted' and \
                                       self.RestrictedSymbols[symbol].shortSellExempt == 'N' ) :
                                    self.A.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                else :
                                    self.A.expect(m, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )
                                    sleep(0.1)

        elif testCase in [ 'BelowMinPrice',    'AtMinPrice', \
                           'AboveMinPrice',    'BelowMaxPrice', \
                           'AtMaxPrice',    'AboveMaxPrice', \
                           'ModBelowMinPrice', 'ModAtMinPrice', \
                           'ModAboveMinPrice', 'ModBelowMaxPrice', \
                           'ModAtMaxPrice',    'ModAboveMaxPrice' ]:

            for side in ['1','3']:
                for ExecCond in ['0', '2', '4', '6', '8']:
                    for shortSellFlag in ['0','5','7']:
                        # omit short sell, exempt / buy combo
                        if not shortSellFlag == '0' and \
                                side == '3':
                            continue
                        # omit IOC order
                        if ExecCond == '8' :
                            continue

                        noBasePrice = 1
                        price = None
                        qty = 0
                        symbol = ''
                        basePrice = None
                        while noBasePrice == 1:
                            symbol = random.choice(self.A.securities.keys())
                            basePrice = self.A.securities[symbol].basePrice
                            maxPrice = self.A.securities[symbol].maxPrice
                            minPrice = self.A.securities[symbol].minPrice
                            if basePrice != 0 :
                                if maxPrice != 0 :
                                    if minPrice != 0 :
                                        if self.A.securities[symbol].lotSize !=0 :
                                            if  basePrice < minPrice or \
                                                    basePrice > maxPrice :
                                                self.A.info('price is not within price range (%d <> %d) -- basePrice = %d' % ( minPrice, maxPrice, basePrice ) )
                                                continue 
                                            qty = self.A.securities[symbol].lotSize * random.choice(range(1,5))
                                            if 'BelowMinPrice' in testCase :
                                                price = minPrice - self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(minPrice)
                                            elif 'AtMinPrice' in testCase :
                                                price = minPrice
                                            elif 'AboveMinPrice' in testCase :
                                                price = minPrice + self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(minPrice)
                                            elif 'BelowMaxPrice' in testCase :
                                                price = maxPrice - self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(maxPrice)
                                            elif 'AtMaxPrice' in testCase :
                                                price = maxPrice
                                            elif 'AboveMaxPrice' in testCase :
                                                price = maxPrice + self.A.tickSize[self.A.securities[symbol].tickGroup].checkTickSize(maxPrice)
                                            noBasePrice = 0

                        if testCase in [ 'BelowMinPrice', 'AtMinPrice', \
                                         'AboveMinPrice', 'BelowMaxPrice', \
                                         'AtMaxPrice',    'AboveMaxPrice' ]:

                            new = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=ExecCond, shortSellFlag=shortSellFlag )

                            if testCase  in [ 'BelowMinPrice', 'AboveMaxPrice']:
                                self.A.expect(new, 'NewOrderAcceptanceError', None, testCaseName=testCase  )
                            else :
                                self.A.expect(new, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )

                        else : 

                            new = self.A.sendNewOrder(symbol, qty, side=side, price=basePrice, execCond=ExecCond, shortSellFlag=shortSellFlag )
                            self.A.expect(new, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )

                            sleep(0.1)
                            mod = self.A.sendMod(new, symbol, price=price )
                            if testCase  in [ 'ModBelowMinPrice', 'ModAboveMaxPrice']:
                                self.A.expect(mod, 'ModRegistrationError', None, testCaseName=testCase )
                            else :
                                self.A.expect(mod, 'ModResultNotice', None, testCaseName=testCase )

                            sleep(0.1)

        elif testCase in [ 'BelowMaxLots', 'AtMaxLots', 'AboveMaxLots' ]:

            for side in ['1','3']:
                for execCond in ['0', '2', '4', '6', '8']:
                    for shortSellFlag in ['0','5','7']:
                        for priceType in ['Limit', 'Market' ]:
                            if not shortSellFlag == '0' and \
                                    side == '3':
                                continue
                            # omit funari / market combo
                            if execCond == '6' and \
                                    priceType == 'Market' :
                                continue
                            # omit short sell / market combo
                            if shortSellFlag == '5' and \
                                    priceType == 'Market' :
                                continue

                            noBasePrice = 1
                            price = None
                            qty = 0
                            symbol = ''
                            while noBasePrice == 1:
                                symbol = random.choice(self.A.securities.keys())
                                basePrice = self.A.securities[symbol].basePrice
                                maxLots = self.A.securities[symbol].maxLot
                                print 'symbol = %s' % symbol
                                print 'basePrice = %d' % basePrice
                                print 'maxLots = %d' % maxLots
                                if basePrice != 0 :
                                    if maxLots != 0 :
                                        if self.A.securities[symbol].lotSize != 0 :
                                            price = basePrice
                                            if  price < self.A.securities[symbol].minPrice or \
                                                    price > self.A.securities[symbol].maxPrice :
                                                self.A.info('price is not within price range (%d <> %d) --price = %d' % ( self.A.securities[symbol].minPrice, self.A.securities[symbol].maxPrice, price ) )
                                                continue 
                                            if testCase == 'BelowMaxLots' :
                                                qty = self.A.securities[symbol].lotSize * ( maxLots - random.choice(range(1, 10)))
                                            elif testCase == 'AtMaxLots' :
                                                qty = self.A.securities[symbol].lotSize * maxLots 
                                            elif testCase == 'AboveMaxLots' :
                                                qty = self.A.securities[symbol].lotSize * ( maxLots + random.choice(range(1, 10)))
                                            noBasePrice = 0

                            print 'sending orders now'
                            m = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )
                            if testCase == 'AboveMaxLots' :
                                self.A.expect(m, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                            else :
                                self.A.expect(m, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )

        elif testCase in [ 'LotSize', 'ModLotSize' ]:

            for symbolLotSize in ( self.symbolsLotSize.keys()) :
                noBasePrice = 1
                symbol = ''
                basePrice = 0
                while noBasePrice == 1:
                    symbol = random.choice(self.symbolsLotSize[symbolLotSize])
                    basePrice = self.A.securities[symbol].basePrice
                    if basePrice != 0 :
                        if  basePrice < self.A.securities[symbol].minPrice or \
                                basePrice > self.A.securities[symbol].maxPrice :
                            self.A.info('price is not within price range (%d <> %d) --basePrice = %d' % ( self.A.securities[symbol].minPrice, self.A.securities[symbol].maxPrice, basePrice ) )
                            continue 
                        noBasePrice = 0


                self.A.info("Testing LotSize(%s) with symbol : %s " % (self.A.securities[symbol].lotSize, symbol))
                for side in ['1', '3']:
                    for execCond in ['0', '2', '4', '6', '8']:
                        for shortSellFlag in ['0', '5', '7']:
                            for priceType in [ 'Limit', 'Market' ]:
                                for lotSize in self.lotSize :
                                    # if lotSize is greater than the actual lotSize for symbol, then skip
                                    if lotSize > self.A.securities[symbol].lotSize :
                                        continue
                                    # omit short sell, exempt / buy combo
                                    if not shortSellFlag == '0' and \
                                            side == '3':
                                        continue
                                    # omit funari / market combo
                                    if execCond == '6' and \
                                            priceType == 'Market' :
                                        continue
                                    # omit short sell / market combo
                                    if shortSellFlag == '5' and \
                                            priceType == 'Market' :
                                        continue
                                    # omit IOC order
                                    if execCond == '8' :
                                        continue

                                    price = None
                                    qty = 0
                                    vqty = 0
                                    randomNumber = [1, 3, 5, 7, 9]

                                    while vqty == 0 :
                                        vqty = self.A.securities[symbol].lotSize * random.choice(range(21, 30) )

                                    while qty == 0 :
                                        num = random.choice(randomNumber )
                                        if self.A.securities[symbol].lotSize == lotSize :
                                            qty = lotSize * num
                                        else :
                                            qty = self.A.securities[symbol].lotSize * random.choice ( range(3) ) + lotSize * num

                                    if priceType == 'Market' :
                                        price = ' 0           '
                                        noBasePrice = 0
                                    else :
                                        price = basePrice 
                                        noBasePrice = 0

                                    if testCase == 'LotSize' :
                                        new = self.A.sendNewOrder(symbol, qty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )

                                        if ( qty % self.A.securities[symbol].lotSize == 0 ):
                                            self.A.expect(new, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )
                                        else :
                                            self.A.expect(new, 'NewOrderAcceptanceError', None, testCaseName=testCase )
                                        sleep(0.1)
                                    elif testCase == 'ModLotSize' :

                                        new = self.A.sendNewOrder(symbol, vqty, side=side, price=price, execCond=execCond, shortSellFlag=shortSellFlag )
                                        self.A.expect(new, 'NewOrderAcceptanceNotice', None, testCaseName=testCase )

                                        sleep(0.1)

                                        mod = self.A.sendMod(new, symbol, qty=qty )
                                        if ( qty % self.A.securities[symbol].lotSize == 0 ) :
                                            self.A.expect(mod, 'ModResultNotice', None, testCaseName=testCase )
                                        else :
                                            self.A.expect(mod, 'ModRegistrationError', None, testCaseName=testCase )







    def getRestrictedSymbols ( self ) :

        self.RestrictedSymbols = {}
        self.A.info("Checking for restricted symbols for client '%s'" % self.A.state['clientID'] )

        for restriction in self.A.restrictions.keys() :
            # 0 : client id 1: symbol
            restrict = restriction
            if restrict[0] == self.A.state['clientID'] :
                self.RestrictedSymbols[restrict[1]] = self.A.restrictions[restriction]
                self.A.info('ClientID = %s symbol = %s' % ( restrict[0], restrict[1] ) )

            elif restrict[0] == '*all' :
                self.RestrictedSymbols[restrict[1]] = self.A.restrictions[restriction]
                self.A.info('ClientID = %s symbol = %s' % ( restrict[0], restrict[1] ) )


    def getLotSizes ( self ) :

        self.symbolsLotSize = {}
        self.lotSize = []
        for symbol in ( self.A.securities.values() ) :
            if not self.symbolsLotSize.has_key(symbol.lotSize) :
                self.symbolsLotSize[symbol.lotSize] = []
            self.symbolsLotSize[symbol.lotSize].append(symbol.symbol)
 
        for lotSize in ( self.symbolsLotSize.keys() ) :
            self.lotSize.append(lotSize)


    def postTestVerification(self):
        self.assertEqual((self.A.msgSeqNumErrorsFound, self.A.acceptSeqNumErrorsFound, 
                          self.A.execSeqNumErrorsFound, self.A.numErrorsFound), 
                         (False, False, False, 0))

       
    def tearDown(self):
        self.A.testReport()
        self.A.showStats()
        self.postTestVerification()
        self.A.stop()

if __name__ == '__main__':
    unittest.main()
