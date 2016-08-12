# $Header: /home/cvs/eqtech/cep/src/testCaseOm2Utilities/OmEngineState.py,v 1.4 2014/11/07 13:56:33 hironk Exp $
# vim: set sw=4 ts=4 sts=4 et:

import KevlarApplicationState

class OmEngineState(KevlarApplicationState.KevlarApplicationState):
    "This class tracks some of the expected state of the om engine"

    def __init__(self, stripeName):
        "This method initializes the om engine's state"
        KevlarApplicationState.KevlarApplicationState.__init__(self, stripeName)

        self.__nextMessageIdToViking = {}
        self.__nextMessageIdFromViking = {}
        self.__nextMessageIdToDropCopy = {}
        self.__nextMessageIdToApollo = {}
        self.__nextMessageIdFromApollo = {}
        self.__nextMessageIdFromIoiProvider = 1
        self.__nextMessageIdToUpstreamOms = 1
        self.__nextMessageIdFromUpstreamOms = 1
        self.__nextMessageIdToDownstreamOms = 1
        self.__nextMessageIdFromDownstreamOms = {}
        self.__nextMessageIdFromDatastreamServer = 1
        self.__nextMessageIdFromInventoryManager = {}
        self.__nextMessageIdToInventoryManager = 1
        self.__nextOrderId = 1
        self.__nextExecutionId = 1
        self.__nextTestCaseOverrideId = 1
        self.__marketDataIsOverridden = False
        self.__nextOrderIdFromUpstreamOms = {}
        self.__nextBasketId = 1
        self.__nextIndicationId = 1
        self.__testDatastreamServer = False
        self.__nextMessageIdToSsr = 1
        self.__nextMessageIdFromSsr = 1
        self.__nextMessageIdToScoop = 1
        self.__nextMessageIdFromScoop = 1
        self.__nextMessageIdToMasterAggregator = 1
        self.__nextMessageIdFromMasterAggregator = 1
        self.__nextMessageIdToAdvisor = {}
        self.__nextMessageIdFromAdvisor = {}
        self.__nextMessageIdToDSS = {}
        self.__nextMessageIdToOmEngine = {}
        self.__waitForEveryTransactionAck = False

        import os

        dssTest = os.getenv('TEST_DSS')
        self.__testDatastreamServer = dssTest != None and dssTest.lower() == 'true'

        waitForEveryTransactionAck = os.getenv('WAIT_FOR_EVERY_TRANSACTION_ACK')
        self.__waitForEveryTransactionAck = waitForEveryTransactionAck != None and waitForEveryTransactionAck.lower() == 'true'
         
    def isMarketDataOverridden(self):
        return self.__marketDataIsOverridden

    def marketDataIsOverridden(self, value):
        self.__marketDataIsOverridden = value

    def nextBasketIdSeqNum(self):
        nextBasketId = str(self.__nextBasketId)
        self.__nextBasketId += 1
        return nextBasketId

    def nextIndicationIdSeqNum(self):
        nextIndicationId = str(self.__nextIndicationId)
        self.__nextIndicationId += 1
        return nextIndicationId

    def nextIndicationId(self):
        "This method returns the nextIndicationId and increments it"

        nextIndicationId = self.tagPrefix() + self.nextBasketIdSeqNum()

        if self.tagsHaveDateSuffix():
            nextIndicationId += self.tagDate()

        if self.sharedSequenceNumsInTags() == 0:
            nextIndicationId += "I"
        
        return nextIndicationId
        
    def nextBasketId(self):
        "This method returns the nextBasketId and increments it"

        nextBasketId = self.tagPrefix() + self.nextBasketIdSeqNum()

        if self.tagsHaveDateSuffix():
            nextBasketId += self.tagDate()

        if self.sharedSequenceNumsInTags() == 0:
            nextBasketId += "B"
        
        return nextBasketId

    def nextOrderIdSeqNum(self):
        nextOrderId = str(self.__nextOrderId)
        self.__nextOrderId += 1
        return nextOrderId
      
    def nextOrderId(self):
        "This method returns the nextOrderId and increments it"

        nextOrderId = self.tagPrefix() + self.nextOrderIdSeqNum()

        if self.tagsHaveDateSuffix():
            nextOrderId += self.tagDate()

        if self.sharedSequenceNumsInTags() == 0:
        	nextOrderId = nextOrderId + "O"
        
        return nextOrderId

    def nextExecutionIdSeqNum(self):
        nextExecutionId = str(self.__nextExecutionId)
        self.__nextExecutionId += 1
        return nextExecutionId
      
    def nextExecutionId(self):
        "This method returns the nextExecutionId and increments it"

        if self.sharedSequenceNumsInTags() == 0:
            nextExecutionId = self.tagPrefix() + self.nextExecutionIdSeqNum()
        else:
            nextExecutionId = self.tagPrefix() + self.nextOrderIdSeqNum()

        if self.tagsHaveDateSuffix():
            nextExecutionId += self.tagDate()

        if self.sharedSequenceNumsInTags() == 0:
        	nextExecutionId = nextExecutionId + "E"
        
        return nextExecutionId

    def nextTestCaseOverrideIdSeqNum(self):
        nextTestCaseOverrideId = str(self.__nextTestCaseOverrideId)
        self.__nextTestCaseOverrideId += 1
        return nextTestCaseOverrideId
      
    def nextTestCaseOverrideId(self):
        "This method returns the nextTestCaseOverrideId and increments it"

        if self.sharedSequenceNumsInTags() == 0:
            nextTestCaseOverrideId = self.tagPrefix() + self.nextTestCaseOverrideIdSeqNum()
        else:
            nextTestCaseOverrideId = self.tagPrefix() + self.nextOrderIdSeqNum()

        if self.tagsHaveDateSuffix():
            nextTestCaseOverrideId += self.tagDate()

        if self.sharedSequenceNumsInTags() == 0:
        	nextTestCaseOverrideId = nextTestCaseOverrideId + "T"
        
        return nextTestCaseOverrideId

    def nextMessageIdToDropCopy(self, serviceName):
        "This method returns the nextMessageIdToDropCopy and increments it"
        if not serviceName in self.__nextMessageIdToDropCopy:
            self.__nextMessageIdToDropCopy[serviceName] = 1

        nextMessageIdToDropCopy = self.__nextMessageIdToDropCopy[serviceName]
        self.__nextMessageIdToDropCopy[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToDropCopy

    def nextMessageIdToApollo(self, serviceName):
        "This method returns the nextMessageIdToApollo and increments it"
        if not serviceName in self.__nextMessageIdToApollo:
            self.__nextMessageIdToApollo[serviceName] = 1

        nextMessageIdToApollo = self.__nextMessageIdToApollo[serviceName]
        self.__nextMessageIdToApollo[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToApollo

    def previousMessageIdToApollo(self, serviceName):
        if not serviceName in self.__nextMessageIdToApollo:
            self.__nextMessageIdToApollo[serviceName] = 1

        previousMessageIdToApollo = self.__nextMessageIdToApollo[serviceName] - 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return previousMessageIdToApollo

    def nextMessageIdFromApollo(self, serviceName):
        "This method returns the nextMessageIdFromApollo and increments it"
        if not serviceName in self.__nextMessageIdFromApollo:
            self.__nextMessageIdFromApollo[serviceName] = 1

        nextMessageIdFromApollo = self.__nextMessageIdFromApollo[serviceName]
        self.__nextMessageIdFromApollo[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromApollo
 
    def previousMessageIdFromApollo(self, serviceName, messageName=None):
        if not serviceName in self.__nextMessageIdFromApollo:
            self.__nextMessageIdFromApollo[serviceName] = 1

        previousMessageFromApollo = self.__nextMessageIdFromApollo[serviceName] - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return previousMessageIdFromApollo
       

    def previousMessageIdToViking(self, serviceName):
        if not serviceName in self.__nextMessageIdToViking:
            self.__nextMessageIdToViking[serviceName] = 1

        previousMessageIdToViking = self.__nextMessageIdToViking[serviceName] - 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return previousMessageIdToViking

    def nextMessageIdToViking(self, serviceName):
        "This method returns the nextMessageIdToViking and increments it"
        if not serviceName in self.__nextMessageIdToViking:
            self.__nextMessageIdToViking[serviceName] = 1

        nextMessageIdToViking = self.__nextMessageIdToViking[serviceName]
        self.__nextMessageIdToViking[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToViking

    def currentMessageIdToViking(self, serviceName):
        "This method returns the nextMessageIdToViking without incrementing it"
        if not serviceName in self.__nextMessageIdToViking:
            raise OmTestCaseException('no messageId has been genenerated for viking datastream serviceName [' + serviceName + ']')

        return self.__nextMessageIdToViking[serviceName]

    def nextMessageIdFromViking(self, serviceName):
        "This method returns the nextMessageIdFromViking and increments it"
        if not serviceName in self.__nextMessageIdFromViking:
            self.__nextMessageIdFromViking[serviceName] = 1

        nextMessageIdFromViking = self.__nextMessageIdFromViking[serviceName]
        self.__nextMessageIdFromViking[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromViking
 
    def previousMessageIdFromViking(self, serviceName, messageName=None):
        if not serviceName in self.__nextMessageIdFromViking:
            self.__nextMessageIdFromViking[serviceName] = 0
        prevMessageIdFromViking = self.__nextMessageIdFromViking[serviceName] - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return prevMessageIdFromViking

    def previousMessageIdFromInventoryManager(self, serviceName, messageName=None):

        if not serviceName in self.__nextMessageIdFromInventoryManager:
            self.__nextMessageIdFromInventoryManager[serviceName] = 0
        prevMessageIdFromViking = self.__nextMessageIdFromInventoryManager[serviceName] - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return prevMessageIdFromInventoryManager

    def nextMessageIdToAdvisor(self, serviceName):
        "This method returns the nextMessageIdToAdvisor and increments it"
        if not serviceName in self.__nextMessageIdToAdvisor:
            self.__nextMessageIdToAdvisor[serviceName] = 1

        nextMessageIdToAdvisor = self.__nextMessageIdToAdvisor[serviceName]
        self.__nextMessageIdToAdvisor[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToAdvisor

    def previousMessageIdToAdvisor(self, serviceName):
        if not serviceName in self.__nextMessageIdToAdvisor:
            self.__nextMessageIdToAdvisor[serviceName] = 1

        previousMessageIdToAdvisor = self.__nextMessageIdToAdvisor[serviceName] - 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return previousMessageIdToAdvisor

    def nextMessageIdFromAdvisor(self, serviceName):
        "This method returns the nextMessageIdFromAdvisor and increments it"
        if not serviceName in self.__nextMessageIdFromAdvisor:
            self.__nextMessageIdFromAdvisor[serviceName] = 1

        nextMessageIdFromAdvisor = self.__nextMessageIdFromAdvisor[serviceName]
        self.__nextMessageIdFromAdvisor[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromAdvisor

    def previousMessageIdFromAdvisor(self, serviceName, messageName=None):
        if not serviceName in self.__nextMessageIdFromAdvisor:
            self.__nextMessageIdFromAdvisor[serviceName] = 1

        previousMessageFromAdvisor = self.__nextMessageIdFromAdvisor[serviceName] - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return previousMessageIdFromAdvisor

        
    def nextMessageIdFromIoiProvider(self, serviceName):
        "This method returns the nextMessageIdFromIoiProvider and increments it"
        nextMessageIdFromIoiProvider = self.__nextMessageIdFromIoiProvider
        self.__nextMessageIdFromIoiProvider += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromIoiProvider
       
    def nextMessageIdToUpstreamOms(self, serviceName):
        "This method returns the nextMessageIdToUpstreamOms and increments it"
        nextMessageIdToUpstreamOms = self.__nextMessageIdToUpstreamOms
        self.__nextMessageIdToUpstreamOms += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToUpstreamOms

    def nextMessageIdFromUpstreamOms(self, serviceName):
        "This method returns the nextMessageIdFromUpstreamOms and increments it"
        nextMessageIdFromUpstreamOms = self.__nextMessageIdFromUpstreamOms
        self.__nextMessageIdFromUpstreamOms += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromUpstreamOms

    def nextMessageIdToDownstreamOms(self, serviceName):
        "This method returns the nextMessageIdToDownstreamOms and increments it"
        nextMessageIdToDownstreamOms = self.__nextMessageIdToDownstreamOms
        self.__nextMessageIdToDownstreamOms += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToDownstreamOms

    def previousMessageIdFromDownstreamOms(self, serviceName, messageName=None): 
        if not serviceName in self.__nextMessageIdFromDownstreamOms:
            self.__nextMessageIdFromDownstreamOms[serviceName] = 0
        prevMessageIdFromDownstreamOms = self.__nextMessageIdFromDownstreamOms[serviceName] - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return prevMessageIdFromDownstreamOms

    def nextMessageIdFromDownstreamOms(self, serviceName):
        "This method returns the nextMessageIdFromDownstreamOms and increments it"
        if not serviceName in self.__nextMessageIdFromDownstreamOms:
            self.__nextMessageIdFromDownstreamOms[serviceName] = 1
        nextMessageIdFromDownstreamOms = self.__nextMessageIdFromDownstreamOms[serviceName]
        self.__nextMessageIdFromDownstreamOms[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromDownstreamOms

    def nextMessageIdToInventoryManager(self, serviceName):
        "This method returns the nextMessageIdToInventoryManager and increments it"
        nextMessageIdToInventoryManager = self.__nextMessageIdToInventoryManager
        self.__nextMessageIdToInventoryManager += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToInventoryManager

    def nextMessageIdFromInventoryManager(self, serviceName):
        "This method returns the nextMessageIdFromInventoryManager and increments it"
        if not serviceName in self.__nextMessageIdFromInventoryManager:
            self.__nextMessageIdFromInventoryManager[serviceName] = 1

        nextMessageIdFromInventoryManager = self.__nextMessageIdFromInventoryManager[serviceName]
        self.__nextMessageIdFromInventoryManager[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromInventoryManager

    def nextOrderIdFromUpstreamOms(self, serviceName):
        "This method returns the nextOrderIdFromUpstreamOms and increments it"
        if(serviceName not in self.__nextOrderIdFromUpstreamOms):
            self.__nextOrderIdFromUpstreamOms[serviceName] = 1;
        else:
            self.__nextOrderIdFromUpstreamOms[serviceName] += 1

        nextOrderId = serviceName + str(self.__nextOrderIdFromUpstreamOms[serviceName])

        if self.tagsHaveDateSuffix():
            nextOrderId += self.tagDate()

        return nextOrderId

    def nextMessageIdFromDatastreamServer(self, serviceName):
        "This method returns the nextMessageIdFromDatastreamServer and increments it"
        nextMessageIdFromDatastreamServer = self.__nextMessageIdFromDatastreamServer
        self.__nextMessageIdFromDatastreamServer += 1
        if self.useLenientMessageIds():
	        var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
	        return var

        return nextMessageIdFromDatastreamServer


    def nextMessageIdFromSsr(self, serviceName):
        "This method returns the nextMessageIdFromSsr and increments it"
        nextMessageIdFromSsr = self.__nextMessageIdFromSsr
        self.__nextMessageIdFromSsr += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromSsr

    def nextMessageIdToSsr(self, serviceName):
        "This method returns the nextMessageIdToSsr and increments it"
        nextMessageIdToSsr = self.__nextMessageIdToSsr
        self.__nextMessageIdToSsr += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToSsr

    def previousMessageIdFromSsr(self, serviceName, messageName=None):
        previousMessageIdFromSsr = self.__nextMessageIdFromSsr - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return previousMessageIdFromSsr

    def nextMessageIdFromScoop(self, serviceName):
        "This method returns the nextMessageIdFromScoop and increments it"
        nextMessageIdFromScoop = self.__nextMessageIdFromScoop
        self.__nextMessageIdFromScoop += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromScoop

    def nextMessageIdToScoop(self, serviceName):
        "This method returns the nextMessageIdToScoop and increments it"
        nextMessageIdToScoop = self.__nextMessageIdToScoop
        self.__nextMessageIdToScoop += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToScoop

    def previousMessageIdFromMasterAggregator(self, serviceName, messageName=None):
        previousMessageIdFromMasterAggregator = self.__nextMessageIdFromMasterAggregator - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return previousMessageIdFromMasterAggregator

    def nextMessageIdFromMasterAggregator(self, serviceName):
        "This method returns the nextMessageIdFromMasterAggregator and increments it"
        nextMessageIdFromMasterAggregator = self.__nextMessageIdFromMasterAggregator
        self.__nextMessageIdFromMasterAggregator += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getInboundMessageIdResetCount()) }
            return var

        return nextMessageIdFromMasterAggregator

    def nextMessageIdToMasterAggregator(self, serviceName):
        "This method returns the nextMessageIdToMasterAggregator and increments it"
        nextMessageIdToMasterAggregator = self.__nextMessageIdToMasterAggregator
        self.__nextMessageIdToMasterAggregator += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToMasterAggregator

    def nextMessageIdToDSS(self):
        "This method returns the nextMessageIdToDSS and increments it"
        serviceName = "replication"
        if not serviceName in self.__nextMessageIdToDSS:
            self.__nextMessageIdToDSS[serviceName] = 0

        nextMessageIdToDSS = self.__nextMessageIdToDSS[serviceName]
        self.__nextMessageIdToDSS[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToDSS

    def nextMessageIdToOmEngine(self):
        "This method returns the nextMessageIdToOmEngine and increments it"
        serviceName = "replication"
        if not serviceName in self.__nextMessageIdToOmEngine:
            self.__nextMessageIdToOmEngine[serviceName] = 0

        nextMessageIdToOmEngine = self.__nextMessageIdToOmEngine[serviceName]
        self.__nextMessageIdToOmEngine[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.getOutboundMessageIdResetCount()) }
            return var

        return nextMessageIdToOmEngine
 
    def testDatastreamServer(self):
        return self.__testDatastreamServer

    def waitForEveryTransactionAck(self):
        return self.__waitForEveryTransactionAck

    def createOrder(self):
        "This method creates an order"
        from OmOrder import OmOrder 
        return OmOrder(self)

    def createExecution(self):
        "This method creates an execution"
        from OmExecution import OmExecution 
        return OmExecution(self)

    def createIndication(self):
        "This method creates an indication"
        from OmIndication import OmIndication 
        return OmIndication(self)

    def createTestCaseOverride(self):
        "This method creates a testCaseOverride"
        from OmTestCaseOverride import OmTestCaseOverride 
        return OmTestCaseOverride(self)
    
    # Note: Do not define a createTestCase() method, only the concrete create method (part of NVI pattern).
    def concrete_createTestCase(self, testCaseName, dependencies=None, expectedResultsInOrder=False):
        "This method creates a test case for an omengine"
        from OmTestCase import OmTestCase 
        return OmTestCase(self, testCaseName, dependencies, expectedResultsInOrder)


    def resetAllToMessageIdCounters(self):
        "This method resets all To message Id counters in the omsimulator to their initial values"
        KevlarApplicationState.KevlarApplicationState.resetAllToMessageIdCounters(self)
        self.__nextMessageIdToViking = {} 
        self.__nextMessageIdToApollo = {}
        self.__nextMessageIdToUpstreamOms = 1
        self.__nextMessageIdToDownstreamOms = 1
        self.__nextMessageIdToDSS = {}


    def resetAllFromMessageIdCounters(self):
        "This method resets all From message Id counters in the omsimulator to their initial values"
        KevlarApplicationState.KevlarApplicationState.resetAllFromMessageIdCounters(self)
        self.__nextMessageIdFromViking = {}
        self.__nextMessageIdFromApollo = {}
        self.__nextMessageIdFromInventoryManager = {}
        self.__nextMessageIdFromAdvisor = {}
        self.__nextMessageIdFromIoiProvider = 1
        self.__nextMessageIdFromUpstreamOms = 1
        self.__nextMessageIdFromDownstreamOms = {}
        self.__nextMessageIdFromDatastreamServer = 1
        self.__nextOrderIdFromUpstreamOms = {}


    def resetIdCounters(self):
        "This method resets all Order, Execution and Basket Id counters in the omsimulator to their initial values"
        KevlarApplicationState.KevlarApplicationState.resetIdCounters(self)
        self.__nextOrderId = 1
        self.__nextExecutionId = 1
        self.__nextBasketId = 1
        self.__nextTestCaseOverrideId = 1

class OmEngineStateAbnerMixin:
    """
    In order to generate tests in Abner format, derive the OmEngineState with this
    e.g.:
    class OmAbnerEngineState(OmEngineState, OmEngineStateAbnerMixin): pass
    """
    def stripeName(self):
        return '[Abner::OmEngine]'

    def tagPrefix(self):
        return '[Abner::OmEngine]'

    def tagDate(self):
        return '[Abner::date::GMT]'

    def onNewScenario(self):
        """
        clear the objectIds at the beginning of each new scenario
        """
        self.__nextBasketId = 1
        self.__nextOrderId = 1
        self.__nextExecutionId = 1
        self.__nextTestCaseOverrideId = 1
        self.__genericUniqueId = {}

    def nextGenericUniqueId(self, serviceName):
        """
        This is mostly used for posDupId generation for messages for a given serviceName.
        We ensure that we ave a different incrementing number for each serviceName.
        The serviceName does not need to be concatenated because this is always
        used in conjunction with the serviceName on the caller side
        """
        uniqueId = self.__genericUniqueId.get(serviceName)
        if uniqueId is None: uniqueId = 0

        uniqueId += 1
        self.__genericUniqueId[serviceName] = uniqueId
        return "[Abner::objectId::%d]" % uniqueId

    def nextBasketIdSeqNum(self):
        nextBasketId = "[Abner::objectId::%d]" % self.__nextBasketId
        self.__nextBasketId += 1
        return nextBasketId
      
    def nextOrderIdSeqNum(self):
        nextOrderId = "[Abner::objectId::%d]" % self.__nextOrderId
        self.__nextOrderId += 1
        return nextOrderId
      
    def nextExecutionIdSeqNum(self):
        nextExecutionId = "[Abner::objectId::%d]" % self.__nextExecutionId
        self.__nextExecutionId += 1
        return nextExecutionId
      
    def nextTestCaseOverrideIdSeqNum(self):
        nextTestCaseOverrideId = "[Abner::objectId::%d]" % self.__nextTestCaseOverrideId
        self.__nextTestCaseOverrideId += 1
        return nextTestCaseOverrideId
