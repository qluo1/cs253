""" OM2 AUCEL QA ivcom config.  """
import copy
## ivcom base catalog
import catalog
## om2 catalog
import om2CompleteCatalog
## hermes catalog
import hermesCatalog

## configuraiton variables: host, port 
VARS = {
        'rf':9200,  'dss':9214,  'hermes':9216,'port': 9094,'rds-hermes': 14741,'imgLive': 9215,
        'oma_port':31105,
        'primary': 'pmeaucea-1.pp.om2.services.gs.com',
        'secondary': 'pmeaucea-2.pp.om2.services.gs.com',
        }

instance = "PMEAUCEA"

def configure():
    mycatalog = copy.deepcopy(catalog.basecatalog)
    ##
    catalog.combineCatalogs(mycatalog,hermesCatalog.hermesCatalog)
    catalog.combineCatalogs(mycatalog,om2CompleteCatalog.om2CompleteCatalog)

    config = {
        'catalog': mycatalog,

        'ivcom': {
                'application-id'   : 'IvComPyServer',
                'application-type' : 'IvComPyServer',
                #'http-metrics'     : { 'port': VARS['port'] }
                },

        'channels': {'hermes': {'connect-to':
                                    [
                                        {'host': VARS['primary'], 'port': VARS['hermes']},
                                     ]
                               },
                     'rf': {'connect-to':
                                    [
                                        {'host': VARS['primary'], 'port': VARS['rf']},
                                        {'host': VARS['secondary'], 'port': VARS['rf']},
                                    ]
                            },
                     'dss': {'connect-to':
                                    [
                                        {'host': VARS['primary'], 'port': VARS['dss']},
                                        {'host': VARS['secondary'], 'port': VARS['dss']},

                                    ]
                            },
                     'rds-hermes':{'connect-to':
                                    [
                                        {'host': VARS['primary'], 'port': VARS['rds-hermes']},
                                        {'host': VARS['secondary'], 'port': VARS['rds-hermes']},
                                    ]
                            },
                     'imageLive':{'connect-to':
                                    [
                                        {'host': VARS['primary'], 'port': VARS['imgLive']},
                                        {'host': VARS['secondary'], 'port': VARS['imgLive']},
                                    ]
                            },
                },
         ## client requests
         'client-request-managers': {
             "%s-Primary" % instance :
                  {
                    'applicationid': 'hermes',
                    'auto-indicate-availability-load': 100,
                    'catalog':
                        [
                            'HermesCommand',
                            'HermesCommandResult',
                            'HermesCommandArgument'
                        ],
                  'channel': 'hermes',
                  'request-failure-interval': 300
                 },
            'engine-%s-requestResponse' % instance:
                {
                    'applicationid': 'MyIvComPy-rf',
                    'channel': 'rf',
                },
            'QAAUCE-d48965-004.dc.gs.com-PRODMIRROR': {
                'applicationid': 'rds-hermes',
                'auto-indicate-availability-load': 100,
                'catalog':
                    [
                        'HermesCommand',
                        'HermesCommandResult',
                        'HermesCommandArgument'
                    ],
              'channel': 'rds-hermes',
              'request-failure-interval': 300
            },
           },
         ################################################ 
         'client-datastreams': {
                "%s->QAAUCE_Listener" % instance:
                {
                    "applicationid":"MyIvComPy-dss",
                    "channel":"dss",
                },

                ### "TransactionNotification"
                #"%s->replication" % instance:{
                #    "applicationid":"MyIvComPy-dss",
                #    "channel":"rf",
                #},
           },
        #############################################
        'image-live-clients':{
               "imageliveserver-%s" % instance:
               {
                   "applicationid":"MyIvComPy-imagelive",
                   "channel":"imageLive",
               },
        },
        ### configure server datastream 
        #'server-datastreams': {
        #}## server-datastrea
    }

    return config


if __name__ == "__main__":
    """ local debug. print out config."""

    from pprint import pprint
    pprint(configure())



