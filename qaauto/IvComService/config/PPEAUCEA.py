""" OM2 AUCEL QA ivcom config.  """
import copy
## ivcom base catalog
import catalog
## om2 catalog
import om2CompleteCatalog
## hermes catalog
import hermesCatalog

## configuraiton variables: host, port 
VARS = {'rf':10300, 'dss':10314, 'hermes':10302,'xtdb': 10311,'port': 9093,'rds-hermes': 14740,'imgLive': 10315,
        #'oma_XTDd': 'xtdd-1.qa.oma.services.gs.com',
        'oma_port':31105,
        'primary': 'ppeaucea-1.pp.om2.services.gs.com',
        'secondary': 'ppeaucea-2.pp.om2.services.gs.com',
        ## viking 
        'vkhost-p': 'ppecxaa-p.qa.viking.services.gs.com',
        'vkhost-s': 'ppecxaa-s.qa.viking.services.gs.com',
        'vkasx': 14070,
        'vkcxa': 27520,
        }

instance = "PPEAUCEA"

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

                    'viking_asx':{ 'connect-to':
                                [
                                {
                                    'host': VARS['vkhost-p'], 'port': VARS['vkasx'],
                                },
                                {
                                    'host': VARS['vkhost-s'], 'port': VARS['vkasx'],
                                },


                                ]
                        },
                    "viking_cxa":{ 'connect-to':
                                [
                                 {
                                'host': VARS['vkhost-p'], 'port': VARS['vkcxa'],
                                },
                                 {
                                'host': VARS['vkhost-s'], 'port': VARS['vkcxa'],
                                },

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
            'QAAUCE-d48965-004.dc.gs.com-PREPROD': {
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

                ## "TransactionNotification"
                #"%s->replication" % instance:{
                #    "applicationid":"MyIvComPy-dss",
                #    "channel":"rf",
                #},
                ## viking
                'PPEASXA->TESTC' : {
                    "applicationid":"MyIvComPy-VKASX",
                    "channel":'viking_asx',
                    },
                ## configure client datastream i.e. om2->oma
                'PPECXAA->TESTA' : {
                            "applicationid":"MyIvComPy-VKCXA",
                            "channel":'viking_cxa',
                },
                ## "TransactionNotification"
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
        # configure server datastream 
        'server-datastreams': {
            'TESTC->PPEASXA' : {
                    "applicationid":"MyIvComPy-VKASX",
                    "channel":'viking_asx',
                    "catalog": [
                          "VikingOrderReinstateCommand",
                          "VikingOrder",
                          "VikingAmendOrder",
                          "VikingCancelOrder",
                          "VikingMultiLegOrder",
                          "VikingAmendMultiLegOrder",
                          "VikingCancelMultiLegOrder",
                          "VikingQuote",
                        ],
                    "auto-indicate-availability-load":"100",
            },
            # configure server datastream 
            'TESTA->PPECXAA' : {
                    "applicationid":"MyIvComPy-VKCXA",
                    "channel":'viking_cxa',
                    "catalog": [
                          "VikingOrderReinstateCommand",
                          "VikingOrder",
                          "VikingAmendOrder",
                          "VikingCancelOrder",
                          "VikingMultiLegOrder",
                          "VikingAmendMultiLegOrder",
                          "VikingCancelMultiLegOrder",
                          "VikingQuote",
                        ],
                    "auto-indicate-availability-load":"100",
            },

        }## server-datastrea
    }

    return config


if __name__ == "__main__":
    """ local debug. print out config."""

    from pprint import pprint
    pprint(configure())



