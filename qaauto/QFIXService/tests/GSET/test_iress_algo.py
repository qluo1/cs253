import random
from datetime import datetime, timedelta, time as dttime, date as dtdate
from pprint import pprint

from tests.fix_order import FIXOrder
import pytest
import gevent
import numpy as np
from dateutil import parser
import pytz
import copy

test_session = "PTIRESS"

#################################################################
## either user specify a symbol or a random symbol will be used.
#symbol = "LCM.AX"

######################################################################################
##  mapping is client specific, and can be customized by Darpan for each client.
test_clients = [
        {'fixId': 'GS_ARN_D','starId': '11332394'},
        #{'fixId': 'DAVE1','starId': '11315122'},
        #{'fixId': 'DAVE2','starId': '11315122'},
        ]

###################################################################
## mapping based on  IOS_to_AP mapping sheet.
## https://gsanzst.web.sharepoint.gs.com/AU%20EQ%20Trading%20Platform%20Integration/Shared%20Documents/Testing/IRESS%20Integration/IOS_to_ATP_Mapping.xlsx?Web=1

test_ios_algos = {

        'VWAP': {'data': {
            'Algorithm': 'VWAP',
            '8042': '1',  ## IOS-Style
            '9112': 30,   ## IOS-VolumnLimit
            '9007': 1,    ## IOS-SOR
            '8143': 1,    ## Rel Limit Bench 1/market, 2/sector
            '8141': 0,    ## visbility, no effective salVis=1
            },
            'expect': {
                'name': 'GSAT_VWAP',
                'tags': {
                    'executionStyle': 1,
                    'volumeLimit': 30,
                    'baseIndexType': 'Market',
                    'salVis': '1',
                    },
                },
            },

        'VWAP_1': {'data': {
            'Algorithm': 'VWAP',
            '8042': '2',  ## IOS-Style
            '9112': 30,   ## IOS-VolumnLimit
            '9007': 1,    ## IOS-SOR
            '8057': None, ## populate as order price.
            '8211': 10,
            '8210': 20,
            '8143': 2,    ## Rel Limit Bench
            '8144': 50.0,  ## -50 to  +50 
            },
            'expect': {
                'name': 'GSAT_VWAP',
                'tags': {
                    'executionStyle': 2, ## neutral
                    'volumeLimit': 30,
                    'salVis': '1',
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 10,
                    'cleanupPercentage': 20,
                    'baseIndexType': 'Sector',
                    'relativeOffsetPct': 50.0,
                    },
                },
            },

        'TWAP': {'data': {
            'Algorithm': 'TWAP',
            '8042': 3,  ## IOS-Style
            '8143': 1,  ## Rel limit benchmark/market
            '9112': 20,   ## IOS-VolumnLimit
            '9007': 1,
            },
            'expect': {
                'name': 'GSAT_TWAP',
                'tags': {
                    'salVis': '1',
                    'executionStyle': 3,
                    'volumeLimit': 20,
                    'baseIndexType': "Market",
                    },
                },
            },

        'TWAP_1': {'data': {
            'Algorithm': 'TWAP',
            '8042': 3,  ## IOS-Style
            '8143': 1,  ## Rel limit benchmark/market
            '9112': 20,   ## IOS-VolumnLimit
            '9007': 1,
            '8057': None, ## populate as order price.
            '8211': 10,
            '8210': 20,
            '8143': 2,    ## Rel Limit Bench
            '8144': 35.0,

            },
            'expect': {
                'name': 'GSAT_TWAP',
                'tags': {
                    'salVis': '1',
                    'executionStyle': '3',
                    'volumeLimit': '20',
                    'baseIndexType': "Market",
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 10,
                    'cleanupPercentage': 20,
                    'baseIndexType': 'Sector',
                    'relativeOffsetPct': 35.0,
                    },
                },
            },

        'IS': {'data': {
            'Algorithm': 'IS',
            '8042': '1',  ## IOS-Style
            '8094': '3',  ## IOS-Benchmark Type
            '9007': 1,
            },
            'expect':{
                'name': 'GSAT_4CAST',
                'tags': {
                    'salVis': '1',
                    'riskAvoidance': '2',
                    'benchMarkType': "midPrice",
                    },

                },
            },

        'IS_1': {'data': {
            'Algorithm': 'IS',
            '8042': '2',  ## IOS-Style
            '8094': '2',  ## IOS-Benchmark Type
            '9007': 1,
            '8057': None, ## populate as order price.
            '8211': 40,
            '8210': 50,
            '8143': 2,    ## Rel Limit Bench
            },
            'expect':{
                'name': 'GSAT_4CAST',
                'tags': {
                    'salVis': '1',
                    'riskAvoidance': '5',
                    'benchMarkType': "openPrice",
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 40,
                    'cleanupPercentage': 50,
                    'baseIndexType': 'Sector',
                    },

                },
            },

        'IS_2': {'data': {
            'Algorithm': 'IS',
            '8042': '3',  ## IOS-Style
            '8094': '1',  ## IOS-Benchmark Type
            '9007': 1,
            '8057': None, ## populate as order price.
            '8211': 20,
            '8210': 30,
            '8143': '1',  ## RelLimitBench
            '8144': 30.0, ## Rel Limit Offset %
            },
            'expect':{
                'name': 'GSAT_4CAST',
                'tags': {
                    'salVis': '1',
                    'riskAvoidance': '8',
                    'benchMarkType': "prevClose",
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 20,
                    'cleanupPercentage': 30,
                    'baseIndexType': 'Market',
                    'relativeOffsetPct': 30.0,
                    },

                },
            },

        'PARTICIPATE': {'data': {
            'Algorithm': 'PARTICIPATE',
            '8042': 1, ## style  1 /2/3
            '9111': 30,  ## participate rate
            '9007': 1,
            }, 'expect': {
                'name': 'GSAT_Participate',
                'tags': {
                    'salVis': '1',
                    'executionStyle':1,
                    'volumeLimit': 30,
                    },

                },
            },

        'PARTICIPATE_1': {'data': {
            'Algorithm': 'PARTICIPATE',
            '8042': 2,
            '9111': 35,  ## participate rate
            '9007': 1,
            '8057': None, ## populate as order price.
            '8211': 20,
            '8210': 30,
            '8143': 1,  ## RelLimitBench
            '8144': 30.0, ## Rel Limit Offset %
            }, 'expect': {
                'name': 'GSAT_Participate',
                'tags': {
                    'salVis': '1',
                    'executionStyle':2,
                    'volumeLimit': 35,
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 20,
                    'cleanupPercentage': 30,
                    'baseIndexType': 'Market',
                    'relativeOffsetPct': 30.0,
                    },
                },
            },

        'SCALING': {'data': {
            'Algorithm': 'SCALING',
            '8042': 2,  ## style
            '8094': 1,  ## IOS-Benchmark Type / Arrival
            '8094': 1,  ## execution view
            '8047': 10.0, ## min val
            '9849': 10.0, ## start val
            '8046': 40.0, ## max vol
            '9007': 1,
            },'expect':{
                'name': 'GSAT_DScaling',
                'tags': {
                    'salVis': "1",
                    'benchMarkType': "prevClose",
                    'executionStyle': 2,
                    'minPRate': 10.0,
                    'maxPRate': 40.0,
                    },

                },
            },

        'SCALING_1': {'data': {
            'Algorithm': 'SCALING',
            '8042': 3,  ## style
            '8094': 2,  ## IOS-Benchmark Type / Arrival
            '8094': 2,  ## execution view
            '8047': 10.0, ## min val
            '9849': 10.0, ## start val
            '8046': 40.0, ## max vol
            '8057': None, ## populate as order price.
            '8211': 20,
            '8210': 30,
            '8143': 1,     ## RelLimitBench
            '8144': -50.0, ## Rel Limit Offset %
            '9007': 1,
            },'expect':{
                'name': 'GSAT_DScaling',
                'tags': {
                    'salVis': "1",
                    'benchMarkType': "openPrice",
                    'executionStyle': 3,
                    'minPRate': 10.0,
                    'maxPRate': 40.0,
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 20,
                    'cleanupPercentage': 30,
                    'baseIndexType': 'Market',
                    'relativeOffsetPct': -50.0,
                    },

                },
            },

        'PWP': {'data': {
            'Algorithm': 'PWP',
            '8042': 1,
            '8148': 10, ## IOS PWP Benchmark
            '9007': 1,
            },'expect': {
                'name': 'GSAT_DScaling',
                'tags': {
                    'PWPBenchmarkRate': 10,
                    'benchMarkType': "PWP",
                    'executionStyle': 1,
                    'maxPRate': 15,
                    'minPRate': 5,
                    'salVis': '1',
                    },
                },
            },

        'PWP_1': {'data': {
            'Algorithm': 'PWP',
            '8042': 2,
            '8148': 10, ## IOS PWP Benchmark
            '8047': 30, ## min part%
            '8046': 90, ## max part%
            '9849': 30, ## start part%
            '9007': 1,
            '8057': None, ## populate as order price.
            '8211': 20,
            '8210': 30,
            '8143': 1,     ## RelLimitBench
            '8144': -50.0, ## Rel Limit Offset %

            },'expect': {
                'name': 'GSAT_DScaling',
                'tags': {
                    'PWPBenchmarkRate': 10,
                    'benchMarkType': "PWP",
                    'executionStyle': 2,
                    'maxPRate': 90,
                    'minPRate': 30,
                    'initPRate':30,
                    'salVis': '1',
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 20,
                    'cleanupPercentage': 30,
                    'baseIndexType': 'Market',
                    'relativeOffsetPct': -50.0,
                    },
                },
            },

        'PWP_2': {'data': {
            'Algorithm': 'PWP',
            '8042': 3,
            '8148': 10, ## IOS PWP Benchmark
            '8047': 30, ## min part%
            '8046': 90, ## max part%
            '9849': 10, ## start part%
            '9007': 1,
            '8057': None, ## populate as order price.
            '8211': 20,
            '8210': 30,
            '8143': 2,    ## RelLimitBench
            '8144': 50.0, ## Rel Limit Offset %

            },'expect': {
                'name': 'GSAT_DScaling',
                'tags': {
                    'PWPBenchmarkRate': 10,
                    'benchMarkType': "PWP",
                    'executionStyle': 3,
                    'maxPRate': 90,
                    'minPRate': 30,
                    'initPRate':10,
                    'salVis': '1',
                    'cleanupPrice': None,
                    'cleanupVolumeLimit': 20,
                    'cleanupPercentage': 30,
                    'baseIndexType': 'Sector',
                    'relativeOffsetPct': 50.0,
                    },
                },
            },

        'PEG': {'data': {
            'Algorithm': 'PEG',
            '8080': 1,   ## style 1 - passive touch, 2 - plus 1
            '8081': 0,   ## display type: 0 - auto
            '8110': 123,
            '9007': 1,
            },'expect': {
                'name': 'GSAT_Peg',
                'tags': {
                    'salVis': '1',
                    'maxShow': 123,
                    'maxShowType': 0,
                    'pegStyle': 1,
                    },
                },
            },
        'PEG_1': {'data': {
            'Algorithm': 'PEG',
            '8080': 2,
            '8081': 1, ## share
            '8110': 45,
            '9007': 1,
            },'expect': {
                'name': 'GSAT_Peg',
                'tags': {
                    'salVis': '1',
                    'maxShow': 45,
                    'maxShowType': 1,
                    'pegStyle': 0,
                    },
                },
            },
        'PEG_2': {'data': {
            'Algorithm': 'PEG',
            '8080': 2,
            '8081': 3, ## %order
            '8110': 45,
            '9007': 1,
            },'expect': {
                'name': 'GSAT_Peg',
                'tags': {
                    'salVis': '1',
                    'maxShow': 45,
                    'maxShowType': 3,
                    'pegStyle': 0,
                    },
                },
            },

        'PEG_3': {'data': {
            'Algorithm': 'PEG',
            '8080': 2,
            '8081': 5, ## %quote
            '8110': 41,
            '9007': 1,
            },'expect': {
                'name': 'GSAT_Peg',
                'tags': {
                    'salVis': '1',
                    'maxShow': 41,
                    'maxShowType': 5,
                    'pegStyle': 0,
                    },
                },
            },

        'STEALTH': {'data': {
            'Algorithm': 'STEALTH',
            '9007': 1,
            },'expect': {
                'name': 'GSAT_SonarBeta',
                'tags': {
                    'salVis': '1',
                    },
                },
            },

        'STEALTH_1': {'data': {
            'Algorithm': 'STEALTH',
            '9007': 1,
            '8053': 6,  ## min takeout size
            '8146': 1,  ## leave type
            '8147': 10, ## leave size
            },'expect': {
                'name': 'GSAT_SonarBeta',
                'tags': {
                    'salVis': '1',
                    'minTOSize': 6,
                    'leaveType': "Shares",
                    'leaveValue': 10,
                    },
                },
            },

        'STEALTH_2': {'data': {
            'Algorithm': 'STEALTH',
            '9007': 1,
            '8053': 30,  ## min takeout size
            '8146': 2,  ## leave type
            '8147': 10, ## leave size
            },'expect': {
                'name': 'GSAT_SonarBeta',
                'tags': {
                    'salVis': '1',
                    'minTOSize': 30,
                    'leaveType': "Pct",
                    'leaveValue': 10,
                    },
                },
            },

        'PEGSTEALTH': {'data': {
            'Algorithm': 'PEGSTEALTH',
            '8042': 1, ## style 1/2/3 aggressive
            '8080': 1, ## peg style
            '8081': 0, ## auto
            '9007': 1,
            },'expect': {
                'name': 'GSAT_PegStealth',
                'tags': {
                    'salVis': '1',
                    'maxShowType': 0,
                    'pegStyle': 1,
                    'snipeStyle': 2,
                    },
                },
            },

        'PEGSTEALTH_1': {'data': {
            'Algorithm': 'PEGSTEALTH',
            '8042': 2, ## style: neutral
            '8080': 2, ## peg style 1- passive touch, 2 - Plus 1
            '8081': 1, ## display: share
            '8110': 10,## display size
            '8146': 1, ## leave type: share
            '8147': 10,## leave qty
            '9007': 1,
            },'expect': {
                'name': 'GSAT_PegStealth',
                'tags': {
                    'salVis': '1',
                    'maxShowType': 1,
                    'maxShow': 10,
                    'pegStyle': 0,   ## peg style 2 mapped to 0
                    'snipeStyle': 1, ## style 2 map to 1
                    'leaveType': "Shares",
                    'leaveValue': 10,
                    },

                },
            },

        'PEGSTEALTH_2': {'data': {
            'Algorithm': 'PEGSTEALTH',
            '8042': 3, ## style: aggressive
            '8080': 2, ## peg style
            '8081': 3, ## display: %order
            '8110': 10,## display size
            '8146': 2, ## leave type: %
            '8147': 5, ## leave qty
            '9007': 1,
            },'expect': {
                'name': 'GSAT_PegStealth',
                'tags': {
                    'salVis': '1',
                    'maxShowType': 3,
                    'maxShow': 10,
                    'pegStyle': 0,
                    'snipeStyle': 0, ## 3 map 0
                    'leaveType': "Pct",
                    'leaveValue': 5,
                    },

                },
            },

        'ICEBERG': {'data': {
            'Algorithm': 'ICEBERG',
            '8042': '1', ## passive
            '8080': '1', ## peg style
            #'8081': '0', ## auto
            '9007': 1,
            },'expect' :{
                'name': 'GSAT_Iceberg',
                'tags': {
                    'salVis': '1',
                    'maxShowType': 'Auto',
                    },
                },
            },

        'SMALLCAP': {'data': {
            'Algorithm': 'SMALLCAP',
            '8042': 1,  ## style - neutral
            '8143': 1,  ## Rel limit benchmark/market
            '9112': 30, ## IOS-VolumnLimit
            '9007': 1,
            },'expect': {
                'name': 'GSAT_SmallCap',
                'tags': {
                    'salVis': '1',
                    'baseIndexType':"Market",
                    'executionStyle': 1,
                    'volumeLimit': 30,
                    }
                }
            },

        'SMALLCAP_1': {'data': {
            'Algorithm': 'SMALLCAP',
            '8042': 2,    ## style - neutral
            '8143': 2,    ## Rel limit benchmark/market
            '9112': 30,   ## IOS-VolumnLimit
            '9007': 1,
            '8144': 34,
            },'expect': {
                'name': 'GSAT_SmallCap',
                'tags': {
                    'salVis': '1',
                    'baseIndexType':"Sector",
                    'executionStyle': 2,
                    'volumeLimit': 30,
                    'relativeOffsetPct': 34.0,
                    }
                }
            },

        'SMARTDMA': {'data': {
            'Algorithm': 'SMARTDMA',
            '8110': 12,
            '9007': 1,
            },'expect': {
                'name': 'GSAT_Iceberg',
                'tags': {
                    'salVis': '1',
                    'maxExtantPerPrice': 12,
                    }
                },
            },

        'SMARTDMA_1': {'data': {
            'Algorithm': 'SMARTDMA',
            '9007': 1,
            },'expect': {
                'name': 'GSAT_Piccolo',
                'tags': {
                    'salVis': '1',
                    }
                },
            },

        '1CLICK': {'data': {
            'Algorithm': '1CLICK',
            '9098': 3,
            '9007': 1,
            },'expect': {
                'name': '1CLICK',
                'tags': {
                    'salVis': '1',
                    'custom': 3,
                    },
                }
            },

        'SIGMAX': {'data': {
            'Algorithm': 'SIGMAX',
            '9018': 'M',  #peg type M
            },'expect': {
                'name': 'SOR_AUSIGMAX',
                'tags': { },
                },
            },

        'SIGMAX_1': {'data': {
            'Algorithm': 'SIGMAX',
            '9018': 'P',  #peg type P
            },'expect': {
                'name': 'SOR_AUSIGMAX',
                'tags': { },
                },
            },

        'SonarDark': {'data': {
            'Algorithm': 'AUDARK',
            '9007': 1,
            },'expect': {
                'name': 'SOR_AUDark',
                'tags': { },
                },
            },

        'ONOPEN': {'data':{
            'Algorithm': 'CUSTOM',
            '9098': "2",
            },'expect': {
                'name': 'GSAT_Piccolo',
                'tags': {
                    'terminateTriggerExpr': "period == 2",
                    'salVis': '1',
                    'startTime': "today+'9:45:00'",
                    }
                },
            },

        'ONCLOSE': {'data': {
            'Algorithm': 'CUSTOM',
            '9098': "3",
            },'expect': {
                'name': 'GSAT_Piccolo',
                'tags': {
                    'salVis': '1',
                    'startTime': "closeAuctStart+'15s'"
                    }
                },
            },
        }

