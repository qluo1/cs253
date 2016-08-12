from om2API import  OM2API

from utils import IvComDictHelper
api = OM2API()

import time
from datetime import datetime

def test_construct_order_accept():
    """ """
    childOrderId = "QAEAUCEA1420160608O"
    qty = 10

    utcnow = datetime.utcnow()
    now = time.mktime(utcnow.timetuple())
    acceptOrder = {

            'commandHeader': 
                {
                    'commandTime': now,
                    'isPosDup': True,
                    'posDupId': "%s-1" % childOrderId,
                    'systemName': "PlutusSGMX",
                    'creatorId': "bot",
                    'creatorIdType': "External",
                    'systemType': "AlgorithmEngine",
                }
            ,
            'externalReferences': [
                {
                    'systemName': "PlutusSGMX-colt",
                    'tag': "%s-1" % childOrderId,
                    'externalObjectIdType': "FixOrderId",
                },
                {
                    'systemName': "bot",
                    'tag': "0-3e1-rq",
                    'externalObjectIdType': "FixOrderId",
                }
                ],
        'orderId': childOrderId,
        'quantityRemaining': qty,
    }


    command = IvComDictHelper("AcceptOrderCommand")

    for k,v in acceptOrder.iteritems():
        command.set(k,v)

    assert command.msg
    print command.msg
