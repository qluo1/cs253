# $Header: /home/cvs/eqtech/cep/src/kevlar/runtime/testCases/testCaseUtilities/KevlarApplicationState.py,v 1.3 2013/01/07 12:52:38 hironk Exp $
# vim: set sw=4 ts=4 sts=4 et:

class KevlarApplicationState:
    "This class tracks some of the expected state of a Kevlar application"

    def __init__(self, stripeName):
        "This method initializes the Kevlar application's state"
        self.__stripeName = stripeName
        self.__nextMessageIdFromHermes = 1
        self.__nextMessageIdToHermes = 1
        self.__nextMessageIdFromClusterLock = 1
        self.__nextMessageIdToClusterLock = 1
        self.__nextMessageIdFromSideKick = 1
        self.__nextMessageIdToSideKick = 1
        self.__nextMessageIdToApplication = {}
        self.__nextMessageIdFromApplication = {}
        self.__nextMessageIdFromSampleClient = {}
        self.__nextMessageIdToSampleClient = {}
        self.__nextGenericUniqueId = 1
        self.__nextTestCaseId = 1
        self.__nextMessageName = 1
        self.__nextMessageIdToCyclops = {}

        ## Allow Tag variable names and MessageId variable names to be unique in the simulator,
        ## across cleanups of the application under test.  (The direction qualifiers in the MessageId
        ## variable names are with respect to the application under test, not the simulator.)
        self.__outboundMessageIdResetCount = 0
        self.__inboundMessageIdResetCount = 0
        self.__tagSequenceNumberResetCount = 0

        import os
        self.__tagPrefix = os.getenv('TAG_PREFIX')
        if self.__tagPrefix == None:
            self.__tagPrefix = ''

        if os.getenv('TAGS_HAVE_DATE_SUFFIX'):
            self.__tagsHaveDateSuffix = 1
        else:
            self.__tagsHaveDateSuffix = 0

        if os.getenv('TAGS_HAVE_OE_SUFFIX'):
            self.__tagsHaveOESuffix = 1
        else:
            self.__tagsHaveOESuffix = 0

        if os.getenv('USE_VARIABLE_TAGS'):
            self.__useVariableTags = 1
        else:
            self.__useVariableTags = 0

        if os.getenv('USE_LENIENT_MESSAGE_IDS'):
            self.__useLenientMessageIds = 1
        else:
            self.__useLenientMessageIds = 0

        if os.getenv('SHARED_SEQUENCE_NUMS_IN_TAGS'):
            self.__sharedSequenceNumsInTags = 1
        else:
            self.__sharedSequenceNumsInTags = 0

    def useLenientMessageIds(self):
        return self.__useLenientMessageIds

    def getOutboundMessageIdResetCount(self):
        return self.__outboundMessageIdResetCount

    def getInboundMessageIdResetCount(self):
        return self.__inboundMessageIdResetCount

    def nextMessageName(self):
        self.__nextMessageName += 1

        return self.__nextMessageName
            
    def tagsHaveDateSuffix(self):
        return self.__tagsHaveDateSuffix

    def sharedSequenceNumsInTags(self):
        return self.__sharedSequenceNumsInTags

    def tagPrefix(self):
        return self.__tagPrefix

    def tagDate(self):
        import time
        return time.strftime('%Y%m%d', time.localtime())

    def stripeName(self):
        "This method returns the stripeName"
        return self.__stripeName

    def useVariableTags(self):
        return self.__useVariableTags

    def getTagSequenceNumberResetCount(self):
        return self.__tagSequenceNumberResetCount

    def nextTestCaseId(self):
        "This method returns the nextTestCaseId and increments it"
        nextTestCaseId = self.__nextTestCaseId
        self.__nextTestCaseId += 1
        return nextTestCaseId

    def nextMessageIdFromHermes(self, serviceName):
        "This method returns the nextMessageIdFromHermes and increments it"
        nextMessageIdFromHermes = self.__nextMessageIdFromHermes
        self.__nextMessageIdFromHermes += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__inboundMessageIdResetCount) }
            return var

        return nextMessageIdFromHermes

    def nextMessageIdToHermes(self, serviceName):
        "This method returns the nextMessageIdToHermes and increments it"
        nextMessageIdToHermes = self.__nextMessageIdToHermes
        self.__nextMessageIdToHermes += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__outboundMessageIdResetCount) }
            return var

        return nextMessageIdToHermes
        
    def nextMessageIdFromClusterLock(self, serviceName):
        "This method returns the nextMessageIdFromClusterLock and increments it"
        nextMessageIdFromClusterLock = self.__nextMessageIdFromClusterLock
        self.__nextMessageIdFromClusterLock += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__inboundMessageIdResetCount) }
            return var

        return nextMessageIdFromClusterLock

    def nextMessageIdToClusterLock(self, serviceName):
        "This method returns the nextMessageIdToClusterLock and increments it"
        nextMessageIdToClusterLock = self.__nextMessageIdToClusterLock
        self.__nextMessageIdToClusterLock += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__outboundMessageIdResetCount) }
            return var

        return nextMessageIdToClusterLock

    def nextMessageIdFromSideKick(self, serviceName):
        "This method returns the nextMessageIdFromSideKick and increments it"
        nextMessageIdFromSideKick = self.__nextMessageIdFromSideKick
        self.__nextMessageIdFromSideKick += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__inboundMessageIdResetCount) }
            return var

        return nextMessageIdFromSideKick

    def nextMessageIdToSideKick(self, serviceName):
        "This method returns the nextMessageIdToSideKick and increments it"
        nextMessageIdToSideKick = self.__nextMessageIdToSideKick
        self.__nextMessageIdToSideKick += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__outboundMessageIdResetCount) }
            return var

        return nextMessageIdToSideKick

    def nextMessageIdFromApplication(self, serviceName):
        "This method returns the nextMessageIdFromApplication and increments it"
        if serviceName not in self.__nextMessageIdFromApplication:
            self.__nextMessageIdFromApplication[serviceName] = 1
        nextMessageId = self.__nextMessageIdFromApplication[serviceName]
        self.__nextMessageIdFromApplication[serviceName] += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__inboundMessageIdResetCount) }
            return var

        return nextMessageId

    def nextMessageIdToApplication(self, serviceName):
        "This method returns the nextMessageIdToApplication and increments it"
        if serviceName not in self.__nextMessageIdToApplication:
            self.__nextMessageIdToApplication[serviceName] = 1
        nextMessageId = self.__nextMessageIdToApplication[serviceName]
        self.__nextMessageIdToApplication[serviceName] += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__outboundMessageIdResetCount) }
            return var

        return nextMessageId

    def nextGenericUniqueId(self, serviceName):
        "This method returns a generic unique id, guaranteed to be unique " + \
            "with respect to all other ids generated by this function for " + \
            "the serviceName provided within one simulator run"
        nextGenericUniqueId = self.__nextGenericUniqueId
        self.__nextGenericUniqueId += 1

        return nextGenericUniqueId

    def nextMessageIdToCyclops(self, serviceName):
        "This method returns the nextMessageIdToCyclops and increments it"
        if not serviceName in self.__nextMessageIdToCyclops:
            self.__nextMessageIdToCyclops[serviceName] = 1

        nextMessageIdToCyclops = self.__nextMessageIdToCyclops[serviceName]
        self.__nextMessageIdToCyclops[serviceName] += 1

        if self.__useLenientMessageIds:
            var = { 'nextMessageId': serviceName + '_' + str(self.__outboundMessageIdResetCount) }
            return var

        return nextMessageIdToCyclops

    def nextMessageIdToSampleClient(self, serviceName):
        "This method increments the MessageId counter of messages received from the appliction"
        if not serviceName in self.__nextMessageIdToSampleClient:
            self.__nextMessageIdToSampleClient[serviceName] = 1

        nextMessageIdToSample = self.__nextMessageIdToSampleClient[serviceName]
        self.__nextMessageIdToSampleClient[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.__outboundMessageIdResetCount) }
            return var

        return nextMessageIdToSample

    def nextMessageIdFromSampleClient(self, serviceName):
        "This method returns the __nextMessageIdFromSampleClient to send to the application, and increments that counter"
        if not serviceName in self.__nextMessageIdFromSampleClient:
            self.__nextMessageIdFromSampleClient[serviceName] = 1

        nextMessageIdFromSample = self.__nextMessageIdFromSampleClient[serviceName]
        self.__nextMessageIdFromSampleClient[serviceName] += 1

        if self.useLenientMessageIds():
            var = { 'nextMessageId': serviceName + '_' + str(self.__inboundMessageIdResetCount) }
            return var

        return nextMessageIdFromSample

    def previousMessageIdFromSampleClient(self, serviceName, messageName=None):
        "This method returns the MessageId that was most recently sent to the application"
        if not serviceName in self.__nextMessageIdFromSampleClient:
            self.__nextMessageIdFromSampleClient[serviceName] = 1

        previousMessageIdFromSample = self.__nextMessageIdFromSampleClient[serviceName] - 1

        if self.useLenientMessageIds():
            if messageName is None:
                var = { 'nextMessageId': serviceName + '_' + str(self.__inboundMessageIdResetCount) }
                return var
            else:
                var = { 'targetMessage': messageName }
                return var

        return previousMessageIdFromSample

    # Using NVI (non-virtual interface) pattern here to defere actual object creation to individual objects.
    def createTestCase(self, testCaseName, dependencies=None, expectedResultsInOrder=False):
        "This method allows poylmorphism to determine the type of TestCase object to create."
        return self.concrete_createTestCase(testCaseName, dependencies, expectedResultsInOrder)

    def concrete_createTestCase(self, testCaseName, dependencies=None, expectedResultsInOrder=False):
        "This method creates a test case for a Kevlar application"
        from KevlarTestCase import KevlarTestCase 
        return KevlarTestCase(self, testCaseName, dependencies, expectedResultsInOrder)

    # The following functions should only be needed in some special cases where the 
    # omsimulator is going to remain up over multiple cycles of the process under test.
    def resetAllCounters(self):
        "This method resets all counters in the omsimulator to their initial values"
        self.resetAllToMessageIdCounters()
        self.resetAllFromMessageIdCounters()
        self.resetIdCounters()


    def resetAllToMessageIdCounters(self):
        "This method resets all To message Id counters in the omsimulator to their initial values and updates the messageId variable name suffix"
        self.__nextMessageIdToHermes = 1
        self.__nextMessageIdToClusterLock = 1
        self.__nextMessageIdToSideKick = 1

        self.__outboundMessageIdResetCount += 1

    def resetAllFromMessageIdCounters(self):
        "This method resets all From message Id counters in the omsimulator to their initial values and updates the messageId variable name suffix"
        self.__nextMessageIdFromHermes = 1
        self.__nextMessageIdFromClusterLock = 1
        self.__nextMessageIdFromSideKick = 1

        self.__inboundMessageIdResetCount += 1

    def resetIdCounters(self):
        "updates the tag variable name suffix"
        self.__tagSequenceNumberResetCount += 1
