import os
import catalog
import hermesCatalog
import copy

import om2CompleteCatalog

## test instance PPE or QAE
env = os.getenv("ENV","PPE")
instance = env + "AUCEA"

hosts = {
        'QAE': {'rf':10200, 'dss':10214, 'hermes':10202,'xtdb':10211,'port': 9092, 'rds-hermes': 14739,'imgLive': 10215,
                ## not oma 
                'primary': 'qaeaucea-1.qa.om2.services.gs.com',
                'secondary': 'qaeaucea-2.qa.om2.services.gs.com',
                ## viking 
                'vkhost': 'qaecxaa-p.qa.viking.services.gs.com',
                'vkasx': 13820,
                'vkcxa': 27420,
                },

        'PPE': {'rf':10300, 'dss':10314, 'hermes':10302,'xtdb': 10311,'port': 9093,'rds-hermes': 14740,'imgLive': 10315,
                #'oma_XTDd': 'xtdd-1.qa.oma.services.gs.com',
                'oma_port':31105,
                'primary': 'ppeaucea-1.pp.om2.services.gs.com',
                'secondary': 'ppeaucea-2.pp.om2.services.gs.com',
                ## viking 
                'vkhost': 'ppecxaa-p.qa.viking.services.gs.com',
                'vkasx': 14070,
                'vkcxa': 27520,
                },

        'PME': {'rf':9200,  'dss':9214,  'hermes':9216,'port': 9094,'rds-hermes': 14741,'imgLive': 9215,
                ## no oma, 
                'primary': 'pmeaucea-1.pp.om2.services.gs.com',
                'secondary': 'pmeaucea-2.pp.om2.services.gs.com',
                ## viking  channel not available for PME
                #'vkhost': 'ppecxaa-p.qa.viking.services.gs.com',
                #'vkasx': 14070,
                #'vkcxa': 27520,
                },
        }
###########################
# primary
#'d48965-004.dc.gs.com'
# secondary
#'d48965-005.dc.gs.com'
###########################

