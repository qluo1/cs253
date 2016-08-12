from KevlarApplicationState import KevlarApplicationState
import os
import getpass
import traceback
import time
import sys

## For time overrides
globalMicrosecondCount=0

# Make consistent time information available to all test cases.
currentTimeT = time.time()
currentLocalTimeStruct = time.localtime(currentTimeT)
currentGMTTimeStruct = time.gmtime(currentTimeT)
currentLocalDateStr = time.strftime("%Y%m%d", currentLocalTimeStruct)
currentGMTDateStr = time.strftime("%Y%m%d", currentGMTTimeStruct)

def embeddedIf(expr, trueRet, falseRet):
    if (expr):
        return trueRet
    return falseRet

class KevlarTestCaseException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# static functions
def printConfiguration(toPrint):
    """
    pretty print the string with indentation
    """
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(toPrint)

def unionOf(*dicts):
    """
    Take a union of fields of the specified dictionaries.
    If fields overlap between dictionaries, an error is raised.
    \param dicts a list of dictionaries
    \return the union dictionary
    """
    import copy
    result = {}
    for dict in dicts:
        if dict is not None:
            for k in dict.keys():
                if k in result:
                    raise KevlarTestCaseException, 'duplicate key [' + k + '] in test case'
            result.update(copy.deepcopy(dict))
    return result

def merge(*dicts):
    """
    Take a union of fields of the specified dictionaries.
    If fields overlap between dictionaries, the latter dictionary will override.
    \param dicts a list of dictionaries
    \return the union dictionary
    """
    import copy
    result = {}
    for dict in dicts:
        if (dict != []):
           result.update(copy.deepcopy(dict))
    return result

def localGmtOffset():
    """Return the offset in hours of the local time zone from UTC,
    possibly including fractions. Note that Python's strftime doesn't
    currently work when passed a known time tuple - it only works with
    the implicit "current time" usage, which makes writing a doctest
    test for this fairly difficult"""

    import time
    rfc822offset = int(time.strftime("%z"))
    sign = 1
    if rfc822offset < 0:
        sign = -1
        rfc822offset = -rfc822offset
    wholeHours = int(rfc822offset / 100)
    minutes = rfc822offset - (wholeHours * 100)

    return sign * (wholeHours + minutes / 60.0)

class KevlarTestException(Exception): pass

