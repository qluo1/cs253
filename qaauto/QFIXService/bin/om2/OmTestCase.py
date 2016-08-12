from OmEngineState import OmEngineState
import os
from om2CommandCatalog import om2CommandCatalog
import om2CompleteCatalog
import getpass
import traceback
import KevlarTestCase



def embeddedIf(expr, trueRet, falseRet):
    return KevlarTestCase.embeddedIf(expr, trueRet, falseRet)

class OmTestCaseException(KevlarTestCase.KevlarTestCaseException):
    def __init__(self, value):
        KevlarTestCase.KevlarTestCaseException.__init__(self, value)

# static functions
def printConfiguration(toPrint):
    KevlarTestCase.printConfiguration(toPrint)

def unionOf(*dicts):
    return KevlarTestCase.unionOf(*dicts)

def filter(dict, fieldList):
    """
    filter out dictionary with only specified fields.
    \param dict      dictionary to be filtered
    \param fieldList list of field names to be returned in the new dictionary
    \return dictionary with filered result
    """
    result = {}
    for k, v in dict.iteritems():
        if k in fieldList:
            result[k] = v
    return result

def merge(*dicts):
    return KevlarTestCase.merge(*dicts)

def localGmtOffset():
    return KevlarTestCase.localGmtOffset()

def wildCardAll(tableName):
    """
    get a dictionary for a message with all fields set as wild cards
    \param tableName name of the message table
    \return a wild carded message
    """
    result = {}

    if tableName in om2CompleteCatalog.om2CompleteCatalog['tables']:
        for column in om2CompleteCatalog.om2CompleteCatalog['tables'][tableName]['columns'].keys():
            result[column] = '{?}'
    else:
        import cyclopsCatalog
        for column in cyclopsCatalog.cyclopsCatalog['tables'][tableName]['columns'].keys():
            result[column] = '{?}'

    return result

def wildCardAllExcept(tableName, exceptionList = []):
    """
    get a dictionary for a message with all fields set as wild cards, except certain fields.
    \param tableName     name of the message table
    \param exceptionList list of fields not to be wildcarded
    \return a wild carded message
    """
    result = {}

    if tableName in om2CompleteCatalog.om2CompleteCatalog['tables']:
        for column in om2CompleteCatalog.om2CompleteCatalog['tables'][tableName]['columns'].keys():
            if column not in exceptionList:
                result[column] = '{?}'
    else:
        import cyclopsCatalog
        for column in cyclopsCatalog.cyclopsCatalog['tables'][tableName]['columns'].keys():
            if column not in exceptionList:
                result[column] = '{?}'

    return result

