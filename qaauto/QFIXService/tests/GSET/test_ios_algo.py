import random
from datetime import datetime, timedelta, time as dttime, date as dtdate
from pprint import pprint

from tests.fix_order import FIXOrder
import pytest
import gevent
import pytz
from tests._utils import active_wait, tickSize, get_passive_price

today = dtdate.today()
now = datetime.now()

tz_offset = int(datetime.now(pytz.timezone("Australia/Sydney")).strftime("%z"))/100
start_time = datetime(today.year,today.month,today.day,now.hour, now.minute,now.second) - timedelta(hours=tz_offset)
end_time = datetime(today.year,today.month,today.day,16, 15,0) - timedelta(hours=tz_offset)


## darkpan mapping IOS algo to ATP algo for per client.
test_clients = [
                {'fixId': 'GS_ARN_D','starId': '11332394'},
                #{'fixId': 'DAVE1','starId': '11315122'},
                #{'fixId': 'DAVE2','starId': '11315122'},
               ]

## helper for generate vwap algo
def _gen_vwap_algo ():
    return  {
        'Algorithm': 'VWAP',
        '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
        '9112': random.choice([1,100]),        ## IOS-VolumnLimit , 1-100
        '9007': random.choice([0,1]),          ## IOS-SOR
        '8143': random.choice(['1','2']),      ## IOS-RelLimitBench market/sector
       }

def _gen_vwap_cleanup(price=0):
    base = _gen_vwap_algo()
    base['8057'] = price                   ## cleanup price
    base['8211'] = random.choice([1,100])  ## cleanup vol limit
    base['8210'] = random.choice([1,100])  ## cleanup per% limit
    return base

def _gen_twap_algo ():
    return  {
        'Algorithm': 'TWAP',
        '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
        '9112': random.choice([1,100]),        ## IOS-VolumnLimit , 1-100
        '9007': random.choice([0,1]),          ## IOS-SOR
        '8143': random.choice(['1','2']),      ## IOS-RelLimitBench 1/2 market/sector
       }

def _gen_twap_cleanup(price=0):
    base = _gen_vwap_algo()
    base['8057'] = price                   ## cleanup price
    base['8211'] = random.choice([1,100])  ## cleanup vol limit
    base['8210'] = random.choice([1,100])  ## cleanup per% limit
    return base

def _gen_is_algo ():
    return  {
        'Algorithm': 'IS',
        '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
        '9112': random.choice([1,50]),         ## IOS-VolumnLimit , 1-50, participate rate
        '9007': random.choice([0,1]),          ## IOS-SOR
        '8143': random.choice(['0','1']),      ## IOS-RelLimit-Bench market/sector
        '8094': random.choice(['1','2','3'])   ## IOS-Benchmark Type
       }
def _gen_is_cleanup(price=0):
    base = _gen_is_algo()
    base['8057'] = price                   ## cleanup price
    base['8211'] = random.choice([1,100])  ## cleanup vol limit
    base['8210'] = random.choice([1,100])  ## cleanup per% limit
    return base

########################################
## volume based  participate
## participate in the market at a specified rate 
def _gen_participate_algo ():
    return  {
        'Algorithm': 'PARTICIPATE',
        '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
        '9111': random.choice([1,50]),         ## IOS-VolumnLimit , 1-50, participate rate
        '9007': random.choice([0,1]),          ## IOS-SOR
      }
def _gen_participate_cleanup(price=0):
    base = _gen_is_algo()
    base['8057'] = price                   ## cleanup price
    base['8211'] = random.choice([1,100])  ## cleanup vol limit
    base['8210'] = random.choice([1,100])  ## cleanup per% limit
    return base

###############################
## scales the rate of participation according to attractivieness of current price
## scaling hte rate up and down with changes in stock price
def _gen_scaling_algo():
     return {
            'Algorithm': 'SCALING',
            '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
            '9007': random.choice([0,1]),          ## IOS-SOR
            '8094': random.choice(['1','2','3','4','5','6','7']),  ## IOS-Benchmark Type / Arrival
            '8061': random.choice(['1','2','3']),  ## execution view
            '8047': random.choice([1,10]),         ## min val
            '8849': random.choice([1,10]),         ## start val
            '8046': random.choice([10,50]),         ## max vol
         }

