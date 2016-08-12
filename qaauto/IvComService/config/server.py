""" demo server ivcom config.  """
# rcsid "$Header: /home/cvs/eqtech/cep/src/ivcom/config/server.py,v 1.21 2014/02/26 18:51:30 krielq Exp $"

import copy
# This imports the message definitions defined in catalog.py
import catalog
# This imports the extra message definitions defined in examplecatalog.py
#import examplecatalog

def configure():
    # To produce the server catalog, we copy the base IvCom catalog
    servercatalog = copy.deepcopy(catalog.servercatalog)

    # these values are configured very small to speed testing
    # do NOT use these values in production configurations
    servercatalog['default-catalog-downloading-num-providers-to-discover'] = 1
    servercatalog['default-catalog-downloading-provider-discovery-interval'] = 1

    return {
        'catalog': servercatalog,
        'channels': {
            'sample-channel': { 'accept-on'  : [ { 'port': 10013 } ] ,
                                'connect-to' : [ { 'host': 'localhost', 'port': 10214 } ],
                                'connecter-accepter': 'true'},
        },
        'ivcom' : {
            'application-id' : 'server',
            'application-type' : 'ivcom-sample-application'
        },
        'server-datastreams': {
            'sample-datastream': { # Used by ExampleIvComDatastreamServer.cpp
                'channel': 'sample-channel',
                'catalog': [ 'TextMessage',
                    # Note: NewTable is not present in the client config. If the last line of this comment
                    # is uncommented, as well as the table definition in examplecatalog.py, the table
                    # definition will be downloaded to the client during datastream initialization.
                    # 'NewTable'
                    ],
                'applicationids': [ 'sample-app' ],
                'maximum-in-flight-messages': 20,
                'auto-indicate-availability-load': 100,
            },
        },
        'server-request-managers': {
            'sample-requests': { # Used by ExampleIvComRequestServer.cpp
                'channel': 'sample-channel',
                'catalog': [ 'TextMessage' ],
                'applicationids': [ 'sample-app' ],
                'auto-indicate-availability-load': 100,
            },
        },
        'image-live-servers': { # Used by ExampleIvComImageLiveServer.cpp
                'sample-image-live': {
                    'channel': 'sample-channel',
                    'catalog': [ 'create-view', 'TextMessage' ],
                    'applicationids': [ 'IMAGELIVE' ],
                    'maximum-in-flight-messages': 1000,
                    'maximum-views-per-client' : 3,
                },
        },
    }