class OmTestCase(KevlarTestCase.KevlarTestCase):
    "This class represents an order. Only the OmEngineState should construct objects of this type"

    def __init__(self, engineState, testCaseName, dependencies=None, expectedResultsInOrder=False):
        "this method initializes an order, the caller may optionally specify a dictionary of order attributes to override the default attributes"
        KevlarTestCase.KevlarTestCase.__init__(self, engineState, testCaseName, dependencies=None, expectedResultsInOrder=False)

    def addMessageFromApollo(self, tableName, dict, apolloInstance = 'apollo'):
        "this function creates a new action, and updates the engine state"
        serviceName = apolloInstance + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromApollo(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageToApollo(self, tableName, dict, checkMessageListOrder = "false"):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->apollo'
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToApollo(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageToDropCopy(self, tableName, dict, checkMessageListOrder = "false"):
        "this function adds an expected result that the simulator should expect over the drop copy interface"
        serviceName = self.state().stripeName() + '->dropCopy'
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToDropCopy(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageFromIoiProvider(self, tableName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = 'ioi->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromIoiProvider(serviceName),
                #'messageId': "FOOBAR",
                'table': tableName,
                'fields': dict,
            },
        })


    def addMessageToVerifyTransactionLogManagerForApollo(self, tableName, dict, checkMessageListOrder = "false"):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->apollo'
        self.clearActions()
        self.expectedResults().append( {
            'serviceType': 'verify-transaction-log-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().previousMessageIdToApollo(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageToOma(self, message, serviceName = 'simulator-oma', tableName = ''):
        """
        Send an NVPSequence message to OMA
        The specification of an NVP Sequence:

        NVP         := {'<nvpName>': {'type': <nvpType>, 'value': <nvpValue>} }
        NVPList     := [NVP*]
        NVPObject   := {'objectName': NVPList }
        NVPSequence := NVPList | NVPObject

        \param message     NVPSequence to be fed in.
        \param serviceName should be simulator-oma
        \param tableName   Not used, can be any value
        """
        self.actions().append( {
             'serviceType': 'oma-line', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'message': [{
                 'table': tableName,
                 'fields': message,
             }],
         })

    def addMessageFromOma(self, message, serviceName = '', tableName = '', selectiveMatch= False):
        """
        Expect Orbix message output from OMA

        \param serviceName for TransactionJournal output, 'TXNLOG_<OMSNAME>'
        \param message     expected NVPSequence to be fed in.
        \param tableName   Not used, can be any value
        \param selectiveMatch whether using selective match mode, default is 'False'
        """
        self.expectedResults().append( {
            'serviceType': 'oma-line', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': [{
                'table': tableName,
                'fields': message,
            }],
            'trace' : self.getTraceback(),
            'selectiveMatch': str(selectiveMatch),
        })

    def addMessageFromCustomer(self, serviceName, tableName, messageId, message):
        self.actions().append( {
            'serviceType': 'fix-line', 'serviceName': serviceName,
            'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
      })

    def addMessageToCustomer(self, serviceName, tableName, messageId, matchField, message):
        self.expectedResults().append( {
            'serviceType': 'fix-line', 'serviceName': serviceName,
            'expectedResultMatchField': matchField,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
      })

    def addMessageFromSrc(self, serviceType, serviceName, tableName, messageId, message):
        self.actions().append( {
            'serviceType': serviceType, 'serviceName': serviceName,
            'message': {
                'messageId': {'nextMessageId' : 'session1'},
                'table': tableName,
                'fields': message,
            },
      })


    def addMessageToSrc(self, serviceType, serviceName, tableName, messageId, matchField, message):
        self.expectedResults().append( {
            'serviceType': serviceType, 'serviceName': serviceName,
            'expectedResultMatchField': matchField,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
      })

    def addMessageFromRashSrc(self, serviceName, tableName, messageId, message):
        self.actions().append( {
            'serviceType': 'rash-line', 'serviceName': serviceName,
            'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
      })

    def addMessageToRashSrc(self, serviceName, tableName, messageId, matchField, message):
        self.expectedResults().append( {
            'serviceType': 'rash-line', 'serviceName': serviceName,
            'expectedResultMatchField': matchField,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
      })

    def addMessageFromOuchSrc(self, serviceName, tableName, messageId, message):
        self.actions().append( {
            'serviceType': 'ouch-line', 'serviceName': serviceName,
            'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
      })

    def addMessageToOuchSrc(self, serviceName, tableName, messageId, matchField, message):
        self.expectedResults().append( {
            'serviceType': 'ouch-line', 'serviceName': serviceName,
            'expectedResultMatchField': matchField,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
      })

    def addMessageFromRashOuchSrc(self, serviceName, tableName, messageId, message):
        self.actions().append( {
            'serviceType': 'rashouch-line', 'serviceName': serviceName,
            'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
      })

    def addMessageToRashOuchSrc(self, serviceName, tableName, messageId, matchField, message):
        self.expectedResults().append( {
            'serviceType': 'rashouch-line', 'serviceName': serviceName,
            'expectedResultMatchField': matchField,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
      })

    def addMessageToViking(self, tableName, vikingInstance, dict, checkMessageListOrder = "false" ):
        "this function creates an expected result, and updates the engine state"
        serviceName = self.state().stripeName() + '->' +  vikingInstance
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToViking(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageToVerifyTransactionLogManagerForViking(self, tableName, vikingInstance, dict, checkMessageListOrder = "false" ):
        "this function creates an expected result, and updates the engine state"
        serviceName = self.state().stripeName() + '->' + vikingInstance
        self.clearActions()
        self.expectedResults().append( {
            'serviceType': 'verify-transaction-log-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().previousMessageIdToViking(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageFromViking(self, tableName, vikingInstance, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = vikingInstance + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromViking(serviceName),
                'table': tableName,
                'fields': dict,
            },
        } )


    # Simulator is acting as an upstream oms
    # For sending orders, corrections and cancellations downstream
    def addMessageFromUpstreamOms(self, omsName, tableName, messageData):
        serviceName = omsName + '->' + self.state().stripeName()
        messageId = self.state().nextMessageIdFromUpstreamOms(serviceName)
        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.actions().append({
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': messageId,
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': serviceName + "_" + str(self.state().nextGenericUniqueId(serviceName)), } ],
                    'sourceSystemName': omsName,
                    'destinationSystemName': self.state().stripeName(),
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                }
            },
        })

    # Simulator is acting as an upstream oms
    # For receiving accepts, rejects and executions from downstream
    def addMessageToUpstreamOms(self, omsName, tableName, messageData, checkMessageListOrder = "false"):
        serviceName = self.state().stripeName() + '->' + omsName
        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.expectedResults().append({
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': '{*}', 'isPosDup': '{*}', 'commandTime': '{*}', 'creatorId': '{?}', 'creatorIdType': '{?}', 'eventTrailData': '{?}'} ],
                    'sourceSystemName': self.state().stripeName(),
                    'destinationSystemName': omsName,
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                },
                'checkOrder': checkMessageListOrder,
            },
            'trace' : self.getTraceback(),
        })


    # Simulator is acting as a downstream oms, but match destinationSystemName with destination
    # For receiving orders, corrections and cancellations from upstream
    def addMessageToDownstreamOmsWithDestination(self, omsName, tableName, messageData, destination):
        serviceName = self.state().stripeName() + '->' + omsName
        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.expectedResults().append({
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToDownstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': '{*}', 'isPosDup': '{*}', 'commandTime': '{*}', 'creatorId': '{*}', 'creatorIdType': '{*}' } ],
                    'sourceSystemName': self.state().stripeName(),
                    'destinationSystemName': destination,
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                },
            },
            'trace' : self.getTraceback(),
        })

    # Simulator is acting as a downstream oms
    # For receiving orders, corrections and cancellations from upstream
    def addMessageToDownstreamOms(self, omsName, tableName, messageData, shouldWildCardCommandHeader=False):
        serviceName = self.state().stripeName() + '->' + omsName
        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.expectedResults().append({
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToDownstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': embeddedIf(shouldWildCardCommandHeader, '{*}', [ { 'posDupId': '{*}', 'isPosDup': '{*}', 'commandTime': '{*}', 'creatorId': '{*}', 'creatorIdType': '{*}' } ]),
                    'sourceSystemName': self.state().stripeName(),
                    'destinationSystemName': omsName,
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                },
            },
            'trace' : self.getTraceback(),
        })

    # Simulator is acting as a downstream apollo instance
    def addRoutedFixMessageToApollo(self, omsName, destinationSystemName, fixTags):
        serviceName = self.state().stripeName() + '->' + omsName

        messageData = '{*}' if fixTags == '{*}' else { 'fixTags' : fixTags }

        self.expectedResults().append({
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToDownstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': '{*}', 'isPosDup': '{*}', 'commandTime': '{*}',  } ],
                    'sourceSystemName': self.state().stripeName(),
                    'destinationSystemName': destinationSystemName,
                    'messageFormat' : 'Fix',
                    'messageData' : messageData,
                },
            },
            'trace' : self.getTraceback(),
        })

    # Simulator is acting as a downstream oms
    # For sending accepts, rejects and executions back upstream
    def addMessageFromDownstreamOms(self, omsName, tableName, messageData):
        serviceName = omsName + '->' + self.state().stripeName()
        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromDownstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': serviceName + "_" + str(self.state().nextGenericUniqueId(serviceName)), } ],
                    'sourceSystemName': omsName,
                    'destinationSystemName': self.state().stripeName(),
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                }
            },
        })


    def changeMarketData(self, dict, instanceRole = "Primary"):
        "this function changes the market data"
        if not self.state().isMarketDataOverridden():
            self.state().marketDataIsOverridden(True)
            self.addMessageFromHermesCollector('startOverridingMarketData', instanceRole=instanceRole)
            self.addMessageToHermesCollector('startOverridingMarketData', instanceRole=instanceRole)

        argumentVector = []
        for key in dict:
            argumentVector.append(key)

        self.addMessageFromHermesCollector('setMarketData', {
            'argumentVector': argumentVector,
        } , instanceRole=instanceRole)

        self.addMessageToHermesCollector('setMarketData', instanceRole=instanceRole)

    def changeCreditUsageData(self, dict, instanceRole = "Primary"):
        "this function changes the credit usage market data"
        if not self.state().isMarketDataOverridden():
            self.state().marketDataIsOverridden(True)
            self.addMessageFromHermesCollector('startOverridingMarketData', instanceRole=instanceRole)
            self.addMessageToHermesCollector('startOverridingMarketData', instanceRole=instanceRole)

        argumentVector = []
        for key in dict:
            argumentVector.append(key)

        self.addMessageFromHermesCollector('setCreditUsageData', {
            'argumentVector': argumentVector,
        } , instanceRole=instanceRole)

        self.addMessageToHermesCollector('setCreditUsageData', instanceRole=instanceRole)

    def changePositionData(self, dict, instanceRole = "Primary"):
        "this function changes the market data"
        if not self.state().isMarketDataOverridden():
            self.state().marketDataIsOverridden(True)
            self.addMessageFromHermesCollector('startOverridingMarketData', instanceRole=instanceRole )
            self.addMessageToHermesCollector('startOverridingMarketData', instanceRole=instanceRole)

        argumentVector = []
        for key in dict:
            argumentVector.append(key)

        self.addMessageFromHermesCollector('setPositionData', {
            'argumentVector': argumentVector,
        }, instanceRole=instanceRole)

        self.addMessageToHermesCollector('setPositionData', instanceRole=instanceRole)


    def changeImbalanceData(self, dict, instanceRole = "Primary"):
        "this function changes the imbalance"

        argumentVector = []
        for key in dict:
            argumentVector.append(key)

        self.addMessageFromHermesCollector('setImbalanceData', {
            'argumentVector': argumentVector,
        }, instanceRole=instanceRole )

        self.addMessageToHermesCollector('setImbalanceData', instanceRole=instanceRole)

    def changeLiquidityQuoteData(self, dict, instanceRole = "Primary"):
        "this function changes the liquidity quotes"

        if not self.state().isMarketDataOverridden():
            self.state().marketDataIsOverridden(True)
            self.addMessageFromHermesCollector('startOverridingMarketData', instanceRole=instanceRole)
            self.addMessageToHermesCollector('startOverridingMarketData', instanceRole=instanceRole)

        argumentVector = []
        for key in dict:
            argumentVector.append(key)

        self.addMessageFromHermesCollector('setLiquidityQuoteData', {
            'argumentVector': argumentVector,
        }, instanceRole=instanceRole )

        self.addMessageToHermesCollector('setLiquidityQuoteData', instanceRole=instanceRole)

    def addHermesMessageToDssFromCollector(self, commandName, dict = {}, instanceRole = "Primary"):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'HermesCommand'

        serviceName = self.state().stripeName() + '-DSS' + '-' + instanceRole

        fromAttr = {
            'userId': getpass.getuser(),
            'requestManager': serviceName,
        }

        # 'message' is not defined in the request message, so if present we must remove it.
        kvps = unionOf(self.buildHermesCommandMessageFields(commandName, dict), fromAttr)
        if 'message' in kvps:
            del kvps['message']

        self.actions().append( {
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromHermes(serviceName),
                'table': tableName,
                'fields': kvps,
            },
        } )

    def addMessageToHermesCollectorFromDss(self, commandName, dict = {}, instanceRole = "Primary"):
        tableName = 'HermesCommandResult'

        serviceName = self.state().stripeName() + '-DSS' + '-' + instanceRole

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

        self.expectedResults().append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToHermes(serviceName),
                'table': tableName,
                'fields': kvps,
            },
            'trace' : self.getTraceback(),
        })

    def printT2XmlSchemaToFile(self, filePath, instanceRole = "Primary"):
        "this function prints xml schemas for each rule engine in OM"

        argumentVector = [{ 'arg' : filePath}]
        self.addMessageFromHermesCollector('printT2XmlSchemaToFile', {
             'argumentVector' : argumentVector,
        } , instanceRole=instanceRole )

        self.addMessageToHermesCollector('printT2XmlSchemaToFile', {'message' : 'Success' }, instanceRole=instanceRole)


    def addMessageAckToApollo(self, messageName):
        "this function creates a new expected result which waits for a message ack"
        serviceName = 'apollo->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromApollo(serviceName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def addRoutedFixMessageFromApollo(self, fixFields, apolloInstance):
        "this function creates a new expected result which waits for a message ack"
        serviceName = apolloInstance + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'fixFields': fixFields,
            'trace' : self.getTraceback(),
         })

    def addMessageFromDSS(self):
        "this function creates a new expected result which waits for a message ack"
        serviceName = 'DSS' + self.state().stripeName() + '->replication'
        self.expectedResults().append( {
             'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'message': {
                 'messageId': self.state().nextMessageIdToDSS(),
                 'table': 'TransactionNotification',
                 'fields': '{*}',
             },
            'trace' : self.getTraceback(),
         })

    def addMessageFromOmEngine(self):
        "this function creates a new expected result which waits for a message ack"
        serviceName = self.state().stripeName() + '->replication'
        self.expectedResults().append( {
             'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'message': {
                 'messageId': self.state().nextMessageIdToOmEngine(),
                 'table': 'TransactionNotification',
                 'fields': '{*}',
             },
            'trace' : self.getTraceback(),
         })

    def addInputMessageAckToViking(self, vikingInstance, messageName):
        "this function creates a new expected result which waits for a message ack"
        serviceName = self.state().stripeName() + '->' + vikingInstance
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromViking(serviceName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def addMessageAckToViking(self, vikingInstance, messageName):
        "this function creates a new expected result which waits for a message ack"
        serviceName = vikingInstance + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromViking(serviceName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def addMessageAckToInventoryManager(self, imInstance, messageName):
        "this function creates a new expected result which waits for a message ack"
        serviceName = imInstance + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromInventoryManager(serviceName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def addMessageAckToAdvisor(self, imInstance, messageName):
        "this function creates a new expected result which waits for a message ack"
        serviceName = imInstance + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId': self.state().previousMessageIdFromAdvisor(serviceName, messageName),
             },
            'trace' : self.getTraceback(),
         })

    def addMessageAckToDownstreamOms(self, omsName, messageName):
        """this function creates a new expected result which waits for a message ack"""
        serviceName = omsName + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId':
                 self.state().previousMessageIdFromDownstreamOms(serviceName, messageName),
             },
         })

    def addMessageAckToSsr(self, ssrName, messageName):
        """this function creates a new expected result which waits for a message ack"""
        serviceName = ssrName + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId':
                 self.state().previousMessageIdFromSsr(serviceName, messageName),
             },
         })

    def addMessageAckToMasterAggregator(self, maName, messageName):
        """this function creates a new expected result which waits for a message ack"""
        serviceName = maName + '->' + self.state().stripeName()
        self.expectedResults().append( {
             'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
             'messageName': self.state().nextMessageName(),
             'messageAck': {
                 'messageId':
                 self.state().previousMessageIdFromMasterAggregator(serviceName, messageName),
             },
         })

