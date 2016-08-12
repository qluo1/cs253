
# rcsid "$Header: /home/cvs/eqtech/cep/src/ivcom/config/client.py,v 1.20 2015/05/11 14:50:37 heshas Exp $"

import catalog

# This configuration file depends on examplecatalog
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

            'dss-channel' : {
                'connect-to' : [ { 'host': 'localhost', 'port': 10014 } ],
                'accept-on'  : [ { 'port': 10215 } ],
                'connecter-accepter': 'true' }
        },
        'ivcom' : {
            'application-id' : 'client',
            'application-type' : 'ivcom-sample-application'
        },
        'client-request-managers': { 
            'sample-requests': {
                'maximum-in-flight-messages': 1,
                'channel': 'sample-channel',
                'applicationid': 'sample-app',
                'catalog': [ 'TextMessage' ]
            }
        },
        'client-datastreams': { 
            'sample-datastream': {
                'channel': 'dss-channel',
                'applicationid': 'sample-app'
            },
        },
        'server-datastreams': {
            'sample-datastream': {
                'channel': 'dss-channel',
                'catalog': ['TextMessage'],
                'applicationids': [ 'sample-app' ],
                'maximum-in-flight-messages': 20,
                'auto-indicate-availability-load': 100,
            }
        },
        'image-live-clients' : {
            'sample-image-live' : {
                'channel' : 'sample-channel',
                'applicationid' : 'IMAGELIVE',
            }
        }
    }
  
    return config

