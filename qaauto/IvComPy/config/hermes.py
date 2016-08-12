import os;

def getCommands():
    commands = { 
        'ls' : {
            'handler': 'ls',
            'baseDirectory': '',
            'arguments': { 
                ' ': [ 'aa', 'bb', 'cc', 'dd', ], 
                '-l': [ 'a', 'b', 'c', 'd', ], 
                '-a': [ 'NA' ],
                '-r': [ 'NA' ],
                '-t': [ 'NA' ], 
            }
        },
        'pwd' : {
            'handler': 'pwd',
            'arguments': { 'NA': ['NA'] },
        },
        'myscript.sh': {
            'handler': 'myscript.sh',
            'baseDirectory': os.getenv('HOME'),
            'arguments': { 'NA': ['NA'] },
        },
        'sleep': {
            'handler': 'sleep',
            'arguments': { ' ': ['2','3','4','5','6','7',] },
        },
        'helloWorld': {
            'handler': 'helloWorld',
            'arguments': {
                ' ': [ 'hi', 'bye', ],
            }
        },
        'startOverridingTheTime': {
            'handler': 'startOverridingTheTime',
            'arguments': { 'NA': ['NA'] },
        },
        'stopOverridingTheTime': {
            'handler': 'stopOverridingTheTime',
            'arguments': { 'NA': ['NA'] },
        },
        'startOverridingMarketData': {
            'handler': 'startOverridingMarketData',
            'arguments': { 'NA': ['NA'] },
        },
        'stopOverridingMarketData': {
            'handler': 'stopOverridingMarketData',
            'arguments': { 'NA': ['NA'] },
        },
        'setMarketData': {
            'handler': 'setMarketData',
            'arguments': { 'NA': ['NA'] },
        },
        'listLocks': {
            'handler': 'listLocks',
            'arguments': { 'NA': ['NA'] },
        },
        'queryLocks': {
            'handler': 'queryLocks',
            'arguments': { 'NA': ['NA'] },
        },
        'clearLocks': {
            'handler': 'clearLocks',
            'arguments': { 'NA': ['NA'] },
        },
        'removeLock': {
            'handler': 'removeLock',
            'arguments': { 'NA': ['NA'] },
        },
        'enableAutoFailover': {
            'handler': 'enableAutoFailover',
            'arguments': { 'NA': ['NA'] },
        },
        'disableAutoFailover': {
            'handler': 'disableAutoFailover',
            'arguments': { 'NA': ['NA'] },
        },
        'becomeActive': {
            'handler': 'becomeActive',
            'arguments': { 'NA': ['NA'] },
        },
        'becomeBackup': {
            'handler': 'becomeBackup',
            'arguments': { 'NA': ['NA'] },
        },
        'SOREnableDestination' : {
            'handler': 'SOREnableDestination',
            'arguments': { 
                'destination': [ ' ', ], 
            }    
        },
        'SORDisableDestination' : {
            'handler': 'SORDisableDestination',
            'arguments': { 
                'destination': [ ' ', ], 
            }    
        },
        'SOREnableVenueQuote' : {
            'handler': 'SOREnableVenueQuote',
            'arguments': { 
                'venue': [ ' ', ], 
            }    
        },
        'SORDisableVenueQuote' : {
            'handler': 'SORDisableVenueQuote',
            'arguments': { 
                'venue': [ ' ', ], 
            }    
        },
        'SOREnableSymbolVenueQuote' : {
            'handler': 'SOREnableSymbolVenueQuote',
            'arguments': { 
                'symbol': [ ' ', ], 
                'venue': [ ' ', ], 
            }    
        },
        'SORDisableSymbolVenueQuote' : {
            'handler': 'SORDisableSymbolVenueQuote',
            'arguments': { 
                'symbol': [ ' ', ], 
                'venue': [ ' ', ], 
            }    
        },
        'SOREnableMultiVenuePlacement' : {
            'handler': 'SOREnableMultiVenuePlacement',
            'arguments': { 'NA': ['NA'] },
        },
        'SORDisableMultiVenuePlacement' : {
            'handler': 'SORDisableMultiVenuePlacement',
            'arguments': { 'NA': ['NA'] },
        },
        'setFeedPreference' : {
            'handler' : 'setFeedPreference',
            'arguments': { 
                'feedName': [ ' ', ], 
                'preference': [ ' ', ], 
                'executionPoint': [ ' ', ], 
            }    
        },
        'getInformation': {
            'handler': 'getInformation',
            'arguments': { 'NA': ['NA'] },
        },
        'setAutoFailoverDelayBuffer': {
            'handler': 'setAutoFailoverDelayBuffer',
            'arguments': { ' ': ['NA',] },
        },
        'startOverridingAggregatePositionData': {
            'handler': 'startOverridingAggregatePositionData',
            'arguments': { 'NA': ['NA'] },
        },
        'setAggregatePositionData': {
            'handler': 'setAggregatePositionData',
            'arguments': { 'NA': ['NA'] },
        },
        'ControlToggleExecSessionQCSource': {
            'handler': 'ControlToggleExecSessionQCSource',
            'arguments': { 'source': [ ' ', ], },
        },
        'ControlExcludeVenueFromConsolidatedBook': {
            'handler': 'ControlExcludeVenueFromConsolidatedBook',
            'arguments': { 'venue': [ ' ', ],}
        },
        'ControlReIncludeVenueInConsolidatedBook': {
            'handler': 'ControlReIncludeVenueInConsolidatedBook',
            'arguments': { 'venue': [ ' ', ],}
        }
    }
    return commands