class KevlarTestCase:
    """
    This class represents a test case (an action and its expected results).
    Only the KevlarEngineState should construct objects of this type
    """

    def __init__(self, applicationState, testCaseName, dependencies=None, expectedResultsInOrder=False):
        "this method initializes an order, the caller may optionally specify a dictionary of order attributes to override the default attributes"
        self.__applicationState = applicationState
        self.__id = applicationState.nextTestCaseId()
        self.__baseTestCaseName = testCaseName
        self.__messageNum = 0;
        self.__data = {
            'testCaseName': testCaseName + ' (' + str(self.id()) + ')',
            'expectedResultsInOrder' : str(expectedResultsInOrder),
            'actions': [],
            'expectedResults': [],
        }
        if dependencies is not None:
            self.__data['dependencyTestCaseNames'] = dependencies

    def state(self):
        return self.__applicationState

    def addDependency(self, dependency):
        if 'dependencyTestCaseNames' not in self.__data:
            self.__data['dependencyTestCaseNames'] = []
        self.__data['dependencyTestCaseNames'].append(dependency)

    def id(self):
        "returns the test case's id"
        return self.__id

    def testCaseData(self):
        "returns the test case's data"
        if (self.__data['actions'] == []):
            self.__data['actions'] = 'None'
        if (self.__data['expectedResults'] == []):
            self.__data['expectedResults'] = 'None'
        return self.__data

    def testCaseName(self):
        "returns the test case's name"
        return self.__data['testCaseName']

    def baseTestCaseName(self):
        "returns the test case's name"
        return self.__baseTestCaseName

    def actions(self):
        "returns actions for this test case"
        return self.__data['actions']

    def addAction(self, action):
        """
        raw way to add an action to the test case
        """
        self.__data['actions'].append(action)

    def addActions(self, actions):
        """
        raw way to add actions to the test case
        """
        self.__data['actions'].extend(actions)

    def addExpectedResult(self, result):
        """
        raw way to add an expected result to the test case
        """
        self.__data['expectedResults'].append(result)

    def addExpectedResults(self, list):
        "returns expected results for this test case"
        self.__data['expectedResults'].extend(list)

    def expectedResults(self):
        "returns expected results for this test case"
        return self.__data['expectedResults']

    def clearExpectedResults(self):
        "clears out any expectedResults for this test case"
        self.__data['expectedResults'] = []

    def clearActions(self):
        "clears out any actions for this test case"
        self.__data['actions'] = []

    def reverseExpectedResults(self):
        "returns expected results for this test case"
        self.__data['expectedResults'].reverse()

    def messageNum(self):
        "returns the message number for this test case"
        temp = self.__messageNum
        self.__messageNum += 1
        return str(temp)

    def setTestFailureTimeout(self, timeout):
        "set timeout value for this test case"
        self.__data['test-failure-interval'] = timeout

    def getTestFailureTimeout(self):
        """get failure timeout value for this test case.
         if the timeout is not yet set, this function will return 0.
         Please note that omsimulator, if the 'test-failure-interval' is not set for a test case, will use its own default value
         configured in the simulator configuration"""
        if 'test-failure-interval' in self.__data and self.__data['test-failure-interval'] is not None:
            return self.__data['test-failure-interval']
        return 0

    def getTraceback(self):
        trace = []
        stack = traceback.extract_stack()[2:-1]
        for i in range(len(stack)):
            if (len(stack[i]) == 4):
                #filename
                #get the filename, truncate anything before the last "/"
                fileName = stack[i][0]
                fileName = fileName[fileName.rfind("/")+1: len(fileName)]
                trace.append("File \"" + fileName + "\", ")

                #line number
                lineNumber = stack[i][1]
                trace[-1] += "line " + str(lineNumber) + ", ";

                #2 = module, not used

                #code at line
                codeLine = stack[i][3]

                # This handles if an import includes something which is not directly in the config directory
                # or if a method is called using eval()
                if codeLine is not None:
                    #remove the parameters given to the function
                    index = codeLine.find("(")
                    if index > 0:
                        codeLine = codeLine[0: index] + "()";
                    trace[-1] += "at " + codeLine + "\n";
                else:
                    trace[-1] += "at <unknown>\n";
        return trace


    def addCachedMessageToCyclops(self, tableName, dict, source, path, checkMessageListOrder = "false", instanceRole = "Primary"):
        "this function creates waits for an initialization message from the application to the Cyclops collector"

        serviceName = self.__applicationState.stripeName() + '-' + instanceRole + '->CCOLLECTOR'

        self.__data['expectedResults'].append( {
            'serviceType': 'client-cyclops-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'cachedMessage': {
                'source': source,
                'path' : path,
                'messageId': self.__applicationState.nextMessageIdToCyclops(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })
        if self.getTestFailureTimeout() < 30:
            self.setTestFailureTimeout(30) #a ivcom cyclops messages might take few additional seconds.

    def addMessageToCyclops(self, tableName, dict, source, path, purgeCacheValue = False, checkMessageListOrder = "false", instanceRole = "Primary"):
        "this function creates waits for a message from the application to the Cyclops collector"

        serviceName = self.__applicationState.stripeName() + '-' + instanceRole + '->CCOLLECTOR'

        msg = {
            'source': source,
            'path' : path,
            'messageId': self.__applicationState.nextMessageIdToCyclops(serviceName),
            'table': tableName,
            'fields': dict,
            'checkOrder': checkMessageListOrder,
        }

        if purgeCacheValue:
            msg['purgeCacheValue'] = 'True'

        self.__data['expectedResults'].append( {
            'serviceType': 'client-cyclops-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': msg,
            'trace' : self.getTraceback(),
        })
        if self.getTestFailureTimeout() < 30:
            self.setTestFailureTimeout(30) #a ivcom cyclops messages might take few additional seconds.
        print self.__data['expectedResults']

    def addMessageToDssCyclops(self, tableName, dict, source, path, purgeCacheValue = False, checkMessageListOrder = "false", instanceRole = "Primary"):
        "this function creates waits for a message from the application to the Cyclops collector"

        serviceName = self.__applicationState.stripeName() + '-DSS-' + instanceRole + '->CCOLLECTOR'

        msg = {
            'source': source,
            'path' : path,
            'messageId': self.__applicationState.nextMessageIdToCyclops(serviceName),
            'table': tableName,
            'fields': dict,
            'checkOrder': checkMessageListOrder,
        }

        if purgeCacheValue:
            msg['purgeCacheValue'] = 'True'

        self.__data['expectedResults'].append( {
            'serviceType': 'client-cyclops-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': msg,
            'trace' : self.getTraceback(),
        })
        if self.getTestFailureTimeout() < 30:
            self.setTestFailureTimeout(30) #a ivcom cyclops messages might take few additional seconds.
        print self.__data['expectedResults']

    def purgeDssCyclopsCache(self, cyclopsSource, metricPath, instanceRole = 'Primary'):
        "this function creates waits for a message from the application to the Cyclops collector"

        serviceName = self.__applicationState.stripeName() + '-DSS-' + instanceRole + '->CCOLLECTOR'
        self.__data['actions'].append( {
            'serviceType': 'client-cyclops-manager',
            'serviceName': serviceName,
            'actionName' : 'purgeMetricPath',
            'message': {
                'metricPath': metricPath,
                'source': cyclopsSource,
            },
        } )

    def purgeCyclopsCache(self, cyclopsSource, metricPath, instanceRole = 'Primary'):
        "this function creates waits for a message from the application to the Cyclops collector"

        serviceName = self.__applicationState.stripeName() + instanceRole + '->CCOLLECTOR'
        self.__data['actions'].append( {
            'serviceType': 'client-cyclops-manager',
            'serviceName': serviceName,
            'actionName' : 'purgeMetricPath',
            'message': {
                'metricPath': metricPath,
                'source': cyclopsSource,
            },
        } )

    def buildHermesCommandMessageFields(self, commandName, dicts):
        "this is just an internal helper function"
        result = {}

        commonAttributes = {
            'cmd': commandName,
	    'args': '',  # this must be set
            'handle': commandName,
            'guiId': '', # this must be set
            'cmdId': '', # this must be set
        }

        result = unionOf(commonAttributes, dicts)

        return result

    def addMessageFromHermesCollector(self, commandName, dict = {}, instanceRole = "Primary"):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'HermesCommand'

        serviceName = os.getenv("monitoredInstance") + '-' + instanceRole

        fromAttr = {
            'userId': getpass.getuser(),
            'requestManager': serviceName,
        }

        # 'message' is not defined in the request message, so if present we must remove it.
        kvps = unionOf(self.buildHermesCommandMessageFields(commandName, dict), fromAttr)
        if 'message' in kvps:
            del kvps['message']

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromHermes(serviceName),
                'table': tableName,
                'fields': kvps,
            },
        } )

    def addMessageToHermesCollector(self, commandName, dict = {}, instanceRole = "Primary", additionalDict = None):
        tableName = 'HermesCommandResult'

        serviceName = os.getenv("monitoredInstance") + '-' + instanceRole

        toAttr = {
            'requestManager': serviceName,
        }

        # Need 'status' and 'message' to be defined in dicts.  If not, we need to supply default 'Success'.
        # Need to prevent 'argumentVector' from appearing in response message.
        kvps = unionOf(self.buildHermesCommandMessageFields(commandName, dict), toAttr)
        if 'status' not in kvps:
            kvps['status'] = 'Success'
        if 'message' not in kvps:
            kvps['message'] = kvps['status']
        if 'argumentVector' in kvps:
            del kvps['argumentVector']

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToHermes(serviceName),
                'table': tableName,
                'fields': kvps,
            },
            'trace' : self.getTraceback(),
        })

        if additionalDict is not None:
            self.__data['expectedResults'].append(additionalDict)

    def addMessageFromHermesCollectorToSideKick(self, commandName, dict = {}, monitoredInstance=os.getenv("monitoredInstance"), instanceRole = "Primary"):
        "this function creates a new action, that describes the specified message being sent from the hermes collector to a sidekick"
        tableName = 'HermesCommand'

        serviceName = monitoredInstance + '-' + instanceRole + '-sidekickHermesControl'

        fromAttr = {
            'userId': getpass.getuser(),
            'requestManager': serviceName,
        }

        # 'message' is not defined in the request message, so if present we must remove it.
        keyValuePairs = unionOf(self.buildHermesCommandMessageFields(commandName, dict), fromAttr)
        if 'message' in keyValuePairs:
            del keyValuePairs['message']

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromHermes(serviceName),
                'table': tableName,
                'fields': keyValuePairs,
            },
        } )

    def addMessageFromSideKickToHermesCollector(self, commandName, dict = {}, monitoredInstance=os.getenv("monitoredInstance"), instanceRole = "Primary", additionalDict = None):
        "this function creates a new expectedResult, that describes the specified message being sent from a sidekick to the hermes collector"
        tableName = 'HermesCommandResult'

        serviceName = monitoredInstance + '-' + instanceRole + '-sidekickHermesControl'

        toAttr = {
            'requestManager': serviceName,
        }

        # Need 'status' and 'message' to be defined in dicts.  If not, we need to supply default 'Success'.
        # Need to prevent 'argumentVector' from appearing in response message.
        keyValuePairs = unionOf(self.buildHermesCommandMessageFields(commandName, dict), toAttr)
        if 'status' not in keyValuePairs:
            keyValuePairs['status'] = 'Success'
        if 'message' not in keyValuePairs:
            keyValuePairs['message'] = keyValuePairs['status']
        if 'argumentVector' in keyValuePairs:
            del keyValuePairs['argumentVector']

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToHermes(serviceName),
                'table': tableName,
                'fields': keyValuePairs,
            },
            'trace' : self.getTraceback(),
        })

        if additionalDict is not None:
            self.__data['expectedResults'].append(additionalDict)

    def getGSLogMessageBySeverity(self, severity, shortSeverity, numberOfMessages, toDss=False, instanceRole = "Primary"):
        "this function queries the engine for the number of logged messages of the specified severity"

        argumentVector = [{ 'arg' : severity}]

        if not toDss:
            self.addMessageFromHermesCollector('getNumMessagesLoggedBySeverity', {
                'argumentVector': argumentVector,
            } , instanceRole=instanceRole )

            self.addMessageToHermesCollector('getNumMessagesLoggedBySeverity', {'message' : (('Success - there were %d %s messages') % (numberOfMessages, shortSeverity)) }, instanceRole=instanceRole )
        else:
            self.addHermesMessageToDssFromCollector('getNumMessagesLoggedBySeverity', {
                'argumentVector': argumentVector,
            } , instanceRole=instanceRole )

            self.addMessageToHermesCollectorFromDss('getNumMessagesLoggedBySeverity', {'message' : (('Success - there were %d %s messages') % (numberOfMessages, shortSeverity)) }, instanceRole=instanceRole )

    def checkProcessTable(self, processName, state, messageId, action, searchString = "", checkWait = 1000, sim = '', async = True):
        "this function checks if process is running"
        serviceName = self.__applicationState.stripeName() + str(messageId)
        self.__data['expectedResults'].append( {
            'serviceType': 'check-process-manager','serviceName': serviceName,
            'simulator' : sim,
            'messageName' :  self.__applicationState.stripeName() + ' ' + str(messageId) + ' ' + processName + ' ' + action,
            'message': {
                'action': action,
                'process': processName,
                'state': state,
                'searchString': searchString,
                'checkWait': checkWait,
                'async': async,
            },
            'trace' : self.getTraceback(),
      })

    def verifyShmTable(self, tableName, column, value, matchField, segment, messageId):
        "this function verifies the shared memory"
        serviceName = self.__applicationState.stripeName()
        self.__data['expectedResults'].append( {
            'serviceType': 'verify-shm-manager','serviceName': serviceName,
            'messageName' :  self.__applicationState.stripeName() + ' ' + str(messageId),
            'message': {
                'table': tableName,
                'fields': matchField,
                'segment': segment,
                'columnId': column,
                'value': value,
            },
            'trace' : self.getTraceback(),
      })

    def updateShmTable(self, tableName, column, value, matchField, segment, messageId, setFields):
        "this function updates the shared memory"
        serviceName = self.__applicationState.stripeName()
        self.__data['actions'].append( {
            'serviceType': 'verify-shm-manager','serviceName': serviceName,
            'message': {
                'table': tableName,
                'fields': matchField,  #needed for insert row
                'segment': segment,
                'columnId': column,
                'value': value,
                'setField':setFields, #needed for update row
            },
        } )


    def addDelay(self, delayTime):
        "this function delays the dependent Testcase for the duration of delayTime"
        serviceName = 'delay'
        self.__data['actions'].append( {
            'serviceType': 'delay-manager', 'serviceName': serviceName,
            'delayDuration': delayTime,
        } )
        self.__data['expectedResults'].append( {
            'serviceType': 'delay-manager', 'serviceName': 'None',
        } )



    def addMessageFromClusterLockServer(self, commandName, dict = {}):
        tableName = 'ClusterLockSuccessResponse'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        fromAttr = {
            'lockName': (getpass.getuser() + '-simulator-lock', dict['lockName'])['lockName' in dict],
            'lockClientId': dict['response-client'],
            'lockState': dict['response-state'],
            'lockCommand': commandName,
        }

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
            'trace' : self.getTraceback(),
        })


    def addFailedMessageFromClusterLockServer(self, commandName, dict = {}):
        tableName = 'ClusterLockFailureResponse'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        fromAttr = {
            'lockName': dict['response-lockName'],
            'lockFailureReason': dict['response-reason'],
            'lockCommand': commandName,
        }

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageToClusterLockServer(self, commandName, dict = {}):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'ClusterLock' + commandName + 'Command'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        toAttr = {
            'lockName': (getpass.getuser() + '-simulator-lock', dict['lockName'])['lockName' in dict],
            'lockClientId': dict['client'],
        }

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToClusterLock(serviceName),
                'table': tableName,
                'fields': toAttr,
            },
        } )

    def addInvalidMessageToClusterLockServer(self, commandName, dict = {}):
        "this function creates a new action with an invalid message (HermesCommand), and an empty expectedResult"
        tableName = 'HermesCommand'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        commonAttributes = {
            'requestManager': serviceName,
            'cmd': commandName,
            'args': 'None', # this must be set
            'handle': commandName,
            'guiId': 12345, # this must be set
            'cmdId': 67890, # this must be set
            'userId': getpass.getuser(),
        }

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToClusterLock(serviceName),
                'table': tableName,
                'fields': commonAttributes,
            },
        } )

    def getLastMessageName(self):
        "this function returns the last action's message name"
        return self.__data['actions'][len(self.__data['actions'])-1]['messageName']

