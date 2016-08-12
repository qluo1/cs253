""" hermes config for the om engine """

import os


def populateSORDesitnationCommands(cmds):
    cmds['SORDisableDestination'] = {
        'handler': 'SORDisableDestination',
        'arguments': {
            'destination': [ ' ', ],
        }
    }
    cmds['SOREnableDestination'] = {
        'handler': 'SOREnableDestination',
        'arguments': {
            'destination': [ ' ', ],
        }
    }

def addHermesCommandsForSRI(commands):
    """add SRI specific hermes commands"""
    commands['GetHeldTillReconnectStatus'] = {
        'handler': 'GetHeldTillReconnectStatus',
        'arguments': { 'NA': ['NA'] },
    }
    commands['ListHeldTillReconnectOrders'] = {
        'handler': 'ListHeldTillReconnectOrders',
        'arguments': { 'NA': ['NA'] },
    }
    commands['DisableHeldTillReconnect'] = {
        'handler': 'DisableHeldTillReconnect',
        'arguments': { 'NA': ['NA'] },
    }
    commands['EnableHeldTillReconnect'] = {
        'handler': 'EnableHeldTillReconnect',
        'arguments': { 'NA': ['NA'] },
    }

def getCommands():
    """return all supported om2 hermes commands for the current engine instance"""
    commands = {}

    commands['purge-executions'] = {
        'handler': 'purge-executions',
	'arguments': {' ': ['NA']},
    }
    commands['purge-execution-by-id'] = {
        'handler': 'purge-execution-by-id',
	'arguments': {' ': ['NA']},
    }
    commands['purge-baskets'] = {
        'handler': 'purge-baskets',
	'arguments': {' ': ['NA']},
    }
    commands['purge-orders-by-pattern'] = {
        'handler': 'purge-orders-by-pattern',
        'arguments': {' ': ['NA']},
    }
    commands['forceStartBatch'] = {
        'handler': 'forceStartBatch',
        'arguments': {'batchName': [' ']},
    }
    commands['deleteBatch'] = {
        'handler': 'deleteBatch',
        'arguments': {'batchName': [' ']},
    }
    commands['takeBatchOffHold'] = {
        'handler': 'takeBatchOffHold',
        'arguments': {'batchName': [' ']},
    }
    commands['putBatchOnHold'] = {
        'handler': 'putBatchOnHold',
        'arguments': {'batchName': [' ']},
    }
    commands['getQueuedOrderStatus'] = {
        'handler': 'getQueuedOrderStatus',
        'arguments': {' ': ['NA']},
    }
    commands['flushQueuedOrders'] = {
        'handler': 'flushQueuedOrders',
        'arguments': {'feedName': [' ']},
    }
    commands['enableOrderQueue'] = {
        'handler': 'enableOrderQueue',
        'arguments': {'feedName': [' ']},
    }
    commands['disableOrderQueue'] = {
        'handler': 'disableOrderQueue',
        'arguments': {'feedName': [' ']},
    }
    commands['querySingleSymbolAggUnitPair'] = {
        'handler': 'querySingleSymbolAggUnitPair',
        'arguments': {'symbol': [' ']},
    }
    commands['querySingleCreditUsage'] = {
        'handler': 'querySingleCreditUsage',
        'arguments': {'symbol': [' ']},
    }
    commands['refreshSingleSymbolAggUnitPair'] = {
        'handler': 'refreshSingleSymbolAggUnitPair',
        'arguments': {'symbol': [' ']},
    }
    commands['refreshAggUnitSymbolPairsFromFile'] = {
        'handler': 'refreshAggUnitSymbolPairsFromFile',
        'arguments': {'file': [' ']},
    }
    commands['refreshSingleCreditUsage'] = {
        'handler': 'refreshSingleCreditUsage',
        'arguments': {'symbol': [' ']},
    }
    commands['refresh'] = {
        'handler': 'refresh',
        'arguments': {'dataStore': [' ']},
    }
    commands['setFeedPreference' ] = {
        'handler' : 'setFeedPreference',
        'arguments': {
            'feedName': [ ' ', ],
            'preference': [ ' ', ],
            'executionPoint': [ ' ', ],
        }
    }
    commands['setFeedPreferenceForSymbol'] = {
        'handler' : 'setFeedPreferenceForSymbol',
        'arguments' : {
            'feedName' : [ ' ' ],
            'preference' : [ ' ' ],
            'symbol' : [ ' ' ],
            'executionPoint' : [ ' ' ]
        }
    }
    commands['setReferenceVenue'] = {
        'handler' : 'setReferenceVenue',
        'arguments': {
            'primaryMarket': [ ' ', ],
            'referenceVenue': [ ' ', ],
        }
    }
    commands['printMarketData' ] = {
        'handler' : 'printMarketData',
        'arguments': {
            'symbol': [ ' ', ],
        }
    }
    commands['printMarketDataSymbolsInState'] = {
        'handler' : 'printMarketDataSymbolsInState',
        'arguments' : {
            'state' : [ ' ' ]
        }
    }
    commands['printSymbolMappingRules'] = {
        'handler' : 'printSymbolMappingRules',
        'arguments' : { }
    }
    commands['enableL2SymbolMapping'] = {
        'handler' : 'enableL2SymbolMapping',
        'arguments' : {
            'symbol' : [ ' ' ],
            'executionPoint' : [ ' ' ],
            'productType' : [ ' ' ],
            'segment' : [ ' ' ]
        }
    }
    commands['disableL2SymbolMapping'] = {
        'handler' : 'enableL2SymbolMapping',
        'arguments' : {
            'symbol' : [ ' ' ],
            'executionPoint' : [ ' ' ],
            'productType' : [ ' ' ],
            'segment' : [ ' ' ]
        }
    }
    commands['resubscribeMarketData'] = {
        'handler' : 'resubscribeMarketData',
        'arguments' : {
            'symbol' : [ ' ' ]
        }
    }
    commands['resubscribeAggregateData'] = {
        'handler' : 'resubscribeAggregateData',
        'arguments' : {
            'aggregationId' : [ ' ' ]
        }
    }
    commands['resubscribeAllMarketData'] = {
        'handler' : 'resubscribeAllMarketData',
        'arguments' : { }
    }
    commands['resubscribeAllAggregateData'] = {
        'handler' : 'resubscribeAllAggregateData',
        'arguments' : { }
    }
    commands['unsubscribeMarketData' ] = {
        'handler' : 'unsubscribeMarketData',
        'arguments': {
            'all': [ ' ', ],
            'symbol': [ ' ', ],
        }
    }
    commands['unsubscribeImbalanceData' ] = {
        'handler' : 'unsubscribeImbalanceData',
        'arguments': {
            'all': [ ' ', ],
            'symbol': [ ' ', ],
        }
    }
    commands['unsubscribePositionData' ] = {
        'handler' : 'unsubscribePositionData',
        'arguments': {
            'all': [ ' ', ],
            'symbol': [ ' ', ],
        }
    }
    commands['unsubscribeCreditUsageData' ] = {
        'handler' : 'unsubscribeCreditUsageData',
        'arguments': {
            'all': [ ' ', ],
            'symbol': [ ' ', ],
        }
    }
    commands['unsubscribeLiquidityQuoteData' ] = {
        'handler' : 'unsubscribeLiquidityQuoteData',
        'arguments': {
            'all': [ ' ', ],
            'symbol': [ ' ', ],
        }
    }
    commands['unsubscribeAggregateData' ] = {
        'handler' : 'unsubscribeAggregateData',
        'arguments': {
            'all': [ ' ', ],
            'aggregationId': [ ' ', ],
        }
    }
    commands['addReutersQuoteConditionCode' ] = {
        'handler' : 'addReutersQuoteConditionCode',
        'arguments': {
            'market': [ ' ', ],
            'reutersCode': [ ' ', ],
            'quoteCondition': [ ' ', ],
        }
    }
    commands['removeReutersQuoteConditionCode' ] = {
        'handler' : 'removeReutersQuoteConditionCode',
        'arguments': {
            'market': [ ' ', ],
            'reutersCode': [ ' ', ],
        }
    }
    commands['enableQuoteConditionUsage'] = {
        'handler': 'enableQuoteConditionUsage',
        'arguments': {
            'executionPoint': [ ' ', ],
        }
    }
    commands['disableQuoteConditionUsage'] = {
        'handler': 'disableQuoteConditionUsage',
        'arguments': {
            'executionPoint': [ ' ', ],
        }
    }
    commands['getMarketData'] = {
            'handler' : 'getMarketData',
            'arguments': {
                'symbol': [ ' ', ],
            }
    }
    commands['getMarketDataSymbol'] = {
            'handler' : 'getMarketDataSymbol',
            'arguments': {
                'symbol': [ ' ', ],
                'productIdType': [ ' ', ],
            }
    }

    commands['reloadT2XmlFile'] = {
            'handler' : 'reloadT2XmlFile',
            'arguments': {
                'fileName': [ ' ', ],
                'ruleBase': [ ' ', ],
            }
    }
    commands['printT2XmlToFile'] = {
            'handler' : 'printT2XmlToFile',
            'arguments': {
                'filePath': [ ' ', ],
            }
    }
    commands['overrideT2RulesData'] = {
            'handler' : 'overrideT2RulesData',
            'arguments': {
                'rulesToUpdate': ['t2TimeRules', 'blockSymbolRange', 'blockSymbolRangeAndExchange'],
            }
    }
    commands['enableTsor'] = {
            'handler' : 'enableTsor',
            'arguments': {
                'country': ['CA', 'NONCA', 'ALL'],
            }
    }
    commands['disableTsor'] = {
            'handler' : 'disableTsor',
            'arguments': {
                'country': ['CA', 'NONCA', 'ALL'],
            }
    }
    commands['enableCrossChecker'] = {
            'handler' : 'enableCrossChecker',
    }
    commands['disableCrossChecker'] = {
            'handler' : 'disableCrossChecker',
    }
    commands['ControlToggleExecSessionQCSource'] = {
            'handler': 'ControlToggleExecSessionQuoteConditionSource',
            'arguments': { 'source': [ ' ', ],
        }
    }
    commands['ControlExcludeVenueFromConsolidatedBook'] = {
            'handler': 'ControlExcludeVenueFromConsolidatedBook',
            'arguments': { 'venue': [ ' ', ],
        }
    }
    commands['ControlReIncludeVenueInConsolidatedBook'] = {
            'handler': 'ControlReIncludeVenueInConsolidatedBook',
            'arguments': { 'venue': [ ' ', ],
        }
    }

    #
    #   Add QA/Dev environment specific commands that has to be disabled in prod
    #
    instanceEnv = os.getenv('instanceEnv')
    if (instanceEnv == None or instanceEnv.lower() != 'prod'):
        commands['changeImbalanceData'] = {
            'handler': 'changeImbalanceData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['startOverridingMarketData'] = {
            'handler': 'startOverridingMarketData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setMarketData'] = {
            'handler': 'setMarketData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setImbalanceData'] = {
            'handler': 'setImbalanceData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setPositionData'] = {
            'handler': 'setPositionData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setCreditUsageData'] = {
            'handler': 'setCreditUsageData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setLiquidityQuoteData'] = {
            'handler': 'setLiquidityQuoteData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setAggregateData'] = {
            'handler': 'setAggregateData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['stopOverridingMarketData'] = {
            'handler': 'stopOverridingMarketData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['startOverridingAggregatePositionData'] = {
            'handler': 'startOverridingAggregatePositionData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['setAggregatePositionData'] = {
            'handler': 'setAggregatePositionData',
            'arguments': { 'NA': ['NA'] },
        }
        commands['stopOverridingAggregatePositionData'] = {
            'handler': 'stopOverridingAggregatePositionData',
            'arguments': { 'NA': ['NA'] },
        }
        # Only required for simulator testing the SOR
        commands['SOREnableMTFPosting'] = {
            'handler': 'SOREnableMTFPosting',
            'arguments': {
                'gameplan': [ ' ', ],
                'market': [ ' ', ],
            }
        }
        commands['printT2XmlSchemaToFile'] = {
            'handler': 'printT2XmlSchemaToFile',
            'arguments': { ' ': [' ', ] },
        }
        commands['isMarketDataOverridden'] = {
            'handler' : 'isMarketDataOverridden',
            'arguments': { 'NA': ['NA'] },
        }
        commands['seedRandomNumber'] = {
            'handler': 'seedRandomNumber',
            'arguments': { 'NA': ['NA'] },
        }

        commands['clearAllOrderBlocks'] = {
            'handler' : 'clearAllOrderBlocks',
            'arguments': {' ': ['NA']},
        }

        commands['clearAllOrderBlocksForTradingUnitId'] = {
            'handler' : 'clearAllOrderBlocksForTradingUnitId',
            'arguments': {'tradingUnitId': [' ']},
            }

        commands['setOrderBlockForTradingUnitId'] = {
            'handler' : 'setOrderBlockForTradingUnitId',
            'arguments': {
                'tradingUnitId': [' '],
                'action' : ['suspend', 'reject'],
                }
            }

        commands['setOrderBlockForPrimaryPartyType'] = {
            'handler' : 'setOrderBlockForPrimaryPartyType',
            'arguments': {
                'primaryPartyType': ['Firm'],
                'productInstrumentType' : ['Equity', 'Option'],
                'action' : ['suspend', 'reject'],
                }
            }

        commands['clearAllOrderBlocksForPrimaryPartyType'] = {
            'handler' : 'clearAllOrderBlocksForPrimaryPartyType',
            'arguments': {
                'primaryPartyType': ['Firm'],
                'productInstrumentType' : ['Equity', 'Option'],
                }
            }

    #
    #   Add commands that are specific to om2engine that has SigmaOrderRouter embedded in it.
    #
    smartRouter = os.getenv('smartRouter')
    sigmaEnabled = os.getenv('SIGMA_ENABLED')
    if ( (smartRouter != None and smartRouter == 'SigmaOrderRouter') or (sigmaEnabled != None and sigmaEnabled.lower() == 'true') ):

        populateSORDesitnationCommands(commands)

        commands['SORDisableGamePlan'] = {
            'handler': 'SORDisableGamePlan',
            'arguments': {
                'gameplan': [ ' ', ],
                'market': [ ' ', ],
            },
        }
        commands['SOREnableGamePlan'] = {
            'handler': 'SOREnableGamePlan',
            'arguments': {
                'gameplan': [ ' ', ],
                'market': [ ' ', ],
            },
        }

        commands['SORAuctionRebalance'] = {
           'handler': 'SORAuctionRebalance',
            'arguments': { 'market': [ ' ', ], },
        }
        commands['SORStopAuctionRebalance'] = {
           'handler': 'SORStopAuctionRebalance',
            'arguments': { 'market': [ ' ', ], },
        }
        commands['SORClearSOROrderCache'] = {
           'handler': 'SORClearSOROrderCache',
            'arguments': {' ': ['NA'] },
        }
        commands['SORMTFRebalance'] = {
           'handler': 'SORMTFRebalance',
            'arguments': {
                'market': [ ' ', ],
            }
        }
        commands['SOREnableVenueQuote'] = {
           'handler': 'SOREnableVenueQuote',
            'arguments': { 'venue': [ ' ' ], },
        }
        commands['SORDisableVenueQuote'] = {
           'handler': 'SORDisableVenueQuote',
            'arguments': { 'venue': [ ' ' ], },
        }
        commands['SOREnableSymbolVenueQuote'] = {
           'handler': 'SOREnableSymbolVenueQuote',
            'arguments': {
                'symbol': [ ' ', ],
                'venue': [ ' ', ],
            }
        }
        commands['SORDisableSymbolVenueQuote'] = {
           'handler': 'SORDisableSymbolVenueQuote',
            'arguments': {
                'symbol': [ ' ', ],
                'venue': [ ' ', ],
            }
        }
        commands['SORRefreshPlacementConfig'] = {
           'handler': 'SORRefreshPlacementConfig',
            'arguments': { 'source': [' '] },
        }
        commands['SORDisableAmends'] = {
            'handler': 'SORDisableAmends',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SOREnableAmends'] = {
            'handler': 'SOREnableAmends',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORDisableMTFRebalance'] = {
            'handler': 'SORDisableMTFRebalance',
            'arguments': { 'market': [ ' ' ], },
        }
        commands['SOREnableMTFRebalance'] = {
            'handler': 'SOREnableMTFRebalance',
            'arguments': { 'market': [ ' ' ], },
        }
        commands['SORDisableAuctionRebalance'] = {
            'handler': 'SORDisableAuctionRebalance',
            'arguments': { 'market': [ ' ' ], },
        }
        commands['SOREnableAuctionRebalance'] = {
            'handler': 'SOREnableAuctionRebalance',
            'arguments': { 'market': [ ' ' ], },
        }
        commands['SORStartOffPrimaryTrading'] = {
            'handler': 'SORStartOffPrimaryTrading',
            'arguments': {
                'primaryMarket': [ ' ' ],
                'referenceVenue': [ ' ' ],
            },
        }
        commands['SORStopOffPrimaryTrading'] = {
            'handler': 'SORStopOffPrimaryTrading',
            'arguments': {
                'primaryMarket': [ ' ' ],
            },
        }
        commands['SOROpeningRebalance'] = {
           'handler': 'SOROpeningRebalance',
            'arguments': {
                'market': [ ' ', ],
            }
        }
        commands['SORToggleSweepOnAmend'] = {
           'handler': 'SORToggleSweepOnAmend',
            'arguments': {
                'gameplan': [ 'SORPassivePlacement', 'SORIceberg' ],
                'value': [ 'true', 'false' ],
            }
        }
        commands['SOROverrideVenueScores'] = {
           'handler': 'SOROverrideVenueScores',
            'arguments': {
                'symbol': [ ' ', ],
                'slotNumber': [ ' ', ],
                'side': [ ' ', ],
                'venueScore': [ ' ', ],
            },
        }
        commands['SORDisablePlacementPlanTimers'] = {
            'handler': 'SORDisablePlacementPlanTimers',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SOREnablePlacementPlanTimers'] = {
            'handler': 'SOREnablePlacementPlanTimers',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORDisableAutoRefresh'] = {
            'handler': 'SORDisableAutoRefresh',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SOREnableAutoRefresh'] = {
            'handler': 'SOREnableAutoRefresh',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORDisableQuoteAccounting'] = {
            'handler': 'SORDisableQuoteAccounting',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SOREnableQuoteAccounting'] = {
            'handler': 'SOREnableQuoteAccounting',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORSetAdvisorErrorCount'] = { #Command to Set the Error count for advisor interface
            'handler': 'SORSetAdvisorErrorCount',
            'arguments': { 'NA': [ 'NA' ] },
        }
        commands['SORGetHeldTillReconnectStatus'] = {
            'handler': 'SORGetHeldTillReconnectStatus',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORGetHeldOrdersList'] = {
            'handler': 'SORGetHeldOrdersList',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORReleaseHeldOrders'] = {
            'handler': 'SORReleaseHeldOrders',
            'arguments': { 'destinations': [ '' ], },
        }
        commands['SORDisableHeldTillReconnect'] = {
            'handler': 'SORDisableHeldTillReconnect',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SOREnableHeldTillReconnect'] = {
            'handler': 'SOREnableHeldTillReconnect',
            'arguments': { 'NA': ['NA'] },
        }
        commands['SORDisableAdvisorRequest'] = { #Command to Disable Advisor Requests from gameplan
            'handler': 'SORDisableAdvisorRequest',
            'arguments': { 'NA': [ 'NA' ] },
        }
        commands['SOREnableAdvisorRequest'] = { #Command to Enable Advisor Requests from gameplan
            'handler': 'SOREnableAdvisorRequest',
            'arguments': { 'NA': [ 'NA' ] },
        }
        commands['SOROpeningAuctionRebalance'] = {
            'handler': 'SOROpeningAuctionRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SORDisableOpeningAuctionRebalance'] = {
            'handler': 'SORDisableOpeningAuctionRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SOREnableOpeningAuctionRebalance'] = {
            'handler': 'SOREnableOpeningAuctionRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SOROpeningAuctionCancelRebalance'] = {
            'handler': 'SOROpeningAuctionCancelRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SORDisableOpeningAuctionCancelRebalance'] = {
            'handler': 'SORDisableOpeningAuctionCancelRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SOREnableOpeningAuctionCancelRebalance'] = {
            'handler': 'SOREnableOpeningAuctionCancelRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SORClosingAuctionRebalance'] = {
            'handler': 'SORClosingAuctionRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SORDisableClosingAuctionRebalance'] = {
            'handler': 'SORDisableClosingAuctionRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SOREnableClosingAuctionRebalance'] = {
            'handler': 'SOREnableClosingAuctionRebalance',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SORResetAuctionFired'] = {
            'handler': 'SORResetAuctionFired',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
                'auction': [ ' ' ],
            },
        }
        commands['SORDisableOpeningAuctionAutoPull'] = {
            'handler': 'SORDisableOpeningAuctionAutoPull',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }
        commands['SOREnableOpeningAuctionAutoPull'] = {
            'handler': 'SOREnableOpeningAuctionAutoPull',
            'arguments': {
                'market': [ ' ' ],
                'segment': [ ' ' ],
            },
        }

    #
    #   Add commands that are specific to x3 matching engines.
    #
    isMatchingEngine = os.getenv('isMatchingEngine')
    if isMatchingEngine and isMatchingEngine == 'true':
        commands['X3Suspend'] = {
            'handler': 'X3Suspend',
            'arguments': {' ': ['NA']},
        }
        commands['X3Unsuspend'] = {
            'handler': 'X3Unsuspend',
            'arguments': {' ': ['NA']},
        }
        commands['X3Halt'] = {
            'handler': 'X3Halt',
            'arguments': {' ': ['NA']},
        }
        commands['X3Unhalt'] = {
            'handler': 'X3Unhalt',
            'arguments': {' ': ['NA']},
        }
        commands['X3Preopen'] = {
            'handler' : 'X3Preopen',
            'arguments': {' ': ['NA']},
        }
        commands['X3SuspendSymbol'] = {
            'handler': 'X3SuspendSymbol',
            'arguments': {
                'symbol': [ ' ', ],
            },
        }
        commands['X3UnsuspendSymbol'] = {
            'handler': 'X3UnsuspendSymbol',
            'arguments': {
                'symbol': [ ' ', ],
            },
        }
        commands['X3HaltSymbol'] = {
            'handler': 'X3HaltSymbol',
            'arguments': {
                'symbol': [ ' ', ],
            },
        }
        commands['X3UnhaltSymbol'] = {
            'handler': 'X3UnhaltSymbol',
            'arguments': {
                'symbol': [ ' ', ],
            },
        }
        commands['X3HaltUser'] = {
            'handler' : 'X3HaltUser',
            'arguments' : {
                'tradingUnitId' : [ ' ' ]
            }
        }
        commands['X3UnhaltUser'] = {
            'handler' : 'X3UnhaltUser',
            'arguments' : {
                'tradingUnitId' : [ ' ' ]
            }
        }
        commands['X3SuspendUser'] = {
            'handler' : 'X3SuspendUser',
            'arguments' : {
                'tradingUnitId' : [ ' ' ]
            }
        }
        commands['X3UnsuspendUser'] = {
            'handler' : 'X3UnsuspendUser',
            'arguments' : {
                'tradingUnitId' : [ ' ' ]
            }
        }
        commands['reloadConfiguration'] = {
            'handler' : 'reloadConfiguration',
            'arguments' : {
            }
        }

    useExtendedMatchingEngineHermesCommands = os.getenv('useExtendedMatchingEngineHermesCommands')
    if useExtendedMatchingEngineHermesCommands and useExtendedMatchingEngineHermesCommands == 'true':
        commands['X3SuspendExchange'] = {
            'handler': 'X3SuspendExchange',
            'arguments': {
                'exchange': [ ' ', ],
            },
        }
        commands['X3UnsuspendExchange'] = {
            'handler': 'X3UnsuspendExchange',
            'arguments': {
                'exchange': [ ' ', ],
            },
        }
        commands['X3HaltExchange'] = {
            'handler': 'X3HaltExchange',
            'arguments': {
                'exchange': [ ' ', ],
            },
        }
        commands['X3UnhaltExchange'] = {
            'handler': 'X3UnhaltExchange',
            'arguments': {
                'exchange': [ ' ', ],
            },
        }
        commands['X3CloseSymbol'] = {
            'handler': 'X3CloseSymbol',
            'arguments': {
                'symbol': [ ' ', ],
            },
        }
        commands['X3Close'] = {
            'handler': 'X3Close',
            'arguments': {
            },
        }
        commands['X3CloseExchange'] = {
            'handler': 'X3CloseExchange',
            'arguments': {
                'exchange': [ ' ', ],
            },
        }
        commands['X3OpenSymbol'] = {
            'handler': 'X3OpenSymbol',
            'arguments': {
                'symbol': [ ' ', ],
            },
        }
        commands['X3Open'] = {
            'handler': 'X3Open',
            'arguments': {
            },
        }
        commands['X3OpenExchange'] = {
            'handler': 'X3OpenExchange',
            'arguments': {
                'exchange': [ ' ', ],
            },
        }
        commands['X3CancelOrder'] = {
            'handler': 'X3CancelOrder',
            'arguments': {
                'orderId': [ ' ', ],
            },
        }
        commands['X3CancelTrader'] = {
            'handler': 'X3CancelTrader',
            'arguments': {
                'traderId': [ ' ', ],
            },
        }
        commands['X3CancelClient'] = {
            'handler': 'X3CancelClient',
            'arguments': {
                'clientId': [ ' ', ],
            },
        }
        commands['X3DisableTiering'] = {
            'handler' : 'X3DisableTiering',
            'arguments': {' ': ['NA']},
        }
        commands['X3EnableTiering'] = {
            'handler' : 'X3EnableTiering',
            'arguments': {' ': ['NA']},
        }
        commands['X3DisableTieringParameters'] = {
            'handler' : 'X3DisableTieringParameters',
            'arguments': {' ': ['NA']},
        }
        commands['X3EnableTieringParameters'] = {
            'handler' : 'X3EnableTieringParameters',
            'arguments': {' ': ['NA']},
        }
        # These were in the previous om2/matchingEngine/herkes/hermes.py file, so they were left here.
        populateSORDesitnationCommands(commands)

    # Add command that is specific to LiquidityQuoteMatching
    enableLiquidityQuoteMatching = os.getenv('enableLiquidityQuoteMatching', 'false')
    if enableLiquidityQuoteMatching.lower() == 'true':
	commands['X3InitializeLiquidityQuoteListeners'] = {
            'handler' : 'X3InitializeLiquidityQuoteListeners',
            'arguments': {' ': ['NA']},
        }

    hasFixInterface = os.getenv('fixEngineInterface')
    if hasFixInterface:
        commands['getFixSessionStatus'] = {
            'handler': 'getFixSessionStatus',
            'arguments': {
                'sessionName': [ ' ', ],
            },
        }

        commands['setFixSessionSequenceNumbers'] = {
            'handler': 'setFixSessionSequenceNumbers',
            'arguments': {
                'sessionName': [ ' ', ],
                'lastIn': [ ' ', ],
                'lastOut': [ ' ', ],
            },
        }

        commands['setFixSessionOnHold'] = {
            'handler': 'setFixSessionOnHold',
            'arguments': {
                'sessionName': [ ' ', ],
                'onHold': [ 'true', 'false'],
            },
        }

    addHermesCommandsForSRI(commands)

    return commands