def _gen_scaling_cleanup(price=0):
    base = _gen_scaling_algo()
    base['8057'] = price                   ## cleanup price
    base['8211'] = random.choice([1,100])  ## cleanup vol limit
    base['8210'] = random.choice([1,100])  ## cleanup per% limit
    return base

############################
## volume based variance on dscaling
def _gen_pwp_algo():
     return {
            'Algorithm': 'PWP',
            '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
            '9007': random.choice([0,1]),          ## IOS-SOR
            '8094': random.choice(['1','2','3','4','5','6','7']),  ## IOS-Benchmark Type / Arrival
            '8061': random.choice(['1','2','3']),  ## execution view
            '8047': random.choice([1,10]),         ## min val
            '8849': random.choice([1,10]),         ## start val
            '8046': random.choice([10,99]),         ## max vol
            ## PWP bencharmk
            '8148': random.choice([1,50])
         }
def _gen_pwp_cleanup(price=0):
    base = _gen_pwp_algo()
    base['8057'] = price                   ## cleanup price
    base['8211'] = random.choice([1,100])  ## cleanup vol limit
    base['8210'] = random.choice([1,100])  ## cleanup per% limit
    return base

############################
## 
def _gen_peg_algo():
     ret =  {
            'Algorithm': 'PEG',
            '8080': random.choice(['1','2']),       ## IOS-PegStyle, passive touch, plus+1 
            '9007': random.choice([0,1]),           ## IOS-SOR
            '8081': random.choice(['0','1','5','3']),  ## Display Type
        }
     ## auto
     if ret['8081'] != '0':
         ret['8110'] = random.choice([10,20])
     return ret

############################
## 
def _gen_steal_algo():
     ret =  {
            'Algorithm': 'STEALTH',
            '8053': random.choice([10,20]),      ## min takeout size
            '9007': random.choice([0,1]),          ## IOS-SOR
        }
     ## leavetype leaveSize
     return ret

############################
## 
def _gen_pegsteal_algo():
     ret =  {
            'Algorithm': 'PEGSTEALTH',
            '8080': random.choice(['1','2']),       ## IOS-PegStyle, passive touch, plus+1 
            '8042': random.choice(['1','2','3']),   ## IOS-Style, passive,neutral,aggressive
            '9007': random.choice([0,1]),           ## IOS-SOR
       }
     ## leavetype leaveSize
     return ret

############################
## 
def _gen_iceberg_algo():
     ret =  {
            'Algorithm': 'ICEBERG',
            '8110': random.choice([10,20]),     ## display size
            '9007': random.choice([0,1]),       ## IOS-SOR
       }
     ## leavetype leaveSize
     return ret
############################
## 
def _gen_smallcap_algo():
     ret =  {
            'Algorithm': 'SMALLCAP',
            '8042': random.choice(['1','2','3']),  ## IOS-Style, passive,neutral,aggressive
            '9112': random.choice([1,100]),        ## display size
            '9007': random.choice([0,1]),          ## IOS-SOR
            '8143': random.choice(['1','2']),      ## IOS-RelLimitBench market/sector
      }
     ## leavetype leaveSize
     return ret

############################
## 
def _gen_smartdma_algo():
     ret =  {
            'Algorithm': 'SMARTDMA',
            '8110': random.choice([1,100]),        ## display size
            '9007': random.choice([0,1]),          ## IOS-SOR
      }
     ## leavetype leaveSize
     return ret
############################
## 
def _gen_stoploss_algo(price=0):
     ret =  {
            'Algorithm': 'STOPLOSS',
            '9007': random.choice([0,1]),          ## IOS-SOR
            '8099': price,
      }
     ## leavetype leaveSize
     return ret
############################
def _gen_sigmax_algo(price=0):
     ret =  {
            'Algorithm': 'SIGMAX',
            '9018': random.choice(['M','P','R']),
      }
     ## leavetype leaveSize
     return ret

####################################
## 1 - CP 2 - onopen, 3 - onclose, 4 - SonarDark
def _gen_custom_algo(price=0):
     ret =  {
            'Algorithm': 'CUSTOM',
            '9098': random.choice(['2','3','4']),
      }
     ## leavetype leaveSize
     return ret