###
### New functions to help with AutoFailover
###
    def addStreamStatusCheck(self, type, streamName, statusEvent):
        "this function checks a specified stream's status"
        self.__data['expectedResults'].append( {
        'serviceType': type, 'serviceName': streamName,
	'messageName': self.__applicationState.nextMessageName(),
        'statusEvent': statusEvent,
        'trace' : self.getTraceback(),
        })

    def addLogScraperExpectedResults(self, logFileId, severes = 'false', data = []):
        "this function scrapes the specified log file using the supplied regular expressions"
        self.__data['expectedResults'].append( {
        'serviceType': 'log-scraper', 'serviceName': logFileId,
        'noSeveres': severes,
        'mustContainEntries' : data,
            'trace' : self.getTraceback(),
        })

    def addStartupRequestFromPrimaryServer(self, dict):
        tableName = 'ModeHandshake'
        serviceName = self.__applicationState.stripeName() + '->startupHandshake'

        fromAttr = {
            'currentMode': dict['state'],
            'startupHandshakeHeartbeatRequestInterval':dict['heartbeatRequestInterval'],
            'startupHandshakeMaximumConnectionFrequency':dict['maximumConnectionFrequency'],
            'startupHandshakeConnectionFailureInterval':dict['connectionFailureInterval'],
        }

        if 'startupHandshakeProtocolUsesCommitId' in dict:
            fromAttr['startupHandshakeProtocolUsesCommitId'] = dict['startupHandshakeProtocolUsesCommitId']
            if 'commitId' in dict:
                fromAttr['commitId'] = dict['commitId']

        self.__data['expectedResults'].append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
            'trace' : self.getTraceback(),
        })

    def addStartupResponseToPrimaryServer(self, dict):
        tableName = 'ModeHandshake'
        serviceName = self.__applicationState.stripeName() + '->startupHandshake'

        fromAttr = {
            'currentMode': dict['state'],
            'startupHandshakeHeartbeatRequestInterval':dict['heartbeatRequestInterval'],
            'startupHandshakeMaximumConnectionFrequency':dict['maximumConnectionFrequency'],
            'startupHandshakeConnectionFailureInterval':dict['connectionFailureInterval'],
        }

        if 'startupHandshakeProtocolUsesCommitId' in dict:
            fromAttr['startupHandshakeProtocolUsesCommitId'] = dict['startupHandshakeProtocolUsesCommitId']
            if 'commitId' in dict:
                fromAttr['commitId'] = dict['commitId']

        self.__data['actions'].append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
        })

    def addStartupRequestToPrimaryServer(self, dict):
        tableName = 'ModeHandshake'
        serviceName = 'startupHandshake->' + self.__applicationState.stripeName()

        fromAttr = {
            'currentMode': dict['state'],
            'startupHandshakeHeartbeatRequestInterval':dict['heartbeatRequestInterval'],
            'startupHandshakeMaximumConnectionFrequency':dict['maximumConnectionFrequency'],
            'startupHandshakeConnectionFailureInterval':dict['connectionFailureInterval'],
        }

        if 'startupHandshakeProtocolUsesCommitId' in dict:
            fromAttr['startupHandshakeProtocolUsesCommitId'] = dict['startupHandshakeProtocolUsesCommitId']
            if 'commitId' in dict:
                fromAttr['commitId'] = dict['commitId']

        self.__data['actions'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
        })

    def addStartupResponseFromPrimaryServer(self, dict):
        tableName = 'ModeHandshake'
        serviceName = 'startupHandshake->' + self.__applicationState.stripeName()

        fromAttr = {
            'currentMode': dict['state'],
            'startupHandshakeHeartbeatRequestInterval':dict['heartbeatRequestInterval'],
            'startupHandshakeMaximumConnectionFrequency':dict['maximumConnectionFrequency'],
            'startupHandshakeConnectionFailureInterval':dict['connectionFailureInterval'],
        }

        if 'startupHandshakeProtocolUsesCommitId' in dict:
            fromAttr['startupHandshakeProtocolUsesCommitId'] = dict['startupHandshakeProtocolUsesCommitId']
            if 'commitId' in dict:
                fromAttr['commitId'] = dict['commitId']

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
            'trace' : self.getTraceback(),
        })

    def addStartupRequestFromSecondaryServer(self, dict):
        tableName = 'ModeHandshake'
        serviceName = 'startupHandshake->' + self.__applicationState.stripeName()

        fromAttr = {
            'currentMode': dict['state'],
            'startupHandshakeHeartbeatRequestInterval':dict['heartbeatRequestInterval'],
            'startupHandshakeMaximumConnectionFrequency':dict['maximumConnectionFrequency'],
            'startupHandshakeConnectionFailureInterval':dict['connectionFailureInterval'],
        }

        if 'startupHandshakeProtocolUsesCommitId' in dict:
            fromAttr['startupHandshakeProtocolUsesCommitId'] = dict['startupHandshakeProtocolUsesCommitId']
            if 'commitId' in dict:
                fromAttr['commitId'] = dict['commitId']

        self.__data['expectedResults'].append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
            'trace' : self.getTraceback(),
        })

    def addStartupResponseToSecondaryServer(self, dict):
        tableName = 'ModeHandshake'
        serviceName = 'startupHandshake->' + self.__applicationState.stripeName()

        fromAttr = {
            'currentMode': dict['state'],
            'startupHandshakeHeartbeatRequestInterval':dict['heartbeatRequestInterval'],
            'startupHandshakeMaximumConnectionFrequency':dict['maximumConnectionFrequency'],
            'startupHandshakeConnectionFailureInterval':dict['connectionFailureInterval'],
        }

        if 'startupHandshakeProtocolUsesCommitId' in dict:
            fromAttr['startupHandshakeProtocolUsesCommitId'] = dict['startupHandshakeProtocolUsesCommitId']
            if 'commitId' in dict:
                fromAttr['commitId'] = dict['commitId']

        self.__data['actions'].append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
        })


    def addMessageFromSimulatedClusterLockServer(self, commandName, result, dict = {}):
        tableName = 'ClusterLock' + result + 'Response'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        if result.lower() == 'success':
            fromAttr = {
                'lockName': self.__applicationState.stripeName(),
                'lockClientId': dict['response-client'],
                'lockState': dict['response-state'],
                'lockCommand': commandName,
            }
	else:
            fromAttr = {
                'lockName': dict['response-lockName'],
                'lockFailureReason': dict['response-reason'],
                'lockCommand': commandName,
            }

        self.__data['actions'].append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
        })

    def addFailedMessageFromSimulatedClusterLockServer(self, commandName, dict = {}):
        tableName = 'ClusterLockFailureResponse'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        fromAttr = {
            'lockName': dict['response-lockName'],
            'lockFailureReason': dict['response-reason'],
            'lockCommand': commandName,
        }

        self.__data['actions'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromClusterLock(serviceName),
                'table': tableName,
                'fields': fromAttr,
            },
        })


    def verifyMessageToSimulatedClusterLockServer(self, commandName, dict = {}):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'ClusterLock' + commandName + 'Command'
        serviceName = self.__applicationState.stripeName() + '->clusterlock'

        toAttr = {
            'lockName': self.__applicationState.stripeName(),
            'lockClientId': dict['client'],
        }

        self.__data['expectedResults'].append( {
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToClusterLock(serviceName),
                'table': tableName,
                'fields': toAttr,
            },
            'trace' : self.getTraceback(),
        } )

    def addRequestToApplication(self, requestResponseName, tableName, dict):
        self.__data['actions'].append({
            'serviceType': 'client-request-manager',
            'serviceName': requestResponseName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToApplication(requestResponseName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addResponseFromApplication(self, requestResponseName, tableName, dict):
        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager',
            'serviceName': requestResponseName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'table': tableName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageFromSampleClient(self, tableName, dict):
        "this function creates a new action which sends a new message to the application"
        serviceName = 'sample->' + self.__applicationState.stripeName()
        self.__data['actions'].append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromSampleClient(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageToSampleClient(self, tableName, dict):
        "this function creates a new expected result for a message from the application"
        serviceName = self.__applicationState.stripeName() + '->sample'
        self.__data['expectedResults'].append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToSampleClient(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageAckToSampleClient(self, messageName):
        "this function creates a new expected result which waits for the message ack from a message sent to the application"
        serviceName = 'sample->' + self.__applicationState.stripeName()
        self.__data['expectedResults'].append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromSampleClient(serviceName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def enqueueMessageToServerDatastream(self, serverDatastreamName, tableName, dict):
        "this function creates a new action by enqueuing a new message to a server datastream"
        self.__data['actions'].append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serverDatastreamName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromSampleClient(serverDatastreamName),
                'table': tableName,
                'fields': dict,
            },
        })

    def receiveMessageFromClientDatastream(self, clientDatastreamName, tableName, dict):
        "this function creates a new expected result for a message from a client datastream"
        self.__data['expectedResults'].append( {
            'serviceType': 'client-datastream-manager', 'serviceName': clientDatastreamName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToSampleClient(clientDatastreamName),
                'table': tableName,
                'fields': dict,
            },
        })

    def receiveMessageAckOnServerDatastream(self, serverDatastreamName, messageName):
        "this function creates a new action by enqueuing a new message to a server datastream"
        self.__data['expectedResults'].append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serverDatastreamName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromSampleClient(serverDatastreamName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def receiveMessageToSimulatedSideKick(self, commandName, dict):
        tableName = commandName
        serviceName = self.__applicationState.stripeName() + '->sidekick'

        toAttr = {
            'instanceName': self.__applicationState.stripeName(),
        }

        self.__data['expectedResults'].append({
            'serviceType': 'server-request-manager',
            'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'table': tableName,
                'fields': toAttr,
            },
            'trace' : self.getTraceback(),
        })


    def sendMessageFromSimulatedSideKick(self, commandName, dict):
        tableName = commandName
        serviceName = self.__applicationState.stripeName() + '->sidekick'

        fromAttr = {
            'timeOfLastActivity': dict['time'],
            'currentEngineState': dict['currentState'],
            'lastNotificationId': dict['lastId'],
            'sideKickResponseType': dict['responseType'],
        }

        self.__data['actions'].append({
            'serviceType': 'server-request-manager',
            'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'table': tableName,
                'fields': fromAttr,
            },
        })



    def addMessageToSideKick(self, commandName, dict = {}):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'SideKickRequestEngineState'
        serviceName = self.__applicationState.stripeName() + '->sidekick'

        fromAttr = {
            'instanceName': self.__applicationState.stripeName(),
        }

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'table': tableName,
                'fields': fromAttr,
            },
            'trace' : self.getTraceback(),
        } )


    def addMessageFromSideKick(self, commandName, dict = {}):
        tableName = commandName
        serviceName = self.__applicationState.stripeName() + '->sidekick'

        toAttr = {
            'timeOfLastActivity': '{*}',
            'currentEngineState': 'Running',
            'lastNotificationId': '{*}',
            'sideKickResponseType': 'Success',
        }

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'table': tableName,
                'fields': toAttr,
            },
            'trace' : self.getTraceback(),
        })

    def restrictSideKickBasedReplication(self, dict, monitoredInstance=os.getenv("monitoredInstance"), instanceRole = "Primary"):
        "this function sends a hermes command to the SideKick to restrict the replication of the last few TransactionNotification messages"
        argumentVector = []
        for key in dict:
            argumentVector.append(key)

        self.addMessageFromHermesCollectorToSideKick('setSideKickReplicationLimit', {
            'argumentVector': argumentVector, }, monitoredInstance, instanceRole)

        self.addMessageFromSideKickToHermesCollector('setSideKickReplicationLimit', {}, monitoredInstance, instanceRole)

    def addHermesMessageToCLSFromCollector(self, commandName, dict = {}, instanceRole = "Primary"):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'HermesCommand'

        serviceName = 'clusterlock-' + os.getenv("monitoredInstance") + '-' + instanceRole

        fromAttr = {
            'userId': getpass.getuser(),
            'requestManager': serviceName,
        }

        # 'message' is not defined in the request message, so if present we must remove it.
        kvps = unionOf(self.buildHermesCommandMessageFields(commandName, dict), fromAttr)
        if 'message' in kvps:
            del kvps['message']

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdFromHermes(serviceName),
                'table': tableName,
                'fields': kvps,
            },
        } )

    def addMessageToHermesCollectorFromCLS(self, commandName, dict = {}, instanceRole = "Primary"):
        tableName = 'HermesCommandResult'

        serviceName = 'clusterlock-' + os.getenv("monitoredInstance") + '-' + instanceRole

        toAttr = {
            'requestManager': serviceName,
        }

        # Need 'status' and 'message' to be defined in dicts.  If not, we need to supply default 'Success'.
        # Need to prevent 'argumentVector' from appearing in response message.
        kvps = unionOf(self.buildHermesCommandMessageFields(commandName, dict), toAttr)
        if 'status' not in kvps:
            kvps['status'] = 'Success'
        if 'message' not in kvps:
            kvps['message'] = kvps['status']
        if 'argumentVector' in kvps:
            del kvps['argumentVector']

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToHermes(serviceName),
                'table': tableName,
                'fields': kvps,
            },
            'trace' : self.getTraceback(),
        })

    def addRequestResponseCommandToApplication(self, commandName, dict):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'CommandRequest'
        serviceName = 'application-' + self.__applicationState.stripeName() + '-requestResponse'

        self.__data['actions'].append( {
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'messageId': self.__applicationState.nextMessageIdToUpstreamOms(serviceName),
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        } )

    def addRequestResponseResponseFromApplication(self, commandName, dict):
        tableName = 'CommandResponse'
        serviceName = 'application-' + self.__applicationState.stripeName() + '-requestResponse'

        self.__data['expectedResults'].append({
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.__applicationState.nextMessageName(),
            'message': {
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addStartServerDatastreamMessage(self, serviceName):
        "this function creates a action to start/stop server datastream"
        self.__data['actions'].append( {
        'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
        'actionName': 'start'
        })

    def addStopServerDatastreamMessage(self, serviceName):
        "this function creates a action to start/stop server datastream"
        self.__data['actions'].append( {
        'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
        'actionName': 'stop'
        })

    def addStartClientDatastreamMessage(self, serviceName, replayMessageId = 0):
        "this function creates a action to start/stop client datastream"
        self.__data['actions'].append( {
        'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
        'actionName': 'start', 'replayMessageId': replayMessageId
        })

    def addStopClientDatastreamMessage(self, serviceName):
        "this function creates a action to start/stop client datastream"
        self.__data['actions'].append( {
        'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
        'actionName': 'stop'
        })


    def addStartClientCyclopsMessage(self, serviceName):
        "this function creates a action to start client cyclops datastream"
        self.__data['actions'].append( {
        'serviceType': 'client-cyclops-manager', 'serviceName': serviceName,
        'actionName': 'start'
        })

    def addStopClientCyclopsMessage(self, serviceName):
        "this function creates a action to stop client cyclops datastream"
        self.__data['actions'].append( {
        'serviceType': 'client-cyclops-manager', 'serviceName': serviceName,
        'actionName': 'stop'
        })


    def addStartServerRequestMessage(self, serviceName):
        "this function creates a action to start server request stream"
        self.__data['actions'].append( {
        'serviceType': 'server-request-manager', 'serviceName': serviceName,
        'actionName': 'start'
        })

    def addStopServerRequestMessage(self, serviceName):
        "this function creates a action to stop server request stream"
        self.__data['actions'].append( {
        'serviceType': 'server-request-manager', 'serviceName': serviceName,
        'actionName': 'stop'
        })

    def addStartClientRequestMessage(self, serviceName):
        "this function creates a action to start client request stream"
        self.__data['actions'].append( {
        'serviceType': 'client-request-manager', 'serviceName': serviceName,
        'actionName': 'start'
        })

    def addStopClientRequestMessage(self, serviceName):
        "this function creates a action to stop client request stream"
        self.__data['actions'].append( {
        'serviceType': 'client-request-manager', 'serviceName': serviceName,
        'actionName': 'stop'
        })

    def addMessageToDb(self, dbConnectionName,  messageId, message):
        self.__data['actions'].append( {
            'serviceType': 'db-process-manager', 'serviceName': dbConnectionName,
            'messageName' :  self.__applicationState.stripeName() + ' ' + str(messageId),
            'message': {
            'messageId': messageId,
            'dbFields': message,
            },
    })

    def addMessageFromDb(self, dbConnectionName,  messageId, matchField, message):
        self.__data['expectedResults'].append( {
            'serviceType': 'db-process-manager', 'serviceName': dbConnectionName,
            'messageName' :  self.__applicationState.stripeName() + ' ' + str(messageId),
            'conclusionMatchField': matchField,
            'message': {
            'messageId': messageId,
            'dbFields': message,
            'trace' : self.getTraceback(),
            },
    })

###
### New convenience functions to help with time overrides.  Expects values in local time and date (not GMT).
###
    def startOverridingTheTime(self, newTime = '12:33:15', microseconds = -1, newDate = None, keepTicking = False, instanceRole = "Primary"):
        """
        Override the time in the application.
        @param newTime local time string 'HH:MM:SS' (no microseconds).  Defaults to current local time '12:33:15'.
        @param microseconds the microseconds value to set.  By default the next increasing microsecond tick.
        @param newDate local date string 'YYYYMMDD'.  Defaults to current local date.
        @param keepTicking True if the time should keep ticking from the overriden time
        """
        global globalMicrosecondCount

        pieces = newTime.split(":")
        if len(pieces) != 3:
            raise KevlarTestException("KevlarTestCase.py-S-startOverridingTheTime() was called incorrectly, must specify time string as HH:MM:SS, not [" + newTime + "]")

        if microseconds < 0:
            globalMicrosecondCount += 1  # We want to start at 1 and automatically tick slowly up to 999,999 with each override call.
            microseconds = globalMicrosecondCount

        newTimeStr = "overrideTime %s:%d" % (newTime, microseconds) # 'hour:minute:seconds', microseconds

        argumentList = []
        argumentList.append({'arg': newTimeStr})

        if newDate:
            if len(newDate) != 8:
                raise KevlarTestException("KevlarTestCase.py-S-startOverridingTheTime() was called with invalid newDate length, must specify in format YYYYMMDD, not [" + newDate + "]")
            try:
                int(newDate)
            except ValueError:
                raise KevlarTestException("KevlarTestCase.py-S-startOverridingTheTime() was called with invalid newDate value, must specify in format YYYYMMDD, not [" + newDate + "]")

            argumentList.append({'arg': "overrideDate %s" % newDate})
        else:
            # Default to the current local date on which testing began.
            # This helps prevent test suites from being impacted by a GMT midnight crossing during testing.
            argumentList.append({'arg': "overrideDate %s" % currentLocalDateStr})

        if keepTicking:
            argumentList.append({'arg': "keepTickingFromThisTime"})

        self.addMessageFromHermesCollector('startOverridingTheTime',
        {
            'argumentVector': argumentList
        }, instanceRole)

        self.addMessageToHermesCollector('startOverridingTheTime', {}, instanceRole)

    def stopOverridingTheTime(self, instanceRole = "Primary"):
        """
        Stop overriding the time
        """

        self.addMessageFromHermesCollector('stopOverridingTheTime', {}, instanceRole)
        self.addMessageToHermesCollector('stopOverridingTheTime', {}, instanceRole)

    def getCurrentTimeOverrideMicrosecondTick(self):
        """
        Returns the most recently overriden microsecond tick value.
        """

        return globalMicrosecondCount

    def resetTimeOverrideMicrosecondTick(self, value = 0):
        """
        Resets the most recently overriden microsecond tick value.
        @param value sets the microsecond value last used to override the time,
               will be incremented during next call to startOverridingTheTime()
               that does not supply a microsecond value.  Defaults to resetting it to 0.
        """
        global globalMicrosecondCount

        if value < 0:
            globalMicrosecondCount = 0
        else:
            globalMicrosecondCount = value

    def addStopSendingImageLiveProcessingAcksMessage(self):
        serviceName = 'imageliveserver-' + self.state().stripeName()
        "this function creates a action to stop automatically sending processing acks on record update"
        self.__data['actions'].append( {
            'serviceType': 'image-live-client', 'serviceName': serviceName,
            'actionName': 'stopSendingProcessingAcks'
        })

    def addStartSendingImageLiveProcessingAcksMessage(self):
        serviceName = 'imageliveserver-' + self.state().stripeName()
        "this function creates a action to start automatically sending processing acks on record update"
        self.__data['actions'].append( {
            'serviceType': 'image-live-client', 'serviceName': serviceName,
            'actionName': 'startSendingProcessingAcks'
        })

    def addImageLiveProcessingAck(self, viewName, recordId, version):
        serviceName = 'imageliveserver-' + self.state().stripeName()
        self.__data['actions'].append( {
            'serviceType': 'image-live-client', 'serviceName': serviceName,
            'actionName': 'sendProcessingAck',
            'viewName': viewName,
            'recordId': recordId,
            'version': version,
        })

