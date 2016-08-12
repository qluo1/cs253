import os
import catalog
import hermesCatalog
import string
import copy


def configure():
    mycatalog = copy.deepcopy(catalog.basecatalog)
    ## 
    catalog.combineCatalogs(mycatalog,hermesCatalog.hermesCatalog)

    config = {
        'catalog': mycatalog,

        'ivcom': {
                'application-id'   : "myivcompy",
                'application-type' : 'myivcompy',
                },

        'channels': {'hermesstandalone': {'connect-to': [{'host': 'd48965-004.dc.gs.com', 'port': '10302'}]
            }
                                                   },
         'client-request-managers': {'PPEAUCEA-Primary':
                                          {'applicationid': 'hermes',
                                          'auto-indicate-availability-load': 100,
                                          'catalog': ['HermesCommand',
                                                      'HermesCommandResult',
                                                      'HermesCommandArgument'
                                                      ],
                                          'channel': 'hermesstandalone',
                                          'request-failure-interval': 300
                                          }
            },
    }


    return config;

#
#if __name__ == "__main__":
#    """
#      unit test
#    """
#    config = configure()
#
#    from pprint import pprint
#    pprint(config)
#