class Test_IOS_VWAP:
    """ test IOS/VWAP with valid params. """

    scenarios = []

    ## vwap
    ios_algos = [_gen_vwap_algo() for i in range(10)]
    ## vwap with cleanup
    ios_algos += [_gen_vwap_cleanup() for i in range(10)]
    ## twap
    ios_algos += [_gen_twap_algo() for i in range(10)]
    ## twap with cleanup
    ios_algos += [_gen_twap_cleanup() for i in range(10)]
    ## IS 
    ios_algos += [_gen_is_algo() for i in range(10)]
    ## IS wiht cleanup
    ios_algos += [_gen_is_cleanup() for i in range(10)]
    ## participate 
    ios_algos += [_gen_participate_algo() for i in range(10)]
    ## IS wiht cleanup
    ios_algos += [_gen_participate_cleanup() for i in range(10)]
    ## scaling 
    ios_algos += [_gen_scaling_algo() for i in range(10)]
    ## scaling wiht cleanup
    ios_algos += [_gen_scaling_cleanup() for i in range(10)]
    ## PWP 
    ios_algos += [_gen_pwp_algo() for i in range(10)]
    ## PWP wiht cleanup
    ios_algos += [_gen_pwp_cleanup() for i in range(10)]
    ## peg
    ios_algos += [_gen_peg_algo() for i in range(5)]
    ## stealth
    ios_algos += [_gen_steal_algo() for i in range(5)]
    ## stealth
    ios_algos += [_gen_pegsteal_algo() for i in range(5)]
    ## iceberg
    ios_algos += [_gen_iceberg_algo() for i in range(5)]
    ## smallcap
    ios_algos += [_gen_smallcap_algo() for i in range(5)]
    ## smartdma
    ios_algos += [_gen_smartdma_algo() for i in range(5)]
    ## stoploss
    ios_algos += [_gen_stoploss_algo() for i in range(3)]
    ## sigmax
    ios_algos += [_gen_sigmax_algo() for i in range(3)]
    ## custom -- CP, ONOPEN, ONCLOSE, SONARDARK
    ios_algos += [_gen_custom_algo() for i in range(5)]

    ## test session
    test_session = "PTIRESS"

    for side in ("Buy","Sell","Sell Short"):
        for test_client in test_clients:
            for algo in ios_algos:
                client = test_client.copy()
                client.update({'side': side, 'algo': algo})
                scenarios.append(client)

    def test_new_amend_cancel(self,side,fixId,starId,algo,symbol_depth):
        """ """
        symbol,quote,cha_quote,attrs = symbol_depth.get_tradable_symbol(build=True)

        last,bid,ask,close = quote['last'],quote['bid']['bid'],quote['ask']['ask'],quote['close']

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
                      "Allocs": [{"AllocAccount":"DAVE_BOOK","AllocShares":qty}],
                      ## start/end time
                      "EffectiveTime": start_time,
                      "ExpireTime": end_time,
                      "Currency": "AUD",
                      }
                }

        order['extra'].update(algo)
        ## set algo cleanup price as order price.
        if '8057' in order['extra']:
            order['extra']['8057'] = price_pass

        ## set stoploss price
        if '8099' in order['extra']:
            order['extra']['8099'] = price_pass

        pprint(order)

        test_order = FIXOrder(self.test_session,order)

        ## check session status
        status = test_order.session_status
        assert status['loggedon'] and status['enabled']

        ## submit new order
        clOrdId, ers = test_order.new()
        assert len(ers) == 1,ers
        ########################
        ## received oma orderId
        assert 'OrderID' in ers[0]
        assert ers[0]['MsgType'] == "ExecutionReport"
        assert ers[0]['OrdStatus'] == "New"
        assert ers[0]['ExecTransType'] == "New"

        #pytest.set_trace()
        gevent.sleep(10)
        ##################################
        ## amend order aggressive, qty up
        clOrdId, ers = test_order.amend(qty=order['qty'] + 2000,
                                        price=price_aggr,
                                        expected_num_msg=2)
        assert len(ers) == 2, ers
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
        assert len(ers) == 2, ers

        assert ers[0]['MsgType'] == "ExecutionReport"
        assert ers[0]["OrdStatus"] == "Pending Cancel"
        assert ers[0]["ExecType"] == "Pending Cancel"

        assert ers[1]['MsgType'] == "ExecutionReport"
        assert ers[1]["OrdStatus"] == "Canceled"
        assert ers[1]["ExecType"] == "Canceled"

