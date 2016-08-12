""" demon ivcom client config. """
# rcsid "$Header: /home/cvs/eqtech/cep/src/ivcom/config/client.py,v 1.18 2014/02/26 18:53:57 krielq Exp $"
import catalog
import examplecatalog

def configure():
    clientCatalog = catalog.servercatalog
    # The following line adds a table not found in server.py to test catalog downloading
    # clientCatalog['tables'].update(examplecatalog.servercatalog['tables'])

    # these values are configured very small to speed testing
    # do NOT use these values in production configurations
    clientCatalog['default-catalog-downloading-num-providers-to-discover'] = 1
    clientCatalog['default-catalog-downloading-provider-discovery-interval'] = 1

    config = {
            'catalog': clientCatalog,
            'channels': {
                'sample-channel': {
                    'connect-to' : [ { 'host': 'localhost', 'port': 10013 } ],
                    'accept-on'  : [ { 'port': 10214 } ],
                    'connecter-accepter': 'true'
                },
            },
            'ivcom' : {
                'application-id' : 'client',
                'application-type' : 'ivcom-sample-application'
            },
            'client-datastreams': { # Used by ExampleIvComDatastreamClient.cpp
                'sample-datastream': {
                    'channel': 'sample-channel',
                    'applicationid': 'sample-app'
                },
            },
            'client-request-managers': { #  Used by ExampleIvComRequestClient.cpp
                'sample-requests': {
                    'maximum-in-flight-messages': 1,
                    'channel': 'sample-channel',
                    'applicationid': 'sample-app',
                    'catalog': [ 'TextMessage' ]
                },
            },
            'image-live-clients': { # Used by ExampleIvComImageLiveClient.cpp
                'sample-image-live': {
                    'channel': 'sample-channel',
                    'applicationid': 'IMAGELIVE',
                },
            },
    }

    return config