def configure():
    mycatalog = copy.deepcopy(catalog.basecatalog)
    ##
    catalog.combineCatalogs(mycatalog,hermesCatalog.hermesCatalog)
    catalog.combineCatalogs(mycatalog,om2CompleteCatalog.om2CompleteCatalog)

    config = {
        'catalog': mycatalog,

        'ivcom': {
                'application-id'   : "myivcompy",
                'application-type' : 'myivcompy',
                'http-metrics'     : { 'port': hosts[env]['port'] }
                },

        'channels': {'hermes': {'connect-to':
                                    [
                                        {'host': hosts[env]['primary'],
                                         'port': hosts[env]['hermes']
                                         },
                                     ]
                               },
                     'rf': {'connect-to':
                                    [
                                        {'host': hosts[env]['primary'], 'port': hosts[env]['rf']},
                                        {'host': hosts[env]['secondary'], 'port': hosts[env]['rf']},
                                    ]
                            },
                     'dss': {'connect-to':
                                    [
                                        {'host': hosts[env]['primary'], 'port': hosts[env]['dss']},
                                        {'host': hosts[env]['secondary'], 'port': hosts[env]['dss']},

                                    ]
                            },
                     'rds-hermes':{'connect-to':
                                    [
                                        {'host': hosts[env]['primary'], 'port': hosts[env]['rds-hermes']},
                                        #{'host': hosts[env]['secondary'], 'port': hosts[env]['rds-hermes']},
                                    ]
                            },
                     'imageLive':{'connect-to':
                                    [
                                        {'host': hosts[env]['primary'], 'port': hosts[env]['imgLive']},
                                        {'host': hosts[env]['secondary'], 'port': hosts[env]['imgLive']},
                                    ]
                            },


                },
         ## client requests
         'client-request-managers': {
             '%s-Primary' % instance:
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
            },
         ## client datastreams
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

         'image-live-clients':{
                "imageliveserver-%s" % instance:
                {
                    "applicationid":"MyIvComPy-imagelive",
                    "channel":"imageLive",
                },
        },
    }

    ### rds hermes
    if env == 'QAE' and 'rds-hermes' in hosts[env]:
        config['client-request-managers']['QAAUCE-d48965-004.dc.gs.com-PRODVER'] = {
            'applicationid': 'my-hermes',
            'auto-indicate-availability-load': 100,
            'catalog':
                [
                    'HermesCommand',
                    'HermesCommandResult',
                    'HermesCommandArgument'
                ],
          'channel': 'rds-hermes',
          'request-failure-interval': 300

        }

    if env == 'PPE' and 'rds-hermes' in hosts[env]:
        config['client-request-managers']['QAAUCE-d48965-004.dc.gs.com-PREPROD'] = {
            'applicationid': 'my-hermes',
            'auto-indicate-availability-load': 100,
            'catalog':
                [
                    'HermesCommand',
                    'HermesCommandResult',
                    'HermesCommandArgument'
                ],
          'channel': 'rds-hermes',
          'request-failure-interval': 300

        }

    if env == 'PME' and 'rds-hermes' in hosts[env]:
        config['client-request-managers']['QAAUCE-d48965-004.dc.gs.com-PRODMIRROR'] = {
            'applicationid': 'my-hermes',
            'auto-indicate-availability-load': 100,
            'catalog':
                [
                    'HermesCommand',
                    'HermesCommandResult',
                    'HermesCommandArgument'
                ],
          'channel': 'rds-hermes',
          'request-failure-interval': 300

        }


    ####################################
    ## update instance specific settings

    ## connect to xtdb at om2
    if 'xtdb' in hosts[env]:
        ## setup channel i.e. om-routing
        channel_name = 'XTDb'
        config['channels'][channel_name] = {
            ##
            'connect-to': [
                          {'host': hosts[env]['primary'], 'port': hosts[env]['xtdb']},
                          {'host': hosts[env]['secondary'], 'port': hosts[env]['xtdb']},
                          ]
        }

        ## configure client datastream i.e. om2->oma
        config['client-datastreams'] ['%s->qa_XTDb' % instance] = {
                    "applicationid":"MyIvComPy-qa_XTDb",
                    "channel":channel_name,
        }
        ## server datastreams i.e. oma->om2
        if 'server-datastreams' not in config:
            config['server-datastreams'] =  {}

        # configure server datastream 
        config['server-datastreams']['qa_XTDb->%s' % instance] = {
                    "applicationid":"MyIvComPy-qa_XTDb",
                    "channel":channel_name,
                    "catalog": [
                             "RejectOrderCommand",
                             "AcceptOrderCommand",
                             "CorrectExecutionCommand",
                             "DoneForDayOrderCommand",
                             "RequestCorrectOrderCommand",
                             "AcceptCorrectOrderCommand",
                             "RejectCorrectOrderCommand",
                             "AcceptCancelOrderCommand",
                             "RejectCancelOrderCommand",
                             "RequestCancelOrderCommand",
                             "CreateOrderCommand",
                             "CreateExecutionCommand",
                             "CancelExecutionCommand",
                             "ForceCancelOrderCommand",
                             "UserAlertCommand",
                             "RoutedMessage",
                             "CommandRequest",
                             "CommandResponse",
                             "CommandReject",
                             "OrderSuspendedDownstreamCommand",
                             "OrderUnsuspendedDownstreamCommand",
                        ],
                    "auto-indicate-availability-load":"100",
        }


    ## connect to xtdb at om2
    if 'xtdd' in hosts[env]:
        channel_name = "XTDd"
        config['channels'][channel_name] = {
            ##
            'connect-to': [
                          {'host': hosts[env]['primary'], 'port': hosts[env]['xtdd']},
                          {'host': hosts[env]['secondary'], 'port': hosts[env]['xtdd']},
                          ]
        }
        ## configure client data stream
        config['client-datastreams'] ['%s->qa_XTDd' % instance] = {
                    "applicationid":"MyIvComPy-qa_XTDd",
                    "channel":channel_name,
        }

        ## server datastreams i.e. oma->om2
        if 'server-datastreams' not in config:
            config['server-datastreams'] =  {}
        # configure server datastream 
        config['server-datastreams']['qa_XTDd->%s' % instance] = {
                    "applicationid":"MyIvComPy-qa_XTDd",
                    "channel":channel_name,
                    "catalog": [
                             "RejectOrderCommand",
                             "AcceptOrderCommand",
                             "CorrectExecutionCommand",
                             "DoneForDayOrderCommand",
                             "RequestCorrectOrderCommand",
                             "AcceptCorrectOrderCommand",
                             "RejectCorrectOrderCommand",
                             "AcceptCancelOrderCommand",
                             "RejectCancelOrderCommand",
                             "RequestCancelOrderCommand",
                             "CreateOrderCommand",
                             "CreateExecutionCommand",
                             "CancelExecutionCommand",
                             "ForceCancelOrderCommand",
                             "UserAlertCommand",
                             "RoutedMessage",
                             "CommandRequest",
                             "CommandResponse",
                             "CommandReject",
                             "OrderSuspendedDownstreamCommand",
                             "OrderUnsuspendedDownstreamCommand",
                        ],
                    "auto-indicate-availability-load":"100",
        }


    #import pdb;pdb.set_trace()
    ## connect to oma
    if 'oma_XTDd' in hosts[env]:
        channel_name = "oma_XTDd"
        config['channels'][channel_name] = {
            'connect-to': [
                            {'host': hosts[env]['oma_XTDd'], 'port': hosts[env]['oma_port']},
                        ]
        }

        ## configure client datastream i.e. om2->oma
        config['client-datastreams'] ['%s->qa_XTDd' % instance] = {
                    "applicationid":"MyIvComPy-qa_XTDd",
                    "channel":channel_name,
        }

    ## configure viking
    if 'vkhost' in hosts[env]:
        channel_asx = "viking_asx"
        config['channels'][channel_asx] = {
            'connect-to': [
                {
                    'host': hosts[env]['vkhost'],
                    'port': hosts[env]['vkasx'],
                    },

            ]
        }

        ## server datastreams i.e. oma->om2
        if 'server-datastreams' not in config:
            config['server-datastreams'] =  {}

        # configure server datastream 
        config['server-datastreams']['TESTC->%sASXA' % env] = {
                    "applicationid":"MyIvComPy-VKASX",
                    "channel":channel_asx,
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
        }

        ## configure client datastream i.e. om2->oma
        config['client-datastreams'] ['%sASXA->TESTC' % env] = {
                    "applicationid":"MyIvComPy-VKASX",
                    "channel":channel_asx,
        }

        channel_cxa = "viking_cxa"
        config['channels'][channel_cxa] = {
            'connect-to': [
                {
                    'host': hosts[env]['vkhost'],
                    'port': hosts[env]['vkcxa'],

                    },
            ]
        }
        ## configure client datastream i.e. om2->oma
        config['client-datastreams'] ['%sCXAA->TESTA' % env] = {
                    "applicationid":"MyIvComPy-VKCXA",
                    "channel":channel_cxa,
        }

        # configure server datastream 
        config['server-datastreams']['TESTA->%sCXAA' % env] = {
                    "applicationid":"MyIvComPy-VKCXA",
                    "channel":channel_cxa,
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
        }


        if env == "QAE":
            ## configure HK viking
            channel_hk = "viking_hk"
            config['channels'][channel_hk] = {
                'connect-to': [
                    {
                        'host': 'hkampsa10.hk.eq.gs.com',
                        'port': 11020,

                        },
                ]
            }
            ## configure client datastream i.e. om2->oma
            config['client-datastreams'] ['HKSEC->TC1'] = {
                        "applicationid":"viking",
                        "channel":channel_hk,
            }

            # configure server datastream 
            config['server-datastreams']['TC1->HKSEC'] = {
                        "applicationid":"viking",
                        "channel":channel_hk,
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
            }



    return config;


if __name__ == "__main__":
    """
      unit test
    """
    config = configure()

    from pprint import pprint
    pprint(config)

