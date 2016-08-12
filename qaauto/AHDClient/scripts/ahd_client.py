""" vendor code with modificaiton.

#######################
Arrowhead Client\n \
Copyright Fusion Systems 2013, all rights reserved.\n \
By: Jonathan Hope\n \
For use to test Fusion's Raptor Raw product only
"""

import os
from time import sleep
from datetime import datetime, timedelta
from threading import Thread
import socket
import logging
import pprint
import copy
import StringIO
import errno
import sys
import random
import csv
from math import floor

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from ahd import *
import scapy
from scapy.all import conf, ConditionalField,Emph

nodelay = 1

class EventState():

    def __init__(self, pkt):
        """Assumes pkt is an OrderCommon or NoticeCommon packet"""
        self.request = None
        self.reasonCode = None
        self.response = None
        self.expectedReasonCode = '0000'
        self.expectedResponse = 'NewOrderAcceptanceNotice'
        self.trail = [pkt]
        self.testCaseName = 'No name provided'
        self.serialNum = None

    def update(self, pkt):
        """Updates the order state structure with the info implied in the packet. Assumes pkt is an OrderCommon or NoticeCommon packet"""
        # if this is a request response, update state
        if NoticeCommon == type(pkt):
            if type(pkt.payload) in [NewOrderAcceptanceNotice,
                                     NewOrderAcceptanceError,
                                     NewOrderRegistrationError,
                                     #ModAcceptanceNotice,
                                     ModAcceptanceError,
                                     ModRegistrationError,
                                     ModResultNotice,
                                     CancelAcceptanceNotice,
                                     CancelAcceptanceError,
                                     CancelRegistrationError,
                                     CancelResultNotice,
                                     ]:
                self.reasonCode = pkt.getfieldval('ReasonCode')
        self.trail.append(pkt)

class EventData():

    def __init__(self ) :

        self.side = None
        self.issueCode = None
        self.priceType = None
        self.price = 0
        self.qty = 0
        self.mktPrice = 0
        self.notionalValue = 0
        self.executedQty = 0
        self.executedPrice = 0
        self.executedNotionalValue = 0
        self.dataID = None
        self.internalProcessing = None
        self.eventType = None

    def update( self, pkt, securityInfo, orderState ):

        self.eventType = pkt.payload.name
        self.issueCode = securityInfo.symbol

        # set side
        if type (pkt.payload) in [ NewOrder, NewOrderAcceptanceNotice, \
                                   ExecutionNotice, InvalidationResultNotice ]:
            self.side = pkt.getfieldval('Side')
        else :
            self.side = orderState['Side']

        # set price of symbol
        if securityInfo.lastPrice != 0 :
            self.mktPrice = securityInfo.lastPrice
        elif securityInfo.basePrice != 0 :
            self.mktPrice = securityInfo.basePrice
        else :
            self.mktPrice = 0

        # set field for internal processing
        self.internalProcessing = pkt.getfieldval('IntProcessing')

        # set qty
        if type(pkt.payload) in [ NewOrder, NewOrderAcceptanceNotice ] :
            self.qty = int( pkt.getfieldval('Qty') ) if type( pkt.getfieldval('Qty')) == int else 0
        else :
            self.qty = orderState['Qty'] 
            if type(pkt.payload) in [ ModOrder, ModResultNotice ] :
                if pkt.getfieldval('Qty') != '             ' :
                    self.qty = self.qty - int( pkt.getfieldval('Qty') ) if type( pkt.getfieldval('Qty')) == int else self.qty

        # set price
        if type(pkt.payload) in [ NewOrder, ModOrder, NewOrderAcceptanceNotice, \
                                   ModResultNotice, InvalidationResultNotice ] :
            if pkt.getfieldval('Price') == ' 0           ' :
                self.priceType = 'Market'
                self.price = self.mktPrice
            elif pkt.getfieldval('Price') != '             ' :
                self.priceType = 'Limit'
                if type (pkt.getfieldval('Price')) == int :
                    self.price = int( pkt.getfieldval('Price') ) / 10000
            else :
                self.priceType = orderState['PriceType']
                self.price = orderState['Price']
        else :
            self.priceType = orderState['PriceType']
            self.price = orderState['Price']

        # calculate notional value
        self.notionalValue = self.price * self.qty

        # set execution info
        if type (pkt.payload) == ExecutionNotice :
            self.executedQty = int ( pkt.getfieldval('Qty') )
            self.executedPrice = int ( pkt.getfieldval('Price' ) ) / 10000
            self.executedNotionalValue = self.executedQty * self.executedPrice

        # set data id
        if type(pkt) == NoticeCommon :
            self.dataID = pkt.getfieldval('IntProcessing') + pkt.getfieldval('SourceVSNum') + pkt.getfieldval('OrderEntrySeqNum')
        elif type(pkt) == OrderCommon :
            self.dataID = pkt.getfieldval('IntProcessing') + pkt.getfieldval('VSNum') + pkt.getfieldval('OrderEntrySeqNum')


class OrderState():

    def __init__(self ):
        """Assumes pkt is an OrderCommon or NoticeCommon packet"""

        self.state = {}
        self.state['Side'] = None
        self.state['IssudeCode'] = None
        self.state['Qty'] = 0
        self.state['OpenQty'] = 0
        self.state['PriceType'] = None
        self.state['Price'] = 0
        self.state['OpenNV'] = 0
        self.state['PendingOpenNV'] = 0
        self.state['CumQty'] = 0
        self.state['AvgPrice'] = 0
        self.state['CumNV'] = 0
        self.state['LastEvent'] = None

        self.state['PreviousOpenNV'] = 0
        self.state['PreviousCumNV'] = 0

        self.eventData = []

    def update( self, pkt, client, securityInfo ) :
        """Updates the order state structure with the info implied in the packet. Assumes pkt is an OrderCommon or NoticeCommon packet"""

        eventData = EventData ()
        eventData.update(pkt, securityInfo, self.state)
        self.__update(eventData)

        client.update( self.state )

        if self.state['LastEvent'] == 'ModOrder' :
            self.state['PreviousOpenNV'] = self.state['PendingOpenNV']
        else :
            self.state['PreviousOpenNV'] = self.state['OpenNV']

        self.state['PreviousCumNV'] = self.state['CumQty']

        self.eventData.append(eventData)

    def __update (self, eventData ) :
        """Updating order status"""

        self.state['LastEvent'] = eventData.eventType
        self.state['Side'] = eventData.side
        self.state['IssudeCode'] = eventData.issueCode

        if not eventData.eventType in [ 'ModOrder' ] :
            self.state['Qty'] = eventData.qty
            self.state['PriceType'] = eventData.priceType
            self.state['Price'] = eventData.price

        if eventData.executedQty > 0 :
            self.state['CumNV'] += eventData.executedQty * eventData.executedPrice
            self.state['CumQty'] += eventData.executedQty
            self.state['AvgPrice'] = self.state['CumNV'] / self.state['CumQty']

        if eventData.eventType in [ 'CancelResultNotice', 'InvalidationResultNotice', \
                                     'NewOrderAcceptanceError', 'NewOrderRegistrationError' ] :
            self.state['OpenQty'] = 0
            self.state['OpenNV'] = 0
        else :
            self.state['OpenQty'] = self.state['Qty'] - self.state['CumQty']
            self.state['OpenNV'] = self.state['OpenQty'] * self.state['Price']

        if eventData.eventType in [ 'ModOrder' ] :
            self.state['PendingOpenNV'] = ( eventData.qty - self.state['CumQty'] ) * eventData.price



class ClientState():

    def __init__(self):
        """Assumes Client has not initial position"""
        self.longOpenMV = 0
        self.shortOpenMV = 0
        self.longMV = 0
        self.shortMV = 0
        self.longRMV = 0
        self.shortRMV = 0
        self.GMV = 0
        self.GRMV = 0
        self.netMV = 0
        self.netRMV = 0

    def update(self, orderState ):
        """Updating client position"""

        if orderState['Side'] == '3' :
            if orderState['LastEvent'] == 'ModOrder' :
                self.longOpenMV += orderState['PendingOpenNV'] - orderState['PreviousOpenNV']
            else :
                self.longOpenMV += orderState['OpenNV'] - orderState['PreviousOpenNV']

            self.longRMV += orderState['CumNV'] - orderState['PreviousCumNV']
            self.longMV = self.longOpenMV + self.longRMV

        elif orderState['Side'] == '1' :
            if orderState['LastEvent'] == 'ModOrder' :
                self.shortOpenMV += orderState['PendingOpenNV'] - orderState['PreviousOpenNV']
            else :
                self.shortOpenMV += orderState['OpenNV'] - orderState['PreviousOpenNV']

            self.shortRMV += orderState['CumNV'] - orderState['PreviousCumNV']
            self.shortMV = self.shortOpenMV + self.shortRMV

        self.GMV = self.longMV + self.shortMV
        self.GRMV = self.longRMV + self.shortRMV
        self.netMV = self.longMV - self.shortMV
        self.netRMV = self.longRMV - self.shortRMV

    def getNotional(self):
        """Providing Dict Object for notional value info"""
        notionalData = {}
        notionalData['LongOpenMV'] = "{:,}".format(self.longOpenMV)
        notionalData['ShortOpenMV'] = "{:,}".format(self.shortOpenMV)
        notionalData['LongMV'] = "{:,}".format(self.longMV)
        notionalData['ShortMV'] = "{:,}".format(self.shortMV)
        notionalData['LongRMV'] = "{:,}".format(self.longRMV)
        notionalData['ShortRMV'] = "{:,}".format(self.shortRMV)
        notionalData['GMV'] = "{:,}".format(self.GMV)
        notionalData['GRMV'] = "{:,}".format(self.GRMV)
        notionalData['NetMV'] = "{:,}".format(self.netMV)
        notionalData['NetRMV'] = "{:,}".format(self.netRMV)
        return notionalData


