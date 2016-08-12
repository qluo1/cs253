""" generic client orderID generator. """

import sys
from datetime import datetime,timedelta
import base62

from conf import settings

import redis
rdb = redis.Redis(host=settings.REDIS_HOST,port=settings.REDIS_PORT,db=settings.REDIS_DB)

def clientOrderId(client, **kw):
    """ generate client orderId for specified client.

    prefix: will be FA8/xxx 
    compact: xxx will be base62_encode
    """
    ## default add prefix to get unique clOrdID
    prefix = kw.get("prefix",True)
    compact = kw.get("compact",True)
    client = str(client)
    today = datetime.now().strftime("%y%m%d")

    today_clientId = "%s-%s" % (today,client)
    client_order_id = rdb.incr(today_clientId)

    if not rdb.ttl(today_clientId):
        rdb.expireat(today_clientId, datetime.now() + timedelta(days=1))

    ## support multiday order as well as clientOrderId for multiday
    day_of_year = datetime.now().timetuple().tm_yday
    if prefix:
        if compact:
            return "%s/%s/%s" % (client,base62.base62_encode(client_order_id),base62.base62_encode(day_of_year))
        else:
            return "%s/%d/%s" % (client,client_order_id,base62.base62_encode(day_of_year))
    if compact:
        return base62.base62_encode(client_order_id)

    return client_order_id



if __name__ == "__main__":
    """ test clientOrderID"""
    ## don't refresh 
    #print clientOrderId("testc",refresh=True)
    for o in range(100):

        #print clientOrderId("VFMC",compact=True)

        #print clientOrderId("test")

        print clientOrderId("A2L")

