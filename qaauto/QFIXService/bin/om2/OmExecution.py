# $Header: /home/cvs/eqtech/cep/src/testCaseOm2Utilities/OmExecution.py,v 1.2 2014/02/28 02:51:06 sawanp Exp $

from OmEngineState import OmEngineState

class OmExecution:
    "This class represents an execution. Only the OmEngineState should construct objects of this type"

    def __init__(self, engineState, dict=None):             
        "this method initializes an execution, the caller may optionally specify a dictionary of execution attributes to override the default attributes"
        self.__data = {}

        # these are the default attributes
        self['executionPrice'] = 100.00
        self['quantity'] = 100.00
        #self['executionTransactionType'] = 'New'
        if dict is not None: self.__data.update(dict) 

        self.__id = engineState.nextExecutionId()
        self.__engineState = engineState

    def id(self):
        "returns the execution's id"
        return self.__id

    def executionId(self):
        "returns the execution id"
	if self.__engineState.useVariableTags():
	    var = { 'variable': self.__id }
	    return var

        return self.__id

    def __setitem__(self, key, item):
        "a 'magic' helper function that allows the OmExecution to look like a dictionary"
        self.__data[key] = item

    def __getitem__(self, key):
        "a 'magic' helper function that allows the OmExecution to look like a dictionary"
        return self.__data.get(key, None)

    def createNewExecutionSuccessfully(self, testName, order):
        "this function creates the message to create a new execution, the expected result, and updates the engine state"
	# change the apollo sequence number, a successful new execution will cause a message to be sent to apollo
        self.__engineState.nextMessageIdToApollo += 1
        self.__engineState.nextMessageIdFromViking += 1

	# these fields are "mandatory" in a viking execution
	premiseFields = {
            'commandHeader': {
                'fields': [
                    {
                        'posDupId': 'CLNT' + str(self.id()),
                    }
                ],
            },
        }

        premiseFields['orderId'] = { 'valueFromOtherMessagesField' : { 'columnName' : 'orderId', 'messageName': 'new order ' + str(order.id()) + ' 2'  } }
        
	# set the fields that are "optional" in a viking execution
        if self['quantity'] is not None: premiseFields['quantity'] = self['quantity']
        if self['buySell'] is not None: premiseFields['buySell'] = self['buySell']
        if self['eventType'] is not None: premiseFields['eventType'] = self['eventType']
        if self['executionPrice'] is not None: premiseFields['executionPrice'] = self['executionPrice']
        if self['productId'] is not None: premiseFields['productId'] = self['productId']
        if self['productIdType'] is not None: premiseFields['productIdType'] = self['productIdType']
        if self['settlementCurrency'] is not None: premiseFields['settlementCurrency'] = self['settlementCurrency']
        if self['settlementDateCalcMethod'] is not None: premiseFields['settlementDateCalcMethod'] = self['settlementDateCalcMethod']
        if self['updateTimestamp'] is not None: premiseFields['updateTimestamp'] = self['updateTimestamp']
        if self['exchangeExecutionId'] is not None: premiseFields['exchangeExecutionId'] = self['exchangeExecutionId']
        if self['settlementDate'] is not None: premiseFields['settlementDate'] = self['settlementDate']
        if self['executionTime'] is not None: premiseFields['executionTime'] = self['executionTime']
        if self['exchangeOrderId'] is not None: premiseFields['exchangeOrderId'] = self['exchangeOrderId']

        conclusionFields = {}
        
        conclusionFields['orderId'] = '{*}'
        conclusionFields['eventTime'] = '{*}'
        conclusionFields['execId'] = '{*}'

	# set the fields that are "optional" in an ApolloOrderStatus object
        if self['buySell'] is not None: conclusionFields['buySell'] = self['buySell']
        if self['orderQuantity'] is not None: conclusionFields['quantity'] = self['orderQuantity']
        if self['orderType'] is not None: conclusionFields['orderType'] = self['orderType']
        if self['timeInForce'] is not None: conclusionFields['timeInForce'] = self['timeInForce']
        if self['limitPrice'] is not None: conclusionFields['limitPrice'] = self['limitPrice']
        if self['notHeld'] is not None: conclusionFields['notHeld'] = self['notHeld']
        if self['maxTrancheSize'] is not None: conclusionFields['maxTrancheSize'] = self['maxTrancheSize']
        if self['requestedCapacity'] is not None: conclusionFields['requestedCapacity'] = self['requestedCapacity']
        if self['productIdType'] is not None: conclusionFields['productIdType'] = self['productIdType']
        if self['productId'] is not None: conclusionFields['productId'] = self['productId']
        if self['stopPrice'] is not None: conclusionFields['stopPrice'] = self['stopPrice']
        if self['settlementType'] is not None: conclusionFields['settlementType'] = self['settlementType']
        if self['projectedSettlementDate'] is not None: conclusionFields['projectedSettlementDate'] = self['projectedSettlementDate']
        if self['expirationDateTime'] is not None: conclusionFields['expirationDateTime'] = self['expirationDateTime']
        if self['sellShort'] is not None: conclusionFields['sellShort'] = self['sellShort']
        if self['sellShortExempt'] is not None: conclusionFields['sellShortExempt'] = self['sellShortExempt']
        if self['positionOpenClose'] is not None: conclusionFields['positionOpenClose'] = self['positionOpenClose']
        if self['comments'] is not None: conclusionFields['comments'] = self['comments']
        if self['clientConsents'] is not None: conclusionFields['clientConsents'] = self['clientConsents']
        if self['allOrNone'] is not None: conclusionFields['allOrNone'] = self['allOrNone']
        if self['useExternalReferenceTable'] is not None: conclusionFields['useExternalReferenceTable'] = self['useExternalReferenceTable']
        if self['externalReferences'] is not None: conclusionFields['externalReferences'] = self['externalReferences']
        if self['executedQuantity'] is not None: conclusionFields['executedQuantity'] = self['executedQuantity']
        if self['quantityRemaining'] is not None: conclusionFields['quantityRemaining'] = self['quantityRemaining']
        if self['averagePrice'] is not None: conclusionFields['averagePrice'] = self['averagePrice']
        if self['averagePriceInExecutionCurrency'] is not None: conclusionFields['averagePriceInExecutionCurrency'] = self['averagePriceInExecutionCurrency']
        if self['averageNetPrice'] is not None: conclusionFields['averageNetPrice'] = self['averageNetPrice']
        if self['eventTime'] is not None: conclusionFields['eventTime'] = self['eventTime']
        if self['validationResultsList'] is not None: conclusionFields['validationResultsList'] = self['validationResultsList']
        if self['execId'] is not None: conclusionFields['execId'] = self['execId']
        if self['executionQuantity'] is not None: conclusionFields['executionQuantity'] = self['executionQuantity']
        if self['executionPrice'] is not None: conclusionFields['executionPrice'] = self['executionPrice']
        if self['executionNetPrice'] is not None: conclusionFields['executionNetPrice'] = self['executionNetPrice']
        if self['settlementPrice'] is not None: conclusionFields['settlementPrice'] = self['settlementPrice']
        if self['settlementNetPrice'] is not None: conclusionFields['settlementNetPrice'] = self['settlementNetPrice']
        if self['executionTime'] is not None: conclusionFields['executionTime'] = self['executionTime']
        if self['executionFlags'] is not None: conclusionFields['executionFlags'] = self['executionFlags']
        if self['executionCapacity'] is not None: conclusionFields['executionCapacity'] = self['executionCapacity']
        if self['executionPoint'] is not None: conclusionFields['executionPoint'] = self['executionPoint']
        if self['subExecutionPoint'] is not None: conclusionFields['subExecutionPoint'] = self['subExecutionPoint']
        if self['fixOrderStatus'] is not None: conclusionFields['fixOrderStatus'] = self['fixOrderStatus']
        if self['originalFixMessage'] is not None: conclusionFields['originalFixMessage'] = self['originalFixMessage']
        if self['oldExternalReferences'] is not None: conclusionFields['oldExternalReferences'] = self['oldExternalReferences']
        if self['fixLineId'] is not None: conclusionFields['fixLineId'] = self['fixLineId']
        if self['fixExecutionId'] is not None: conclusionFields['fixExecutionId'] = self['fixExecutionId']
        if self['oldFixExecutionId'] is not None: conclusionFields['oldFixExecutionId'] = self['oldFixExecutionId']
        if self['executionTransactionType'] is not None: conclusionFields['executionTransactionType'] = self['executionTransactionType']

        return {
            'testName': testName + ' new execution ' + str(self.id()),
            'dependencyTestCaseNames': [ testName + ': new order ' + str(order.id()) ],
            'actions': [
                {
                    'serviceType': 'server-datastream-manager',
                    'serviceName': 'LNSE->' + self.__engineState.instance,
                    'messageName': 'new execution ' + str(self.id()) + ' 1' ,
                    'message': {
                        'table': 'VikingExecution',
                        'fields': premiseFields,
                        'messageId': self.__engineState.nextMessageIdFromViking,
                    },
                },
            ],
            'expectedResults': [
                {
                    'serviceType': 'client-datastream-manager', 'serviceName': self.__engineState.instance + '->' + 'apollo',
                    'messageName': 'new execution ' + str(self.id()) + ' 2' ,
                    'message': {
                        'messageId': self.__engineState.nextMessageIdToApollo,
                        'table': 'ApolloOrderStatus',
                        'fields': conclusionFields,
                    },
                },
            ],
        }