class SecurityData() :

    def __init__(self, sdata):
        """Setting up security data """
        self.symbol = sdata['Symbol']
        self.exchange = sdata['Exchange']
        self.basePrice = 0
        self.lastPrice = 0
        self.maxPrice = 0
        self.minPrice = 0
        self.lotSize = 0
        self.maxLot = 0
        self.tickGroup = 0
        self.marketprice = 0
        self.mktPriceTolerance = sdata['MktPriceTolerance']
        if sdata['BasePrice'] != '' :
            self.basePrice = float(sdata['BasePrice'])
        if sdata['Last'] != '' :
            self.lastPrice = float(sdata['Last'])
        if sdata['MaxPrice'] != '' :
            self.maxPrice = float(sdata['MaxPrice'])
        if sdata['MinPrice'] != '' :
            self.minPrice = float(sdata['MinPrice'])
        if sdata['LotSize'] != '' :
            self.lotSize = int(sdata['LotSize'])
        if sdata['MaxLots'] != '' :
            self.maxLot = int(sdata['MaxLots'])
        if sdata['TickGroup'] != '' :
            self.tickGroup = int(sdata['TickGroup'])
        if self.lastPrice != 0 :
            self.marketprice = self.lastPrice
        else :
            self.marketprice = self.basePrice

class RestrictionData() :

    def __init__(self, rdata):
        """Setting up restriction data """
        self.buy = rdata['Buy']
        self.sell = rdata['Sell']
        self.shortSell = rdata['ShortSell']
        self.shortSellExempt = rdata['ShortSellExempt']
        self.symbol = rdata['Symbol']
        self.exchange = rdata['Exchange']
        self.client = rdata['Client']
        self.secType = rdata['SecType']

class LimitsData() :

    def __init__(self, ldata):
        """Setting up limits  data """
        self.client = ldata['Client']
        self.exchange = ldata['Exchange']
        self.securityType = ldata['SecurityType']
        if ldata['MaxNV'] != '' :
            self.maxNV = int ( ldata['MaxNV'] )
        else :
            self.maxNV = 0
        if ldata['MaxDailyValue'] != '' :
            self.maxDailyValue = int(ldata['MaxDailyValue'])
        if ldata['MinNetValue'] != '' :
            self.minNetValue = int(ldata['MinNetValue'])
        if ldata['MaxNetValue'] != '' :
            self.maxNetValue = int(ldata['MaxNetValue'])
        self.buyRestricted = ldata['BuyRestricted']
        self.sellRestricted = ldata['SellRestricted']
        self.shortRestricted = ldata['ShortRestricted']
        self.shortExemptRestricted = ldata['ShortExemptRestricted']
        self.maxDuplicateOrders = int(ldata['MaxDupOrders']) if ldata['MaxDupOrders'] != '' else None
        self.maxOrders = int(ldata['MaxOrders']) if ldata['MaxOrders'] != '' else None

class TickSizeData() :
    def __init__(self, tdata):
        """Setting up tickSize data """
        if tdata['TickSize'] != '' :
            self.tickSize = float( tdata['TickSize'])

class TickSizeTable() :
    def __init__(self):
        """Setting up tickSize table """
        self.tickSizeTable = {}

    def addTickSize(self, priceFloor, tickSize ):
        self.tickSizeTable[int(priceFloor)] = tickSize

    def checkTickSize(self, price ):
        for priceFloor in sorted ( self.tickSizeTable.keys(), reverse=True ):
            if ( price >= priceFloor ) :
                return self.tickSizeTable[priceFloor].tickSize

    def getValidPrice (self, price, up=1 ):
        if ( price % self.checkTickSize(price) == 0 ):
            return price
        else :
            while not ( price % self.checkTickSize(price) == 0 ) :
                if ( up ==1 ) :
                    price += self.checkTickSize(price) - (price % self.checkTickSize(price))
                else :
                    price -= self.checkTickSize(price) - (price % self.checkTickSize(price))
            return price

def getSodData(csvPath, sodType, fieldkey, fieldkey2=None, clientID=None ):
    CSVData = {}
    if not os.path.isfile(csvPath):
        return CSVData
    CSV = csv.reader(open(csvPath, 'r'), delimiter=',')
    header = 0
    headers = []
    for row in CSV :
        i = 0
        RowData = {}
        for field in row :
            if header == 0 :
                headers.append(field)
            else :
                if len(headers) > i :
                    key = headers[i]
                    RowData[key]=field
                    i += 1
        if header != 0 :
            if sodType == 'Security' :
                CSVData[RowData[fieldkey]] = SecurityData(RowData)
            elif sodType == 'Restriction' :
                CSVData[(RowData[fieldkey], RowData[fieldkey2])] = RestrictionData(RowData)
            elif sodType == 'Limit' :
                CSVData[RowData[fieldkey]] = LimitsData(RowData)
            elif sodType == 'TickSize' :
                CSVData['%s:%s' % (RowData[fieldkey], RowData[fieldkey2])] = TickSizeData(RowData)

        header += 1
    if fieldkey == 'PriceFloor' :
        lastTickSize = 0
        tickSizeTable = {}
        CSVDataKey = {}

        for key in CSVData.keys() :
            #'PriceFloor': 'Group'
            Keys = key.split(':')
            print 'Group = ' + Keys[1] + ' PriceFloor = ' + Keys[0]
            if not tickSizeTable.has_key(int(Keys[1])):
                tickSizeTable[int(Keys[1])] = TickSizeTable()
            tickSizeTable[int(Keys[1])].addTickSize(Keys[0], CSVData[key] )

        return tickSizeTable

    return CSVData