###
### New functions to help with AutoFailover
###
    def addMessageToImageLiveServer(self, actionName, targetTable, dict = {}):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = targetTable
        serviceName = 'imageliveserver-' + self.state().stripeName()

        self.actions().append( {
            'serviceType': 'image-live-client',
            'imageLiveMethodName': actionName,
            'serviceName': serviceName,
            'messageName': self.testCaseName() + ' ' + tableName + ' ' + actionName + self.messageNum(),
            'message': {
                'table': tableName,
                'messageId' : '1',
                'fields': dict,
            },
        } )

    def addMessageFromImageLiveServer(self, tableName, dict = {}):
        serviceName = 'imageliveserver-' + self.state().stripeName()

        self.expectedResults().append({
            'serviceType': 'image-live-client',
            'serviceName': serviceName,
            'messageName': self.testCaseName() + ' ' + tableName + self.messageNum(),
            'message': {
               'table': tableName,
               'messageId' : '2',
               'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addRequestResponseCommandToDss(self, commandName, dict):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'CommandRequest'
        serviceName  = 'imagelive-' + self.state().stripeName() + '-requestResponse'

        self.actions().append( {
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        } )

    def addRequestResponseResponseFromDss(self, commandName, dict):
        tableName = 'CommandResponse'
        serviceName  = 'imagelive-' + self.state().stripeName() + '-requestResponse'

        self.expectedResults().append({
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addRequestResponseCommandToOmReinstater(self, commandName, dict):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'CommandRequest'
        serviceName  = 'omreinstater-' + self.state().stripeName() + '-requestResponse'

        self.actions().append( {
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        } )

    def addRequestResponseResponseFromOmReinstater(self, commandName, dict):
        tableName = 'CommandResponse'
        serviceName  = 'omreinstater-' + self.state().stripeName() + '-requestResponse'

        self.expectedResults().append({
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addRoutedMessageToRouter(self, sourceOms, destOms, tableName, messageData, messageID = -1):
        serviceName = sourceOms + '->' + self.state().stripeName();

        if messageID == -1:
            messageID = self.state().nextMessageIdToUpstreamOms(serviceName);

        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }

        fields = {
            'commandHeader': [ { 'posDupId': serviceName + "_" + str(self.state().nextGenericUniqueId(serviceName)), } ],
            'sourceSystemName': sourceOms,
            'tableId': om2CommandCatalog['tables'][tableName]['id'],
            'messageData': messageData,
            'messageFormat' : 'Iv',
        }

        if destOms != '':
            fields['destinationSystemName'] = destOms

        self.actions().append({
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': fields,
            },
        })

    def addRoutedMessageFromRouter(self, sourceOms, destOms, tableName, messageData, noAction = False, includeDestinationInMessage = True):
        serviceName  = self.state().stripeName() + '->' + destOms

        if noAction == True:
            self.clearActions()

        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }

        fields = {
            'commandHeader': [ { 'posDupId': '{?}', 'isPosDup': '{?}', 'commandTime': '{?}', 'creatorId': '{?}', 'creatorIdType': '{?}' } ],
            'sourceSystemName': sourceOms,
            'tableId': om2CommandCatalog['tables'][tableName]['id'],
            'messageData': messageData,
            'messageFormat' : 'Iv',
        }

        if includeDestinationInMessage:
            fields['destinationSystemName'] = destOms


        self.expectedResults().append({
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': 'RoutedMessage',
                'fields': fields,
            },
            'trace' : self.getTraceback(),
        })

    def addRoutedRequestMessageFromRouter(self, inboundOmsName, outboundOmsName, tableName, messageData, noAction = False):
        serviceName  = 'engine-' + outboundOmsName + '-requestResponse'

        if noAction == True:
            self.clearActions()

        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.expectedResults().append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': '{?}', 'isPosDup': '{?}', 'commandTime': '{?}', 'systemName' : '{?}' } ],
                    'sourceSystemName': inboundOmsName,
                    'destinationSystemName': '{?}', # might be missing if the request did not have a destination in mind
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                },
            },
            'trace' : self.getTraceback(),
        })

    def addRoutedResponseMessageToRouter(self, sourceOms, destOms, tableName, messageData, messageID = -1):
        serviceName = 'engine-' + sourceOms + '-requestResponse';

        self.actions().append({
            'serviceType': 'server-request-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': serviceName + "_" + str(self.state().nextGenericUniqueId(serviceName)), } ],
                    'sourceSystemName': self.state().stripeName(),
                    'destinationSystemName': destOms,
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                },
            },
        })


    def addRoutedResponseMessageFromRouter(self, inboundOmsName, outboundOmsName, tableName, messageData, noAction = False):
        serviceName  = 'engine-' + self.state().stripeName() + '-requestResponse'

        if noAction == True:
            self.clearActions()

        if(len(messageData) > 0 and messageData.keys()[0].find('Command') == -1):
            messageData = { tableName: messageData }
        self.expectedResults().append({
            'serviceType': 'client-request-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'table': 'RoutedMessage',
                'fields': {
                    'commandHeader': [ { 'posDupId': '{?}', 'isPosDup': '{?}', 'commandTime': '{?}', 'systemName' : '{?}' } ],
                    'sourceSystemName': inboundOmsName,
                    'destinationSystemName': '{?}', # might be missing if the request did not have a destination in mind
                    'tableId': om2CommandCatalog['tables'][tableName]['id'],
                    'messageData': messageData,
                    'messageFormat' : 'Iv',
                },
                'trace' : self.getTraceback(),
            },
        })


    def addRouteRejectFromRouter(self, omsName, dict):
        tableName = 'CommandReject';

        serviceName  = self.state().stripeName() + '->' + omsName

        self.expectedResults().append({
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': tableName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addRequestResponseCommandToEngine(self, commandName, dict):
        "this function creates a new action, and an empty expectedResult, it can not be combined with other messages into a testcase"
        tableName = 'CommandRequest'
        serviceName = 'engine-' + self.state().stripeName() + '-requestResponse'

        self.actions().append( {
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToUpstreamOms(serviceName),
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        } )

    def addRequestResponseResponseFromEngine(self, commandName, dict):
        tableName = 'CommandResponse'
        serviceName = 'engine-' + self.state().stripeName() + '-requestResponse'

        self.expectedResults().append({
            'serviceType': 'client-request-manager',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'table': commandName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageFromDatastreamServer(self, tableName, clientName, dict ):
        "this function creates an expected result, and updates the engine state"
        serviceName = self.state().stripeName() + '->' +  clientName
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromDatastreamServer(serviceName),
                'table': tableName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addInputMessageFromDatastreamServer(self, tableName, clientName, dict ):
        "this function creates a new action to send a message to a dss client"
	serviceName = self.state().stripeName() + '->' +  clientName
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromDatastreamServer(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageToInventoryManager(self, tableName, imName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->' + imName
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromInventoryManager(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageFromInventoryManager(self, tableName, imName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = imName + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToInventoryManager(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageToMasterAggregator(self, tableName, maName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->' + maName
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromInventoryManager(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageFromMasterAggregator(self, tableName, maName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = maName + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToInventoryManager(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageToAdvisor(self, tableName, advisorName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->' + advisorName
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToAdvisor(serviceName),
                'table': tableName,
                'fields': dict,
            },
            'trace' : self.getTraceback(),
        })

    def addMessageFromAdvisor(self, tableName, advisorName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = advisorName + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromAdvisor(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })


    def addInputMessageToViking(self, tableName, vikingInstance, dict, checkMessageListOrder = "false" ):
        "this function creates a new action to send a message to a dss client"
        serviceName = self.state().stripeName() + '->' +  vikingInstance
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToViking(serviceName),
                'table': tableName,
                'fields': dict,
                'checkOrder': checkMessageListOrder,
            },
        })

    def addOutputMessageFromViking(self, tableName, vikingInstance, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = vikingInstance + '->' + self.state().stripeName()
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromViking(serviceName),
                'table': tableName,
                'fields': dict,
            },
        } )

    def addExecutionNotificationMessageFromViking(self, exreInstance, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->' + exreInstance
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromViking(serviceName),
                'table': 'VikingExecutionNotification',
                'fields': dict,
            },
        } )

    def addMessageToSsr(self, tableName, ssrInstance, dict):
        "this function creates a new action, and updates the engine state"
        serviceName =  self.state().stripeName() + '->' + ssrInstance
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToSsr(serviceName),
                'table': tableName,
                'fields': dict,
            },
        } )

    def addMessageToScoop(self, tableName, scoopInstance, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = self.state().stripeName() + '->' + scoopInstance
        self.expectedResults().append( {
            'serviceType': 'client-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdToScoop(serviceName),
                'table': tableName,
                'fields': dict,
            },
        } )

    def addMessageFromScoop(self, tableName, scoopName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = scoopName + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromScoop(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageFromSsr(self, tableName, ssrName, dict):
        "this function creates a new action, and updates the engine state"
        serviceName = ssrName + '->' + self.state().stripeName()
        self.actions().append( {
            'serviceType': 'server-datastream-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': self.state().nextMessageIdFromSsr(serviceName),
                'table': tableName,
                'fields': dict,
            },
        })

    def addMessageToTibRvDaemonSrc(self, serviceName, tableName, message):
        self.expectedResults().append( {
            'serviceType': 'rv-session', 'serviceName': serviceName,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
        })

    def addSybaseIqQueryRequestResult(self, serviceName, viewName, filter, recordSets):
        "The action/expected in a single interface for sybaseIqQuery"
        self.expectedResults().append( {
            'serviceType': 'sybaseiq-query-manager', 'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'viewName': viewName,
            'message' : {
                #Default table name as we only select on view for sybaseIqQuery
                'table' : 'create-view',
                'fields' : filter,
            },
            'resultRecords' : recordSets,
            'trace' : self.getTraceback(),
        })

    def addTransactionMessages(self, skipDssForThisTransaction = False, skipOmEngineForThisTransaction = False):
        "this function adds expected results for the engine transction message and DSS if in DSS mode"
	if not self.state().waitForEveryTransactionAck():
            return

        if not skipOmEngineForThisTransaction:
            self.addMessageFromOmEngine()

        if not skipDssForThisTransaction and self.state().testDatastreamServer():
            self.addMessageFromDSS()

    def addFixMessageFromExchange(self, serviceName, table, dict):
        self.actions().append( {
            'serviceType': 'fix-line',
            'serviceName': serviceName,
            'messageName': self.state().nextMessageName(),
            'message': {
                'messageId': '',
                'table': table,
                'fields': dict,
            },
        })

    def addFixMessageToExchange(self, serviceName, tableName, messageId, matchField, message):
        self.expectedResults().append( {
            'serviceType': 'fix-line',
            'serviceName': serviceName,
            'expectedResultMatchField': matchField,
             'message': {
                'messageId': messageId,
                'table': tableName,
                'fields': message,
            },
            'trace' : self.getTraceback(),
      })