NOT_ATP_ALGO = ('SIGMAX','SIGMAX_1','SonarDark')

def is_16_15():
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    if hour > 16 or hour == 16 and minute > 15:
        return True
    return False

today = dtdate.today()
now = datetime.now()

tz_offset = int(datetime.now(pytz.timezone("Australia/Sydney")).strftime("%z"))/100
start_time = datetime(today.year,today.month,today.day,9, 49,30) - timedelta(hours=tz_offset)
end_time = datetime(today.year,today.month,today.day,16, 15,0) - timedelta(hours=tz_offset)

from tests._utils import active_wait, tickSize, get_passive_price

from MultiDict import OrderedMultiDict

class Test_IOS_Algo:
    """
    test IOS Algo order.
    """
    scenarios = []

    ## algo not mapped yet
    ignore_algos = ['1CLICK',]

    for test_client in test_clients:
        for algo in test_ios_algos:
            if algo in ignore_algos: continue
            client = test_client.copy()
            client.update({'algo': algo})
            scenarios.append(client)

    def test_new_amend_cancel(self,fixId,starId,algo,symbol_depth,nvp_service):
        """ """
        if 'symbol' in globals():
            quote,cha_quote = symbol_depth.get_symbol_quote(symbol)
        else:
            symbol,quote,cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)

        last,bid,ask,close = quote['last'],quote['bid']['bid'],quote['ask']['ask'],quote['close']

        side = random.choice(['Buy','Sell','Sell Short'])
        delta = 3 if side == "Buy" else -3

        print " ====== market quote ====="
        pprint(quote)
        price_aggr = last + tickSize(last,delta)
        price_pass = last - tickSize(last,delta)

        qty = random.randint(1000,5000)
        order = {
                'side': side,
                'symbol': symbol,
                'ordType': "Limit",
                'price': price_pass,
                'qty': qty,
                'extra': {
                    "HandlInst"   : "auto-public",
                    "IDSource"    : "RIC code",
                    "SecurityID"  : symbol,
                    "Account"     : fixId,
                    "SendingTime" : datetime.utcnow(),
                    "SecurityType": "CS",
                    "SecurityExchange":"ASX",
                    #"OnBehalfOfCompID":fixId,
                    "Allocs": [{"AllocAccount":"DAVE_BOOK","AllocShares":qty}],
                    ## start/end time
                    "EffectiveTime": start_time,
                    "ExpireTime": end_time,
                    "Currency": "AUD",
                    }
                }

        ## set algo param
        algoVals = copy.deepcopy(test_ios_algos[algo]['data'])
        expect =  copy.deepcopy(test_ios_algos[algo]['expect'])
        ## cleanup price
        if '8057' in algoVals:
            algoVals['8057'] = price_pass
            expect['tags']["cleanupPrice"] = price_pass

        order['extra'].update(algoVals)

        pprint(order)

        test_order = FIXOrder(test_session,order)

        ## check session status
        status = test_order.session_status
        assert status['loggedon'] and status['enabled']
        ### 

        ## submit new order
        clOrdId, ers = test_order.new()
        assert len(ers) == 1
        assert 'OrderID' in ers[0]
        ## wait for nvp ready.
        gevent.sleep(2)
        ## capture nvp before validation order status.
        oma_order_id = ers[0]["OrderID"]
        nvp_list = nvp_service.get_order(oma_order_id,nvp=True)
        assert len(nvp_list) > 0, "query nvp failed"
        nvp = OrderedMultiDict(nvp_list)
        algo_name = nvp["OmaOrder"]["OmaNvpTradingAlgorithm"]
        algo_params = nvp["OmaOrder"]["OmaNvpTradingAlgorithmParameters"]
        oma_execInst = nvp["OmaOrder"]["OmaNvpExecutionInstructions"]
        print "algo_name", algo_name
        print "algo_params", algo_params
        print "oma_execInst", oma_execInst
        ##############################
        ##validate mapping
        ## when atp closed, only send new order only.
        atp_closed  = is_16_15()
        if not atp_closed or algo in NOT_ATP_ALGO :
            assert ers[0]['MsgType'] == "ExecutionReport"
            assert ers[0]['OrdStatus'] == "New"
            assert ers[0]['ExecTransType'] == "New"
        else:
            assert ers[0]['MsgType'] == "ExecutionReport"
            ## atp might stll accept new order, but will not cancel order.
            #assert ers[0]['OrdStatus'] == "Rejected"

        ## check sor enabled
        if '9007' in algoVals:
            assert '83' in oma_execInst
        assert algo_name == expect["name"]

        if algo not in ('SIGMAX','SIGMAX_1','SonarDark'):
            atp_params = dict([r.split("=",1) for r in algo_params])
            atp_params = {k:v.replace("\"","") for k,v in atp_params.iteritems()}
            ## compare each key/value
            for k, v in expect['tags'].iteritems():
                assert k in atp_params
                if isinstance(v,int):
                    assert v == int(atp_params[k]) , "key:%s, val:%s, atp: %s" % (k,v,atp_params)
                elif isinstance(v,float):
                    assert np.isclose(v,float(atp_params[k]))
                else:
                    assert v == atp_params[k]

            ## validate startTime/endTime if not specified.
            if "startTime" not in expect['tags']:
                startTime = parser.parse(atp_params["startTime"]).replace(tzinfo=None)
                assert startTime == start_time
            if "endTime" not in expect['tags']:
                endTime = parser.parse(atp_params["endTime"]).replace(tzinfo=None)
                assert endTime == end_time

        ## skip amend for atp closed.
        if atp_closed:
            return
        gevent.sleep(10)
        clOrdId, ers = test_order.amend(qty=order['qty'] + 2000,
                price=price_aggr,
                expected_num_msg=2)
        assert len(ers) == 2
        er_pending_replace = ers[0]
        er_replace = ers[1]
        assert er_pending_replace['MsgType'] == "ExecutionReport"
        assert er_replace['MsgType'] == "ExecutionReport"

        assert er_pending_replace['ExecType'] == "Pending Replace"
        assert er_pending_replace["OrdStatus"] == "Pending Replace"
        assert er_replace['ExecType'] == "Replace"
        assert er_replace["OrdStatus"] == "Replaced"

        gevent.sleep(10)
        clOrdId, ers = test_order.cancel(expected_num_msg=2)
        assert ers
        assert len(ers) == 2

        assert ers[0]['MsgType'] == "ExecutionReport"
        assert ers[0]["OrdStatus"] == "Pending Cancel"
        assert ers[0]["ExecType"] == "Pending Cancel"

        assert ers[1]['MsgType'] == "ExecutionReport"
        assert ers[1]["OrdStatus"] == "Canceled"
        assert ers[1]["ExecType"] == "Canceled"