class App():

    __instance__ = None

    def __init__(self, cfg, logPath, cb_notify):

        print '\nArrowhead Client\nCopyright Fusion Systems 2013\n'
        ## passin directly
        CFG = cfg
        assert callable(cb_notify)
        self.cb_notify = cb_notify


        print 'Loaded configuration from %s:' % cfg
        pprint.pprint(CFG)

        self.logPath = logPath
        self.state = {}
        self.sessions = {}
        self.adminLinkUp = {}
        self.logoutRespRecvd = {}
        self.loginRespRecvd = {}
        self.preLogoutRespRecvd = {}
        self.gotDisconnected = {}
        self.gotConnected = {}
        self.sendTimer = {}
        self.recvTimer = {}
        self.sendTimerThread = {}
        self.recvTimerThread = {}
        self.recvThread = {}
        self.socket = {}
        self.hbtInterval = {}
        self.hbtRecvInterval = {}
        self.bindWaitTime = {}
        self.logName = '';
        self.vsNums = []
        self.securities = {}
        self.restrictions = {}
        self.limits = {}
        self.tickSize = {}
        self.acceptNumberFromIntProcessing = {}
        self.gotOpLinkUp = {}

        #import pdb;pdb.set_trace()
        for vsNum in CFG.keys() :
            if vsNum == 'clientID' :
                self.state['clientID'] = CFG[vsNum]
                continue
            if vsNum == 'logLevel' :
                continue
            if vsNum == 'securityCSV' :
                self.state['securityCSV'] = CFG[vsNum]
                continue
            if vsNum == 'restrictionCSV' :
                self.state['restrictionCSV'] = CFG[vsNum]
                continue
            if vsNum == 'limitsCSV' :
                self.state['limitsCSV'] = CFG[vsNum]
                continue
            if vsNum == 'tickSizeCSV' :
                self.state['tickSizeCSV'] = CFG[vsNum]
                continue
            if vsNum == 'prefix' :
                self.state['prefix'] = CFG[vsNum]
                continue
            if vsNum == 'opStart' :
                self.state['opStart'] = CFG[vsNum]
                continue

            self.logName += vsNum
            self.vsNums.append(vsNum)
            self.sessions[vsNum] = {}
            self.sessions[vsNum]['ip'] = CFG[vsNum]['remoteIp']
            self.sessions[vsNum]['port'] = CFG[vsNum]['remotePort']
            self.sessions[vsNum]['localIp'] = CFG[vsNum]['localIp']
            self.sessions[vsNum]['localPort'] = CFG[vsNum]['localPort']
            self.sessions[vsNum]['vsNum'] = CFG[vsNum]['vsNum']
            self.sessions[vsNum]['participantCode'] = CFG[vsNum]['participantCode']
            self.sessions[vsNum]['msgSeqNum'] =  1 
            self.sessions[vsNum]['samsn'] = '    1000'
            self.sessions[vsNum]['armsn'] = '       1'
            self.logoutRespRecvd[vsNum] = False
            self.adminLinkUp[vsNum] = False
            self.loginRespRecvd[vsNum] = False
            self.preLogoutRespRecvd[vsNum] = False
            self.gotDisconnected[vsNum] = False
            self.gotConnected[vsNum] = False
            self.sendTimer[vsNum] = 0
            self.recvTimer[vsNum] = 0
            self.hbtInterval[vsNum] = CFG[vsNum]['hbtInterval']
            self.hbtRecvInterval[vsNum] = CFG[vsNum]['hbtTimeout']
            self.bindWaitTime[vsNum] = CFG[vsNum]['bindWaitTime']
            self.sendTimerThread[vsNum] = None
            self.recvTimerThread[vsNum] = None
            self.recvThread[vsNum] = None
            self.socket[vsNum] = None

            self.sessions[vsNum]['orderEntrySeqNum'] = 0
            self.sessions[vsNum]['recvdMsgSeqNum'] = 0
            self.sessions[vsNum]['acceptNoticeSeqNum'] = 0
            self.sessions[vsNum]['execNoticeSeqNum'] = 0
            self.sessions[vsNum]['lineStatus'] = None
            self.gotOpLinkUp[vsNum] = False

            print 'set config for ' + self.sessions[vsNum]['vsNum']
        if self.state['clientID'] :
            self.logName  = self.state['clientID']
        self.outStats = {}
        self.inStats = {}
        self.Events = {}
        self.Orders = {}

        self.requests = []
        self.notices = []
        self.adminIn = []
        self.adminOut = []
        self.espIn = []
        self.espOut = []
        self.client = ClientState()
        self.cfg = {}
        self.cfg['SessionReject'] = '00'

        self.numErrorsFound = 0
        self.msgSeqNumErrorsFound = False
        self.acceptSeqNumErrorsFound = False
        self.execSeqNumErrorsFound = False

        self.fileFormatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s:%(funcName)s - %(message)s')
        self.consoleFormatter = logging.Formatter('%(levelname)s:\t%(message)s')
        self.consoleLogger = logging.StreamHandler()
        self.consoleLogger.setLevel(logging.DEBUG)
        self.consoleLogger.setFormatter(self.consoleFormatter)
        logging.getLogger('').addHandler(self.consoleLogger)

        # assume the root of path is valid
        if not os.path.exists(logPath):
            os.mkdir(logPath)

        # roll logs
        if not sys.argv == [] and not sys.argv[0]=='':
            self.fileBase = sys.argv[0]
        else:
            self.fileBase = 'ahd_client'
        # traffic
        self.trafficFileBase = 'traffic'

        if os.path.exists(logPath + '/%s-%s.log' % (self.fileBase, self.logName)):
            i = 2
            while os.path.exists(logPath + '/%s-%s-%d.log' % (self.fileBase, self.logName, i)):
                i += 1
            os.rename(logPath + '/%s-%s.log' % (self.fileBase, self.logName),
                      logPath + '/%s-%s-%d.log' % (self.fileBase, self.logName, i))

        if os.path.exists(logPath + '/%s.log' % self.trafficFileBase):
            i = 2
            while os.path.exists(logPath + '/%s.%d.log' % (self.trafficFileBase, i)):
                i += 1
            os.rename(logPath + '/%s.log' % (self.trafficFileBase),
                      logPath + '/%s.%d.log' % (self.trafficFileBase,  i))

        self.fileLogger = logging.FileHandler(filename = os.path.join(logPath ,'%s.log' % self.logName))

        self.trafficHandler = open(logPath + '/%s.log' % (self.trafficFileBase), 'w' )

        print '\nLogging will be written to ' + logPath + '/%s-%s.log' % \
            (self.fileBase, self.logName)
        print '\nTrraffic will be written to ' + logPath + '/%s.log' % (self.trafficFileBase)
        print
        self.fileLogger.setLevel(logging.DEBUG)
        self.fileLogger.setFormatter(self.fileFormatter)
        logging.getLogger('').addHandler(self.fileLogger)
        self.logger = logging.getLogger('Client logger')
        self.logger.setLevel(CFG['logLevel'])

        if self.state['securityCSV'] :
            self.info('loading Security data from %s' % self.state['securityCSV'])
            self.securities = getSodData( self.state['securityCSV'], 'Security', 'Symbol' )
        if self.state['restrictionCSV'] :
            self.info('loading Restriction data from %s' % self.state['restrictionCSV'])
            self.restrictions = getSodData( self.state['restrictionCSV'], 'Restriction', 'Client', 'Symbol' )
        if self.state['limitsCSV'] :
            self.info('loading Limits data from %s' % self.state['limitsCSV'])
            self.limits = getSodData( self.state['limitsCSV'], 'Limit', 'Client' )
        if self.state['tickSizeCSV'] :
            self.info('loading tickSize data from %s' % self.state['tickSizeCSV'])
            self.tickSize = getSodData( self.state['tickSizeCSV'] , 'TickSize', 'PriceFloor', 'Group' )

    def start(self, loadSeqNoFile=None):
        """ Establishes the ESP, Admin, and Op links with the exchange and starts the protocol threads. This should always be called (by the user) before sending orders. """
        self.info("Starting ...")
        try :
            if loadSeqNoFile :
                self.loadSeqNo(loadSeqNoFile)
        except :
            self.warning("Failed to load seqNo file")
            return  False

        self.info("Starting ...")
        for vsNum in self.vsNums :
            self.socket[vsNum] = socket.socket()
            self.socket[vsNum].setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1 )
            self.gotConnected[vsNum] = False

            # Est connection
            self.info('Connecting to %s:%s from %s:%s' %
                    (self.sessions[vsNum]['ip'], self.sessions[vsNum]['port'],
                     self.sessions[vsNum]['localIp'], self.sessions[vsNum]['localPort']))

            while not self.gotConnected[vsNum]:
                try:
                    self.socket[vsNum].bind((self.sessions[vsNum]['localIp'], self.sessions[vsNum]['localPort']))
                except socket.error, e:
                    if e.args[0] == errno.EADDRINUSE:
                        self.warning('Socket binding error, address in use, retrying in %d secs...' %
                                         self.bindWaitTime[vsNum])
                        sleep(self.bindWaitTime[vsNum])
                        continue
                self.gotConnected[vsNum] = True
                time.sleep(0.1)

            try:
                self.socket[vsNum].connect((self.sessions[vsNum]['ip'], self.sessions[vsNum]['port']))
            except socket.error:
                self.__exception('Connection error, exiting')
                sys.exit(0)

            self.recvTimerThread[vsNum] = Thread(target=self.__recvTimerThread, args=(vsNum,))
            self.recvTimerThread[vsNum].setDaemon(True)
            self.recvTimerThread[vsNum].start()
            self.recvThread[vsNum] = Thread(target=self.__recvThread, args=(vsNum,))
            self.recvThread[vsNum].setDaemon(True)
            self.recvThread[vsNum].start()

            self.info('%s : Connected' % vsNum)

            # temorarily
            # self.sendOpStartRequest(vsNum)

            # Est. ESP link
            self.info('%s : Establishing ESP link...' % vsNum)
            self.sendPacket(LoginRequest(),vsNum)

            while not self.loginRespRecvd[vsNum] :
                self.info('%s : Waiting for login response' % vsNum)
                time.sleep(0.1)

            self.info('%s : ESP link established' % vsNum)

            # Est. Admin link
            self.info('%s : Establishing Admin link...' % vsNum)
            while not self.adminLinkUp[vsNum] :
                self.info('%s : Waiting for MarketAdmin' % vsNum) 
                time.sleep(0.1)

            self.info('Admin link established')

            self.info('%s : Starting Send Hbt, Recv Hbt, and Recv threads' % vsNum)
            self.sendTimerThread[vsNum] = Thread(target=self.__sendTimerThread, args=(vsNum,))
            self.sendTimerThread[vsNum].setDaemon(True)
            self.sendTimerThread[vsNum].start()

            # wait to get the op start response
            # skip messages if need to
            if self.state['opStart']:
                self.info('Establishing Operations link...')
                self.sendOpStartRequest(vsNum)
                time.sleep(1.0)
                while not self.gotOpLinkUp[vsNum]:
                    # Est. Operations link
                    self.info('Waiting to Establish Operations link...')
                    time.sleep(1.0)

            self.info(self.sessions[vsNum])
            sleep(0.5)
            self.info('%s : App is ready for operation' % vsNum)
        self.info('App is ready for operation')

    def sessionStop(self, vsNum):

        self.info ('Received logout request from the exchange, sending logout and terminate the process: %s' % vsNum) 
        try:
            self.sendPacket(LogoutResponse(),vsNum)
        except:
            self.error('Send error duringlogout')
            return

        self.info ('Closing socket: %s' % vsNum)
        self.socket[vsNum].close()
        self.gotConnected[vsNum] = False
        self.logoutRespRecvd[vsNum] = True

    def suddenStop(self, vsNum):
        """ Does the sudden session close without prelogout/logout handshake"""
        l_onoff = 1
        l_linger = 0
        self.info('Doing Sudden Stopping')
        sleep(0.5)
        self.socket[vsNum].setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
            struct.pack('ii', l_onoff, l_linger))
        self.socket[vsNum].close()
        self.info('socket should be closed')

    def stop(self):
        """ Does the prelogout/logout handshake with the exchange and closes the TCP socket. This should always be called by the user before exiting the application."""

        self.info('Stopping application')
        sleep(0.5)
        for vsNum in self.vsNums :
            if not self.gotConnected[vsNum] or \
                    (self.gotConnected[vsNum] and self.gotDisconnected[vsNum]):
                return

        # Do pre-logout
        for vsNum in self.vsNums :
            try:
                self.sendPacket(PreLogoutRequest(),vsNum)
            except:
                self.error('Send error during pre logout')
                return

            sleep(1)
            if not self.preLogoutRespRecvd[vsNum]:
                self.info('%s : Awaiting pre-logout response' % vsNum)
                try:
                    msg = self.__recvPacket(vsNum)
                except:
                    self.error('Recv error during pre logout')
                    return

                p = ESPCommon(msg)

                if not self.sessions[vsNum]['recvdMsgSeqNum'] + 1 == int(p.getfieldval('MsgSeqNum')):
                    self.error('Expected MsgSeqNum %d but got %d' %
                               (self.sessions[vsNum]['recvdMsgSeqNum']+1, int(p.getfieldval('MsgSeqNum'))))
                    self.numErrorsFound += 1
                    self.msgSeqNumErrorsFound = True
                # should request a resend, but since that's blocked in Raw, just accept num
                else:
                    self.sessions[vsNum]['recvdMsgSeqNum'] = int(p.getfieldval('MsgSeqNum'))

                if int(self.sessions[vsNum]['samsn']) < int(p.getfieldval('SAMSN')):
                    self.sessions[vsNum]['samsn'] = p.getfieldval('SAMSN')
                # TODO: log error if got a lower SAMSN??

                if p.getfieldval('MsgType') == WENUMS['ESPMsgTypeDown']['PreLogoutResponse']:
                    # TODO: confirm ARMSN sequence numbers
                    self.sessions[vsNum]['armsn'] = p.getfieldval('ARMSN')
                    self.preLogoutRespRecvd[vsNum] = True
                    self.info('%s : Got pre-logout response' % vsNum)
                else:
                    self.error('ERROR: Expected PreLogoutResponse, instead got')
                    self.error(p)
                    return
            else:
                self.info('%s : Pre-logout response received already. Continuing logout...' % vsNum)

            # Do logout
            self.sendPacket(LogoutRequest(),vsNum)

            self.info('%s : Awaiting logout response' % vsNum)
            try:
                msg = self.__recvPacket(vsNum)
            except:
                # TODO: handle case?
                pass

            p = ESPCommon(msg)

            if not self.sessions[vsNum]['recvdMsgSeqNum'] + 1 == int(p.getfieldval('MsgSeqNum')):
                self.error('Expected MsgSeqNum %d but got %d' %
                           (self.sessions[vsNum]['recvdMsgSeqNum']+1, int(p.getfieldval('MsgSeqNum'))))
                self.numErrorsFound += 1
                self.msgSeqNumErrorsFound = True
            # should request a resend, but since that's blocked in Raw, just accept num
            else:
                self.sessions[vsNum]['recvdMsgSeqNum'] = int(p.getfieldval('MsgSeqNum'))


            if p.getfieldval('MsgType') == WENUMS['ESPMsgTypeDown']['LogoutResponse']:
                self.logoutRespRecvd[vsNum] = True
                self.info('%s : Got logout response' % vsNum)
                self.info('%s : Closing socket' % vsNum)
                self.socket[vsNum].close()
            else:
                self.error('Expected LogoutResponse, instead got')
                self.error(p)
        self.info("Done")

    def __sendRawPacket(self, packetStr, vsNum):
        """Sends the the literal string, packetStr, on the socket. This is the lowest level of send for the App class and is called by the other send methods. The user will rarely need to call this directly, if ever."""
        msg = str(packetStr)
        msgLen = len(msg)
        totalSent = 0
        while totalSent < msgLen:
            sent = self.socket[vsNum].send(msg[totalSent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalSent = totalSent + sent
        self.trafficHandler.write('%s >> %s\n' % (datetime.now().strftime('%H%M%S%f'), msg ) )
        self.cb_notify(name="send_packet",msg=msg)


    def sendPacket(self, p, vsNum):
        """Embeds admin/order request packet, p, into an ESPCommon packet setting the ESP seq nums, date, time, part code, VSNum, etc and sends on the VS. Direct use of this is not recommended if you are not familiar with the Arrowhead protocol. All send funcs call this to ensure the ESP fields pass validation. p is assumed to be AdminCommon, OrderCommon, or NoticeCommon. This can be used by the user who wants more control over the packet."""

        # TODO: loop and retry if seqnum < samsn
        if self.sessions[vsNum]['msgSeqNum'] < int(self.sessions[vsNum]['samsn']):
            h = ESPCommon()
            h.setfieldval('MsgSeqNum', '%8d' % (self.sessions[vsNum]['msgSeqNum']))
            # h.setfieldval('ARMSN', self.sessions[vsNum]['armsn'])
            h.setfieldval('ARMSN', '%8d' % int(self.sessions[vsNum]['recvdMsgSeqNum']))
            h.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
            h.setfieldval('MsgType', WENUMS['MsgType'][p.name])
            h.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
            h.setfieldval('TransDate', time.strftime("%Y%m%d", time.localtime()))
            h.setfieldval('TransTime',  datetime.now().strftime('%H%M%S%f'))

            pkt = h/p
            try:
                self.__sendRawPacket(pkt, vsNum)
            except Exception:
                self.__exception('Send exception')
                exit()

            if pkt.getfieldval('MsgType') == '40':
                self.requests.append(p)
                self.__fromApp(p)
            elif pkt.getfieldval('MsgType') == '80':
                self.adminOut.append(p)
                self.__fromAdmin(p)
                self.info(p)
            self.espOut.append(pkt)

            self.sessions[vsNum]['msgSeqNum'] += 1
            self.sendTimer[vsNum] = 0
            self.debug('sendPacket(): sent')
            self.debug(pkt)

            return True

        else:
            return False

    # sets the order entry seq num & ordid of order common and sends
    def sendRequest(self, r, vsNum):
        """Sends the OrderCommon packet (new order, mod, cancel) after updating the OrderCommon frame with participant code, VS number, an incrementing Order Entry Seq Num, and ordid (using IntProcessing field). The ordid is constructed as VSNum + OrderEntrySeqNum followed by zeros. Use this if you want more control over the request packet. Direct use not recommeded if you are not familiar with the Arrowhead protocol. """
        self.info('vsNum = %s' % vsNum)
        r.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        r.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        r.setfieldval('OrderEntrySeqNum', '%8d'%(self.sessions[vsNum]['orderEntrySeqNum']))
        #r.setfieldval('OrderEntrySeqNum', '{:>8}'.format(self.sessions[vsNum]['orderEntrySeqNum']))

        # if new order, add order entry ordid and seq num, incr
        if r.getfieldval('IntProcessing') == ("%20s" % ' ') :
            if r.getfieldval('DataClassCode')=='1111' and self.state['prefix'] :
                r.setfieldval('IntProcessing',
                          '%s%08d%s' % (self.state['prefix'] if len(self.state['prefix']) == 6 else self.state['prefix'] + '0'* (6 - len(self.state['prefix'])),

                          self.sessions[vsNum]['orderEntrySeqNum'], self.sessions[vsNum]['vsNum']))
            elif r.getfieldval('DataClassCode')=='1111' and r.getfieldval('IntProcessing') == ( "%20s" % ' ') :
                r.setfieldval('IntProcessing',
                          self.sessions[vsNum]['vsNum'] +
                          '%08d'%(self.sessions[vsNum]['orderEntrySeqNum']) + '000000')
        self.sendPacket(r,vsNum)
        self.info(r)
        #self.consoleLogger.flush()
        self.sessions[vsNum]['orderEntrySeqNum'] += 1
        return r

    def sendNewOrder(self, symbol, qty, side='3', price=None,
                     execCond='0', shortSellFlag='0', propBrokerageClass='0',
                     cashMarginCode='0', stabArbCode='0',
                     ordAttrClass='1', suppMemberClass='0',
                     exchClass='1', mktClass='11',
                     vsNum=None, ordid=None, optional='0000'):
        """Sends a new order request with the specified parameter values. As all new order parameters are setable here, this should be the method used by the user all if not most of the time. While the user needs to be familiar with the new order parameters, lower level settings are handled by this method, making it the quickest and easiest way to submit an order. \n\nsymbol (required) - four-char str, exchange symbol, eg. '1301'\n\nqty (required) - int, whole number of shares, eg. 1000\n\nside - str, AHD enum for side: '1' sell, '3' buy\n\nprice - int or str, as int it is the limit price in whole yen, as str it is the AHD formatted price. Leave unset (None) for market orders\n\nexecCond - str, AHD execution condition\n\nshortSellFlag - str, AHD short sell flag\npropBrokerageClass - str, AHD proprietary/brokerage classification code\n\ncashMarginCode - str, AHD cash margin code\n\nstabArbCode - str, AHD stabilization/arbitrage code\norderAttrClass - str, AHD order attribute classification\n\nsuppMemberClass - str, AHD support member classification\n\nexchClass - str, AHD exchange classificationcode \n\nmktClass - str, AHD market classification code"""
        m = OrderCommon()/NewOrder()

        m.getlayer('OrderCommon').setfieldval('ExchClassCode', exchClass)
        m.getlayer('OrderCommon').setfieldval('MarketClassCode', mktClass)

        m.getlayer('NewOrder').setfieldval('IssueCode', '%-12s'%(symbol))
        if type(qty)  == int:
            m.getlayer('NewOrder').setfieldval('Qty', '%13d'%(qty))
        else:
            m.getlayer('NewOrder').setfieldval('Qty', '%13s'%(qty))
        if not vsNum :
            vsNum=random.choice(self.sessions.keys())

        if side:
            m.getlayer('NewOrder').setfieldval('Side', side)
        if price:
            # if int given, convert to AHD str
            if type(price) == int:
                m.getlayer('NewOrder').setfieldval('Price', '%9d0000' %(price))
            elif type(price) == float:
                m.getlayer('NewOrder').setfieldval('Price', '%13d' %(price*10000))
            else: # else assume string and exact format
                m.getlayer('NewOrder').setfieldval('Price', price)

        if execCond:
            m.getlayer('NewOrder').setfieldval('ExecCond', execCond)
        if shortSellFlag:
            m.getlayer('NewOrder').setfieldval('ShortSellFlag', shortSellFlag)
        if propBrokerageClass:
            m.getlayer('NewOrder').setfieldval('PropBrokerageClass', propBrokerageClass)
        if cashMarginCode:
            m.getlayer('NewOrder').setfieldval('CashMarginCode', cashMarginCode)
        if stabArbCode:
            m.getlayer('NewOrder').setfieldval('StabArbCode', stabArbCode)
        if ordAttrClass:
            m.getlayer('NewOrder').setfieldval('OrdAttrClass', ordAttrClass)
        if suppMemberClass:
            m.getlayer('NewOrder').setfieldval('SuppMemberClass', suppMemberClass)
        if not ordid == None :
            m.getlayer('NewOrder').setfieldval('IntProcessing', '%-20s'%(ordid))

        m.getlayer('NewOrder').setfieldval('Optional', '%4s' % optional)

        return self.sendRequest(m,vsNum)

    def sendMod(self, ordid, symbol, qty=None, price=None,
            execCond = None, exchClass='1', mktClass='11', 
            dataClassCode=None, vsNum=None, optional=None):
        """Sends an order modification request for the specified order.\n\nordid - str or Packet, as str, is the ordid for the order to be modified (ie, the IntProcessing field of the order, as Packet, is the Packet containing the original ord or a previous mod or cancel.\n\nSee help(ahd_client.sendNewOrder) for values of the other parameters."""
        m = OrderCommon()/ModOrder()

        m.getlayer('OrderCommon').setfieldval('ExchClassCode', exchClass)
        m.getlayer('OrderCommon').setfieldval('MarketClassCode', mktClass)

        if dataClassCode :
            m.setfieldval('DataClassCode', '5131')
            if type(ordid) == str:
                m.getlayer('ModOrder').setfieldval('OrderAcceptanceNum', '%-14s'%(ordid))
            elif type(ordid) == OrderCommon:
                m.getlayer('ModOrder').setfieldval('OrderAcceptanceNum', self.acceptNumberFromIntProcessing[ordid.getfieldval('IntProcessing')])
            else: #otherwise assume this is a full AHD packet (ESPCommon type)
                m.getlayer('ModOrder').setfieldval('OrderAcceptanceNum',
                                                self.acceptNumberFromIntProcessing[ordid.getlayer('OrderCommon').getfieldval('IntProcessing')])
        else :
            # decode the ordid
            m.setfieldval('DataClassCode', '9132')
            if type(ordid) == str:
                m.getlayer('ModOrder').setfieldval('IntProcessing', '%-20s'%(ordid))
            elif type(ordid) == OrderCommon:
                m.getlayer('ModOrder').setfieldval('IntProcessing', ordid.getfieldval('IntProcessing'))
            else: #otherwise assume this is a full AHD packet (ESPCommon type)
                m.getlayer('ModOrder').setfieldval('IntProcessing',
                                                ordid.getlayer('OrderCommon').getfieldval('IntProcessing'))
        
        
        m.getlayer('ModOrder').setfieldval('IssueCode', '%-12s'%(symbol))
        if qty:
            if type(qty) == int:
                m.getlayer('ModOrder').setfieldval('Qty', '%13d' % (qty) )
            else :
                m.getlayer('ModOrder').setfieldval('Qty', '%13s' % (qty) )
        if price:
            if type(price) == int:
                m.getlayer('ModOrder').setfieldval('Price', '%9d0000' %(price))
            elif type(price) == float:
                m.getlayer('ModOrder').setfieldval('Price', '%13d' %(price*10000))
            else:
                m.getlayer('ModOrder').setfieldval('Price', price)
        if execCond:
            m.getlayer('ModOrder').setfieldval('ExecCond', execCond)
        if not vsNum :
            vsNum=random.choice(self.sessions.keys())

        if optional :
             m.getlayer('ModOrder').setfieldval('Optional', '%4s' % optional)

        return self.sendRequest(m, vsNum)

    def sendCancel(self, ordid,  symbol=None, 
        exchClass='1', mktClass='11', 
        dataClassCode=None, vsNum=None):
        """Sends an order cancel request for the specified order.\n\nordid - str or Packet, as str, is the ordid for the order to be cancel (ie, the IntProcessing field of the order, as Packet, is the Packet containing the original ord or a previous mod or cancel.\n\nSee help(ahd_client.sendNewOrder) for values of the other parameters."""
        m = OrderCommon()/CancelOrder()

        m.getlayer('OrderCommon').setfieldval('ExchClassCode', exchClass)
        m.getlayer('OrderCommon').setfieldval('MarketClassCode', mktClass)

        if dataClassCode :
            m.setfieldval('DataClassCode', '3121')
            if type(ordid) == str:
                m.getlayer('CancelOrder').setfieldval('OrderAcceptanceNum', '%-14s'%(ordid))
                m.getlayer('CancelOrder').setfieldval('IssueCode', '%-12s'%(symbol))
            elif type(ordid) == OrderCommon:
                m.getlayer('CancelOrder').setfieldval('OrderAcceptanceNum', self.acceptNumberFromIntProcessing[ordid.getfieldval('IntProcessing')])
                m.getlayer('CancelOrder').setfieldval('IssueCode', ordid.getfieldval('IssueCode'))
            else: #otherwise assume this is a full AHD packet (ESPCommon type)
                m.getlayer('CancelOrder').setfieldval('OrderAcceptanceNum',
                                                self.acceptNumberFromIntProcessing[ordid.getlayer('OrderCommon').getfieldval('IntProcessing')])
                m.getlayer('CancelOrder').setfieldval('IssueCode',
                                                ordid.getlayer('OrderCommon').getfieldval('IssueCode'))                                                
        else :
            # decode the ordid
            m.setfieldval('DataClassCode', '7122')
            if type(ordid) == str:
                m.getlayer('CancelOrder').setfieldval('IntProcessing', '%-20s'%(ordid))
                m.getlayer('CancelOrder').setfieldval('IssueCode', '%-12s'%(symbol))
            elif type(ordid) == OrderCommon:
                m.getlayer('CancelOrder').setfieldval('IntProcessing', ordid.getfieldval('IntProcessing'))
                m.getlayer('CancelOrder').setfieldval('IssueCode', ordid.getfieldval('IssueCode'))
            else: #otherwise assume this is a full AHD packet (ESPCommon type)
                m.getlayer('CancelOrder').setfieldval('IntProcessing',
                                                ordid.getlayer('OrderCommon').getfieldval('IntProcessing'))        
                m.getlayer('CancelOrder').setfieldval('IssueCode',
                                                ordid.getlayer('OrderCommon').getfieldval('IssueCode'))
        if not vsNum :
            vsNum=random.choice(self.sessions.keys())

        return self.sendRequest(m, vsNum)

    def sendLoginRequest(self, vsNum) :
        """ Send a login request """
        self.sendPacket(LoginRequest(), vsNum)

    # ESP level message
    def sendRejectMessage(self, vsNum, rejectSeqNum = None, rejectMsgType = None, rejectReasonCode = None ):
        """ Sends an ESP reject message."""
        if not rejectSeqNum :
            rejectSeqNum = self.sessions[vsNum]['recvdMsgSeqNum']-3
        if not rejectMsgType :
            rejectMsgType = '50'
        if not rejectReasonCode :
            rejectReasonCode = '0013'
        m = Reject()
        m.setfieldval('RejectSeqNum', '%8d' % rejectSeqNum) 
        m.setfieldval('RejectMsgType', '%2s' % rejectMsgType) 
        m.setfieldval('RejectReasonCode', '%4s' % rejectReasonCode) 
        self.sendPacket(m, vsNum)

    def sendResendRequest(self, vsNum, startSeqNum = None):
        """ Sends an ESP Resend request. startSeqNum is the starting point, defaults to 3 previous messages received from the exchange."""
        if not startSeqNum:
            startSeqNum = self.sessions[vsNum]['recvdMsgSeqNum']-3
        m = ResendRequest()
        m.setfieldval('StartSeqNum', '%8d' % startSeqNum)
        self.sendPacket(m, vsNum)

    # Admin message
    def sendOpStartRequest(self, vsNum, acceptNoticeSeq=None, execNoticeSeq=None):
        """Sends an operation start request message"""
        m = AdminCommon()/OpStart()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        if acceptNoticeSeq :
            m.setfieldval('AcceptNoticeSeqNum', '%8d' % acceptNoticeSeq)
        else :
            m.setfieldval('AcceptNoticeSeqNum', '%8d' % self.sessions[vsNum]['acceptNoticeSeqNum'])

        if execNoticeSeq :
            m.setfieldval('ExecutionNoticeSeqNum', '%8d' % execNoticeSeq )
        else :
            m.setfieldval('ExecutionNoticeSeqNum', '%8d' % self.sessions[vsNum]['execNoticeSeqNum'])
        self.sendPacket(m, vsNum)

    def sendOpEndRequest(self, vsNum) :
        """Sends an operation end request messages"""
        m = AdminCommon()/OpEnd()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        self.sendPacket(m, vsNum)

    def sendRetransRequest(self, vsNum, startSeqNum = None):
        """Sends an Admin Retransmission request. startSeqNum is the starting accept/exec notice sequence number. Default is the previous (acceptance notice) messages."""
        if not startSeqNum:
            startSeqNum = self.sessions[vsNum]['acceptNoticeSeqNum']-1
        m = AdminCommon()/RetransRequest()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.setfieldval('MarketClassCode', '11')
        m.setfieldval('DataClassCode', '6231')
        m.getlayer('RetransRequest').setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.getlayer('RetransRequest').setfieldval('StartSeqNum', '%8d' % startSeqNum)
        m.getlayer('RetransRequest').setfieldval('NoticeType', '0')
        m.getlayer('RetransRequest').setfieldval('EndSeqNum', '%8d' % (startSeqNum+1))
        self.sendPacket(m, vsNum)

    def sendOrdSeqNumEnq(self, vsNum, targetVsNum=None) :
        """Sends an order sequence number enquiry""" 
        m = AdminCommon()/OrdSeqNumEnq()
        if not targetVsNum :
            targetVsNum = vsNum
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.getlayer('OrdSeqNumEnq').setfieldval('VSNum',targetVsNum)
        self.sendPacket(m, vsNum)

    def sendNoticeSeqNumEnq(self, vsNum, targetVsNum=None) :
        """Sends a notice sequence number enquiry"""  
        m = AdminCommon()/NoticeSeqNumEnq()
        if not targetVsNum :
            targetVsNum = vsNum
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.getlayer('NoticeSeqNumEnq').setfieldval('VSNum',targetVsNum)
        self.sendPacket(m, vsNum)

    def sendOrderSunspendCancelRequest (self, vsNum, targetVsNum=None) :
        """Sends a Order Sunspend/Cancel Request"""
        m = AdminCommon()/OrdSuspensionRequest()
        if not targetVsNum :
            targetVsNum = vsNum
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.setfieldval('TargetVSNum', targetVsNum)
        self.sendPacket(m, vsNum)

    def sendOrderSunspendReleaseRequest (self, vsNum, targetVsNum=None) :
        """Sends a Order Sunspend Release Request"""
        m = AdminCommon()/OrdSuspensionReleaseRequest()
        if not targetVsNum :
            targetVsNum = vsNum
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.setfieldval('TargetVSNum', targetVsNum)
        self.sendPacket(m, vsNum)

    def sendHardLimitSetupRequest (self, vsNum, targetVsNum=None, lmtPerOrder=None,
                                   lmtOnCumOrder=None, intvlForOrder=None,
                                   lmtOnCumExec=None, intvlForExec=None ) :
        """Sends a Hard Limits Setup Request"""
        m = AdminCommon()/HardLimitSetupRequest()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        if not targetVsNum :
            targetVsNum = vsNum
        m.getlayer('HardLimitSetupRequest').setfieldval('VSNum', targetVsNum)
        if lmtPerOrder : 
            m.getlayer('HardLimitSetupRequest').setfieldval('LimitsPerOrder', '%20d' % lmtPerOrder)  
        if lmtOnCumOrder : 
            m.getlayer('HardLimitSetupRequest').setfieldval('LimitsOnCumulOrder', '%20d' % lmtOnCumOrder)  
        if intvlForOrder : 
            m.getlayer('HardLimitSetupRequest').setfieldval('Interval1', '%5d' % intvlForOrder)  
        if lmtOnCumExec : 
            m.getlayer('HardLimitSetupRequest').setfieldval('LimitsOnCumulExec', '%20d' % lmtOnCumExec)  
        if intvlForExec : 
            m.getlayer('HardLimitSetupRequest').setfieldval('Interval2', '%5d' % intvlForExec)  
        self.sendPacket(m, vsNum)

    def sendHardLimitEnquiryRequest(self, vsNum, targetVsNum=None):
        """Sends a Hard Limits Enquiry Request"""
        m = AdminCommon()/HardLimitEnquiryRequest()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        if not targetVsNum :
            targetVsNum = vsNum
        m.setfieldval('TargetVSNum', targetVsNum)
        self.sendPacket(m, vsNum)

    # not valid in 2005 sept 
    def sendProxyRequest(self, vsNum, destVSNum = None):
        """ Sends an Admin Proxy request. destVSNum is the virtual server destination, defaults to the same as the current VS."""
        if not destVSNum:
            destVSNum = self.sessions[vsNum]['vsNum']
        m = AdminCommon()/ProxyRequest()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.setfieldval('MarketClassCode', '11')
        m.setfieldval('DataClassCode', '6241')

        m.getlayer('ProxyRequest').setfieldval('ProxySrcVSNum', self.sessions[vsNum]['vsNum'])
        m.getlayer('ProxyRequest').setfieldval('ProxySrcVSNum', destVSNum)
        m.getlayer('ProxyRequest').setfieldval('AcceptanceSeqNum', '%8d' % self.sessions[vsNum]['acceptNoticeSeqNum'])
        m.getlayer('ProxyRequest').setfieldval('ExecutionSeqNum', '%8d' % self.sessions[vsNum]['execNoticeSeqNum'])
        self.sendPacket(m,vsNum)

    def sendProxyAbortRequest(self, vsNum):
        """ Sends an Admin Proxy Abort request."""
        m = AdminCommon()/ProxyAbortRequest()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.setfieldval('MarketClassCode', '11')
        m.setfieldval('DataClassCode', '6241')

        m.getlayer('ProxyAbortRequest').setfieldval('ProxySrcVSNum', self.sessions[vsNum]['vsNum'])
        self.sendPacket(m,vsNum)

    def sendNoticeDestSetup(self, vsNum, srcVsNum = None):
        """ Sends a Notice Destination Setup request. vsNum is the destination of notices, defaults to the current VS"""
        if not srcVsNum:
            srcVsNum = self.sessions[vsNum]['vsNum']
        m = AdminCommon()/NoticeDestSetupRequest()
        m.setfieldval('ParticipantCode', self.sessions[vsNum]['participantCode'])
        m.setfieldval('VSNum', self.sessions[vsNum]['vsNum'])
        m.setfieldval('ExchClassCode', '1')
        m.setfieldval('MarketClassCode', '11')
        m.setfieldval('DataClassCode', '6291')
        m.getlayer('NoticeDestSetupRequest').setfieldval('VSNum', vsNum)
        self.sendPacket(m, vsNum)

    def __recvPacket(self, vsNum):
        """Receives the raw data on the socket and returns a full AHD message, blocking until that is complete"""
        header = ESPCommon()
        headerLen = len(str(header))
        msg1 = ''
        while len(msg1) < headerLen:
            chunk = self.socket[vsNum].recv(headerLen-len(msg1))
            if chunk == '':
                raise RuntimeError("socket connection broken")
            msg1 = msg1 + chunk
        header = ESPCommon(msg1)

        dataLen = int(header.getfieldval('DataLen'))
        msg2 = ''
        while len(msg2) < dataLen:
            chunk = self.socket[vsNum].recv(dataLen-len(msg2))
            if chunk == '':
                raise RuntimeError("socket connection broken")
            msg2 = msg2 + chunk

        self.trafficHandler.write('%s << %s\n' % (datetime.now().strftime('%H%M%S%f'), msg1+msg2) )
        self.cb_notify(name="recv_packet",msg=msg1+msg2)

        return msg1+msg2

    # Thread to keepalive ESP link
    def __sendTimerThread(self, vsNum):
        self.debug('__sendTimerThread() started')
        while not self.logoutRespRecvd[vsNum]:
            if self.sendTimer[vsNum] > self.hbtInterval[vsNum]:
                self.sendPacket(Heartbeat(), vsNum)
            sleep(1)
            self.sendTimer[vsNum] += 1

    # Thread to monitor ESP link
    def __recvTimerThread(self, vsNum):
        self.debug('__recvTimerThread() started')
        while not self.logoutRespRecvd[vsNum]:
            if self.recvTimer[vsNum] > self.hbtRecvInterval[vsNum]:
                self.sendPacket(LogoutRequest(LogoutReason = '0105'), vsNum)
                break

            sleep(1)
            self.recvTimer[vsNum] += 1

    # thread to recv incoming messages
    def __recvThread(self,vsNum):
        self.debug('__recvThread() started')

        # listen for msgs, but only if not in the (pre) logout process
        while not self.logoutRespRecvd[vsNum] and not self.preLogoutRespRecvd[vsNum]:
            try:
                msg = self.__recvPacket(vsNum)

            except socket.error:
                self.error('Socket error on __recvThread()')
                self.gotDisconnected[vsNum] = True
                break

            self.recvTimer[vsNum] = 0
            p = ESPCommon(msg)

            if not self.sessions[vsNum]['recvdMsgSeqNum'] + 1 == int(p.getfieldval('MsgSeqNum')):
                self.error('Expected MsgSeqNum %d but got %d' %
                           (self.sessions[vsNum]['recvdMsgSeqNum']+1, int(p.getfieldval('MsgSeqNum'))))
                self.numErrorsFound += 1
                self.msgSeqNumErrorsFound = True

            # should request a resend, but since that's blocked in Raw, just accept num
            elif p.getfieldval('MsgType') == self.cfg['SessionReject']:
                self.error('Simulating Session Reject for "%s"' % self.cfg['SessionReject'])
                self.sendRejectMessage(vsNum, int(p.getfieldval('MsgSeqNum')), p.getfieldval('MsgType'), '0009')
                self.cfg['SessionReject'] = '00'
                self.sessions[vsNum]['recvdMsgSeqNum'] = int(p.getfieldval('MsgSeqNum'))            
            else:
                self.sessions[vsNum]['recvdMsgSeqNum'] = int(p.getfieldval('MsgSeqNum'))

            if p.getfieldval('MsgType') in ['11', '12', '13', '14', '15',
                                            '16', '17', '18', '51', '91', '52', '92']:
                self.debug('recv(): %s' % (msg))
                self.debug(p)
            else:
                self.info(p)
                #self.consoleLogger.flush()

            self.sessions[vsNum]['armsn'] = p.getfieldval('ARMSN')
            if int(self.sessions[vsNum]['samsn']) < int(p.getfieldval('SAMSN')):
                self.sessions[vsNum]['samsn'] = p.getfieldval('SAMSN')


            if p.getfieldval('MsgType') == WENUMS['MsgType']['MarketAdmin'] and\
                    'T111' == p.getlayer('AdminCommon').getfieldval('DataClassCode'):
                self.adminLinkUp[vsNum] = True

            # if msg is LogoutResponse, assume this is the conclusion
            # of a valid logout process and notify send/recv threads
            # to stop
            if p.getfieldval('MsgType') == WENUMS['ESPMsgTypeDown']['LoginResponse']:
                self.loginRespRecvd[vsNum] = True

            if p.getfieldval('MsgType') == WENUMS['ESPMsgTypeDown']['LogoutResponse']:
                self.logoutRespRecvd[vsNum] = True

            # if msg is PreLogoutResposne, assume this is the middle of
            # of a valid prelogout process and signal to the stop() func
            # that it doesn't need to wait for this message (again)
            if p.getfieldval('MsgType') == WENUMS['ESPMsgTypeDown']['PreLogoutResponse']:
                self.preLogoutRespRecvd[vsNum] = True

            if p.getfieldval('MsgType') == WENUMS['ESPMsgTypeDown']['LogoutRequest']:
                self.socket[vsNum].close()
                self.gotConnected[vsNum] = False
                self.logoutRespRecvd[vsNum] = True
                # self.sessionStop(vsNum)

            # if is business msg, send to app
            if p.getfieldval('MsgType') == '50':
                self.__toApp(p.payload,vsNum)

            # if is admin msg, send to admin
            elif p.getfieldval('MsgType') == '90':
                self.__toAdmin(p.payload, vsNum)

            else:
                self.espIn.append(p)


    def __toApp(self, p, vsNum=''):
        """ Callback for incoming (to the app) business messages. Assumes p is a NoticeCommon packet """
        self.notices.append(p)
        try:
            ordid = p.getfieldval('IntProcessing') + p.getfieldval('SourceVSNum') + p.getfieldval('OrderEntrySeqNum')
            intProcess = p.getfieldval('IntProcessing')
            issueCode = p.getfieldval('IssueCode').strip()

            if type(p.payload) in [NewOrderAcceptanceNotice, NewOrderAcceptanceError] :
                self.acceptNumberFromIntProcessing[intProcess] = p.getfieldval('OrderAcceptanceNum')
        except Exception,e:
            #self.warning('Got notice without IntProcessing field, ignoring')
            self.warning('Got notice without required field, ignoring : %s' % e )
            return

        if issueCode in self.securities :
            securityInfo = self.securities[issueCode]
            if ordid in self.Events:
                self.Events[ordid].update(p )
            else:
                self.Events[ordid] = EventState(p)
            if intProcess in self.Orders:
                self.Orders[intProcess].update(p, self.client, securityInfo )
            else:
                self.Orders[intProcess] = OrderState()
                self.Orders[intProcess].update(p, self.client, securityInfo )
        else :
            if ordid in self.Events:
                self.Events[ordid].update(p )
            else:
                self.Events[ordid] = EventState(p)


        # if this is an acceptance-related notice and
        # we've received an acceptNoticeSeqNum previously
        # then verify the acceptNoticeSeqNum
        if p.getfieldval('DataClassCode') in ['A111', 'B131', 'B121',
                                              'C119', 'D139', 'D129',
                                              'A191']:
            if self.sessions[vsNum]['acceptNoticeSeqNum']:
                if not self.sessions[vsNum]['acceptNoticeSeqNum'] + 1 == \
                        int(p.getfieldval('NoticeSeqNum')):
                    self.error('Expected acceptNoticeSeqNum %d but got %d' %
                               (self.sessions[vsNum]['acceptNoticeSeqNum']+1,
                                int(p.getfieldval('NoticeSeqNum'))))
                    self.numErrorsFound += 1
                    self.acceptSeqNumErrorsFound = True
            self.sessions[vsNum]['acceptNoticeSeqNum'] = int(p.getfieldval('NoticeSeqNum'))
        # this is an execution related notice
        # verify exec related notice seq num
        else:
            if self.sessions[vsNum]['execNoticeSeqNum']:
                if not self.sessions[vsNum]['execNoticeSeqNum'] + 1 == \
                        int(p.getfieldval('NoticeSeqNum')):
                    self.error('Expected execNoticeSeqNum %d but got %d' %
                               (self.sessions[vsNum]['execNoticeSeqNum']+1,
                                int(p.getfieldval('NoticeSeqNum'))))
                    self.numErrorsFound += 1
                    self.execSeqNumErrorsFound = True
            self.sessions[vsNum]['execNoticeSeqNum'] = int(p.getfieldval('NoticeSeqNum'))

        # record stats
        if p.payload.name not in self.inStats:
            self.inStats[p.payload.name] = 1
        else:
            self.inStats[p.payload.name] += 1


    def __fromApp(self, p):
        """ Callback for outgoing business messages. Assumses p is an OrderCommon packet """

        # add p to order state
        # if response already there, add at the front of the list

        ordid = p.getfieldval('IntProcessing') +  p.getfieldval('VSNum') + p.getfieldval('OrderEntrySeqNum')
        intProcess = p.getfieldval('IntProcessing')
        issueCode = p.getfieldval('IssueCode').strip()
        if issueCode in self.securities :
            securityInfo = self.securities[issueCode]
            if ordid in self.Events:
                self.Events[ordid].trail = \
                [EventState(p)] + self.Events[ordid].trail
            else:
                self.Events[ordid] = EventState(p)

            if not intProcess in self.Orders :
                self.Orders[intProcess] = OrderState()

            self.Orders[intProcess].update(p, self.client, securityInfo )

        else :
            if ordid in self.Events:
                self.Events[ordid].trail = \
                [EventState(p)] + self.Events[ordid].trail
            else:
                self.Events[ordid] = EventState(p)



        # record stats
        if p.payload.name not in self.outStats:
           self.outStats[p.payload.name] = 1
        else:
            self.outStats[p.payload.name] += 1


    def __toAdmin(self, p, vsNum):
        self.adminIn.append(p)
        if 'T211' == p.getfieldval('DataClassCode') :
            self.info(p)
            if int(p.getfieldval('OrderEntrySeqNum')) != self.sessions[vsNum]['orderEntrySeqNum'] :
                self.info('Execpected orderEntrySeqNum of %s, instead got %s' % ( self.sessions[vsNum]['orderEntrySeqNum'], p.getfieldval('OrderEntrySeqNum') ))
            self.sessions[vsNum]['orderEntrySeqNum'] = int(p.getfieldval('OrderEntrySeqNum'))
            self.sessions[vsNum]['orderEntrySeqNum'] += 1
            self.gotOpLinkUp[vsNum] = True
            self.info('Op link established')

        elif 'T221' == p.getfieldval('DataClassCode'):
            self.info(p)
            self.gotOpLinkUp[vsNum] = False

    def __fromAdmin(self, p):
        pass


    def __showPacket(self, p, indent=3, lvl="", label_lvl=""):
        """Prints, to a returned str, a hierarchical view of the packet. "indent" = the size of indentation for each layer."""
        ct = conf.color_theme
        string =  "%s%s %s %s\n" % (label_lvl,
                              ct.punct("###["),
                              ct.layer_name(p.name),
                              ct.punct("]###"))

        for f in p.fields_desc:
            if isinstance(f, ConditionalField) and not f._evalcond(p):
                continue
            if isinstance(f, Emph) or f in conf.emph:
                ncol = ct.emph_field_name
                vcol = ct.emph_field_value
            else:
                ncol = ct.field_name
                vcol = ct.field_value
            fvalue = p.getfieldval(f.name)
            if (isinstance(fvalue, Packet) or
                (f.islist and f.holds_packets and type(fvalue) is list)):
                line = "%s  \\%-10s\\" % (label_lvl+lvl, ncol(f.name))
                string += line + '\n'
                string.append
                fvalue_gen = SetGen(fvalue,_iterpacket=0)
                for fvalue in fvalue_gen:
                    fvalue.__showPacket(indent=indent, label_lvl=label_lvl+lvl+"   |")
            else:
                begn = "%s  %-10s%s " % (label_lvl+lvl,
                                         ncol(f.name),
                                         ct.punct("="),)
                reprval = f.i2repr(p,fvalue)
                if type(reprval) is str:
                    reprval = reprval.replace("\n", "\n"+" "*(len(label_lvl)
                                                              +len(lvl)
                                                              +len(f.name)
                                                              +4))
                line = "%s%s" % (begn,vcol(reprval))
                string += line + '\n'
        if not type(p.payload) == scapy.packet.NoPayload:
            string += self.__showPacket(p.payload, indent=indent,
                                      lvl=lvl+(" "*indent*p.show_indent),
                                      label_lvl=label_lvl) + '\n'
        return string


    def __showPacket2(self, p):
        """Prints, to a returned str, a hierarchical view of an assembled version of the packet, so that automatic fields are calculated (checksums, etc.)"""
        return self.__showPacket(p.__class__(str(p)))

    def showRequests(self):
        """Prints in human readable form the list of requests sent"""
        for i in range(len(self.requests)):
            self.requests[i].show2()

    def showNotices(self):
        """Prints in human readable form the list of notices received"""
        for i in range(len(self.notices)):
            self.notices[i].show2()

    def showStats(self):
        self.info('Outbound stats:\n%s', self.outStats)
        self.info('Inbound stats:\n%s', self.inStats)

    def testReport(self):

        foundError = False
        self.info ('Start testReport')
        # roll test report files
        if os.path.exists(self.logPath + '/results-%s-%s.csv' %
                          (self.fileBase, self.logName )):
            self.info ('Start testReport: path exists')
            i = 2
            while os.path.exists(self.logPath + '/results-%s-%s-%d.csv' %
                                 (self.fileBase, self.logName, i) ) :
                i += 1
            os.rename(self.logPath + '/results-%s-%s.csv' %
                      (self.fileBase, self.logName ),
                      self.logPath + '/results-%s-%s-%d.csv' %
                      (self.fileBase, self.logName, i ))

        f = open(self.logPath + '/results-%s-%s.csv' %
                 (self.fileBase, self.logName), 'w' )
        self.info('Writing test report to ' + self.logPath + '/results-%s-%s.csv' %
                    (self.fileBase, self.logName ))

        # header
        f.write('Serial Num, Test Case Name, Request Type, Message, Expected Response Type, Expected Reason Code, Response Type, Reason Code, Pass/Fail, Orig Msg\n')

        # for all orders, write expected a values and received
        for s in self.Events.values():

            # ignore unsolicited notices, solicited = first element in trail is new order
            if type(s.trail[0]) == OrderCommon:
                s.request = s.trail[0].payload.name

                # update the response record
                if len(s.trail)>1:
                    s.response = s.trail[1].payload.name
                else:
                    s.response = 'None'

                if (not s.expectedReasonCode or s.expectedReasonCode==s.reasonCode) and \
                        (not s.expectedResponse or s.expectedResponse==s.response):
                    passes = 'OK'
                else:
                    passes = 'FAIL'
                    foundError = True

                try:
                    f.write('%s,%s,%s,\"%s\",%s,%s,%s,%s,%s,\"%s\"\n' % \
                                (s.serialNum, s.testCaseName, s.request,
                                 self.__showPacket(s.trail[0]),
                                 s.expectedResponse, s.expectedReasonCode,
                                 s.response, s.reasonCode,
                                 passes, str(s.trail[0])))
                except Exception:
                    print 'Got exception while writing test report'
                    print s.trail

        return foundError

    def expect(self, order, responseType, reasonCode, testCaseName=None, serialNum=None):
        try:
            ordid = order.getfieldval('IntProcessing') + order.getfieldval('VSNum') + order.getfieldval('OrderEntrySeqNum')
        except Exception, e:
            self.__exception("failed to set 'expect' : %s" % e )
            return
        self.Events[ordid].expectedReasonCode = reasonCode
        self.Events[ordid].expectedResponse = responseType
        if testCaseName:
            self.Events[ordid].testCaseName = testCaseName
        if serialNum:
            self.Events[ordid].serialNum = serialNum


    # Centralized logging, intended to be used
    # over the logging module functions
    # Writes to common logfile, pretty printing
    # when necessary
    def __log(self, level, msg, *args, **kargs):
        if isinstance(msg, scapy.packet.Packet):
            msg = self.__showPacket2(msg)
        elif type(msg) != str:
            strFile = StringIO.StringIO()
            pp = pprint.PrettyPrinter(stream=strFile)
            pp.pprint(msg)
            msg = strFile.getvalue()
            strFile.close()

        newArgs = []
        for i in range(len(args)):
            if isinstance(args[i], scapy.packet.Packet):
                newArgs.append(self.__showPacket2(args[i]))
            elif type(args[i]) not in [str, int, float]:
                strFile = StringIO.StringIO()
                pp = pprint.PrettyPrinter(stream=strFile)
                pp.pprint(args[i])
                newArgs.append(strFile.getvalue())
                strFile.close()
            else:
                newArgs.append(args[i])

        newArgs = tuple(newArgs)
        self.logger.log(level, msg, *newArgs,  **kargs)

    def debug(self, msg, *args, **kargs):
        self.__log(logging.DEBUG, msg, *args, **kargs)

    def info(self, msg, *args, **kargs):
        self.__log(logging.INFO, msg, *args, **kargs)

    def warning(self, msg, *args, **kargs):
        self.__log(logging.WARNING, msg, *args, **kargs)

    def error(self, msg, *args, **kargs):
        self.__log(logging.ERROR, msg, *args, **kargs)

    def critical(self, msg, *args, **kargs):
        self.__log(logging.CRITICAL, msg, *args, **kargs)

    def __exception(self, msg, *args):
        self.logger.exception(msg, *args)


    def saveSeqNum (self, csvFile='seqNum' ) :

        if os.path.exists(self.logPath + '/%s-%s.csv' %
                          (csvFile, self.state['clientID'] )):
            self.info ('Start saving seqNumber : path exists')
            i = 2
            while os.path.exists(self.logPath + '/%s-%s-%d.csv' %
                                 (csvFile, self.state['clientID'], i) ) :
                i += 1
            os.rename(self.logPath + '/%s-%s.csv' %
                      (csvFile, self.state['clientID'] ),
                      self.logPath + '/%s-%s-%d.csv' %
                      (csvFile, self.state['clientID'], i ))

        f = open(self.logPath + '/%s-%s.csv' %
                 (csvFile, self.state['clientID']), 'w' )
        self.info('Writing seqNumber to ' + self.logPath + '/%s-%s.csv' %
                 (csvFile, self.state['clientID'] ))

        # header
        f.write('VSNum,AcceptNoticeSeqNum,ExecNoticeSeqNum,OrderEntrySeqNum\n')
        for session in self.sessions.values():
            f.write ('%s,%d,%d,%d\n' %
                 (session['vsNum'], session['acceptNoticeSeqNum'], session['execNoticeSeqNum'], session['orderEntrySeqNum'] ) )
        self.info('Done ... ')

    def loadSeqNo (self, csvPath):
        CSVData = {}
        if not os.path.isfile(csvPath):
            return CSVData
        CSV = csv.reader(open(csvPath, 'r'), delimiter=',')
        header = 0
        headers = []
        for row in CSV :
            i = 0
            RowData = {}
            for field in row :
                if header == 0 :
                    headers.append(field)
                else :
                    if len(headers) > i :
                        key = headers[i]
                        RowData[key]=field
                    i += 1
            if header != 0 :
                vsNum = RowData['VSNum']
                self.sessions[vsNum]['orderEntrySeqNum'] = int(RowData['OrderEntrySeqNum'])
                self.sessions[vsNum]['acceptNoticeSeqNum'] = int(RowData['AcceptNoticeSeqNum'])
                self.sessions[vsNum]['execNoticeSeqNum'] = int(RowData['ExecNoticeSeqNum'])
            header += 1

    def getNotional(self) :
        """ showing the current Notional value kept in client """
        self.info(self.client.getNotional() )

    def updateSODData (self, filename, fileType ):
        """ updating security data, valid fileTypes are securityCSV, restrictionCSV, limitsCSV, tickSizeCSV"""
        try :
            if fileType == 'securityCSV' :
                self.info('loading Security data from %s' % filename )
                self.securities = getSodData( filename, 'Security', 'Symbol' )
            elif fileType == 'restrictionCSV' :
                self.info('loading Restriction data from %s' % filename)
                self.restrictions = getSodData( filename, 'Restriction', 'Client', 'Symbol' )
            elif fileType == 'limitsCSV' :
                self.info('loading Limits data from %s' % filename )
                self.limits = getSodData( filename, 'Limit', 'Client' )
            elif self.state['tickSizeCSV'] :
                self.info('loading tickSize data from %s' % filename)
                self.tickSize = getSodData( filename , 'TickSize', 'PriceFloor', 'Group' )
        except Exception, e:
            self.error("failed to update data : %s" % e )

    def checkExpectedReasonCodeNew(self, p):
        """ check expected reason code for neworder """

        if not type(p) == OrderCommon :
            self.warning('Cannot check reason code as type(%s) is not expected', type(p))
            return None

        if p.getfieldval('ExecCond') == '6' and p.getfieldval('Price') == ' 0           ' :
            return '8024'
        elif not p.getfieldval('PropBrokerageClass') == '0' :
            return '8026'
        elif not p.getfieldval('CashMarginCode') == '0' :
            return '8025'
        elif not p.getfieldval('StabArbCode') == '0' :
            return '8042'
        elif not p.getfieldval('OrdAttrClass') == '1' :
            return '8041'
        elif not p.getfieldval('SuppMemberClass') == '0' :
            return '8043'
        elif not p.getfieldval('ShortSellFlag') == '0' and p.getfieldval('Side') == '3' :
            return '8047'
        elif p.getfieldval('ShortSellFlag') == '5' and p.getfieldval('Price') == ' 0           ' : 
            return '8023'


    def checkRestriciton(self, clientID, symbol, side, shortSellFlag ):
        """ check restriction status for client/symbol """
        if (clientID, symbol) in self.restrictions :
            if side == '3' and shortSellFlag == '0' :
                if self.restrictions[(clientID, symbol)].buy == 'N':
                    return '8014'
            elif side == '1' and shortSellFlag == '0' :
                if self.restrictions[(clientID, symbol)].sell == 'N':
                    return '8015'
            elif side == '1' and shortSellFlag == '5' :
                if self.restrictions[(clientID, symbol)].shortSell == 'N':
                    return '8016'
            elif side == '1' and shortSellFlag == '7' :
                if self.restrictions[(clientID, symbol)].shortSellExempt == 'N':
                    return '8017'
        if ('*all', symbol) in self.restrictions :
            if side == '3' and shortSellFlag == '0' :
                if self.restrictions[('*all', symbol)].buy == 'N':
                    return '8014'
            elif side == '1' and shortSellFlag == '0' :
                if self.restrictions[('*all', symbol)].sell == 'N':
                    return '8015'
            elif side == '1' and shortSellFlag == '5' :
                if self.restrictions[('*all', symbol)].shortSell == 'N':
                    return '8016'
            elif side == '1' and shortSellFlag == '7' :
                if self.restrictions[('*all', symbol)].shortSellExempt == 'N':
                    return '8017'
        return None 


import signal

def getApp(cfg, logPath,callback):
    """Returns an instance of and AHD client application. Implements the singleton pattern, so returns the same instance if called multiple times. Sets up the SIGINT handler to call stop() on the app instance when the user presses <CTRL-C>."""
    assert isinstance(cfg,dict)
    assert callable(callback)

    if not App.__instance__:
        App.__instance__ = App(cfg, logPath,callback)

        def signal_handler(signal, frame):
            print 'SIGINT received!'
            App.__instance__.stop()
            print 'Exiting.'
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
    print 'Config Loaded ..'
    return App.__instance__

if __name__ == '__main__':
    signal.pause()
