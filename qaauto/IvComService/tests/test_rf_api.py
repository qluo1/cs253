"""test call for create imageLive view for OM2.

"""

from datetime import datetime
import time
import os
import zerorpc

from utils import IvComDictHelper


env = os.envrion['SETTINGS_MODULE'].split(".")[-1]

ENDPOINTS = {'QAEAUEA':"tcp://localhost:29011",
             'PPEAUEA':"tcp://localhost:29021",
             }

API_ENDPOINT = ENDPOINTS[env]
api = zerorpc.Client(API_ENDPOINT)

def test_rf_create_order_command():
    """ """
    now = time.time()

    posDupId = datetime.fromtimestamp(now).isoformat()

    test_order = {'serviceOffering': 1, 'allOrNone': False, 'buySell': 1,
                  'externalReferences': [{'tag': 'lC4/4/1o', 'systemName': 'MyIvComRF', 'tagDate': int(now), 'externalObjectIdType': 1}],
                  'orderType': 2, 'productIdType': 2, 'flowSpecificAustralia': {'iosAccountExchangeCrossReference': 'lC4/4/1o'},
                  'limitPrice': 8.01, 'timeInForce': 1,
                  'accounts': [{'accountAliases': [{'accountSynonymType': 4, 'accountSynonym': 'FC4'}],
                      'accountRole': 1, 'accountType': 2, 'entity': 'GSJP'}], 'executionPointOverride': 'SYDE',
                  'commandHeader': {'posDupId': posDupId, 'systemType': 14, 'creatorIdType': 1, 'isPosDup': True,
                      'systemName': 'PlutusChild_DEV', 'creatorId': 'default',
                      'commandTime': int(now)}, 'crossConsent': 2, 'quantity': 100.0, 'productId': 'CCL'}

    ret = api.send_rf_request("engine-%s-requestResponse" % env,"CreateOrderCommand",test_order)
    print  ret

def test_rf_cancel_execution_command():
    """ executionId is mandatory."""
    now = time.time()

    posDupId = datetime.fromtimestamp(now).isoformat()

    #orderId = "QAEAUCEA6820160421O"
    #orderId = "QAEAUCEA6720160421O"
    #execId = "QAEAUCEA3020160421E"
    #execId="QAEAUCEA2920160421E"
    execId="n-3bm-rq-6"
    orderId = "PPEAUCEA9420160421O"

    exRefs =  [{
               "externalObjectIdType": 3,
               "systemName": "SYDE",
               "tag": "1240000032",
               "tagDate": 1461196800
               }]

    test_order = {
                'orderId': orderId,
                'executionId': execId,
                #'externalReferences': exRefs,
                  'commandHeader': {'posDupId': posDupId, 'systemType': 14, 'creatorIdType': 1, 'isPosDup': True,
                      'systemName': 'PlutusChild_DEV', 'creatorId': 'default',
                      'commandTime': int(now)}, }

    ret = api.send_rf_request("engine-%s-requestResponse" % env ,"CancelExecutionCommand",test_order)
    print  ret

