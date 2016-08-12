import os
import sys
import traceback
from collections import OrderedDict
from datetime import date
import logging
import cfg
import gevent
import zerorpc
from conf import settings

from redislite import Redis

from pyfix42 import SOH

log = logging.getLogger("redisdb")


SET_KEY = "all_dates"

class Listener(object):
    """ """

    def __init__(self,rdb):
        """ """
        self.rdb_ = rdb

    def on_message(self,message):
        """ """
        try:
            assert isinstance(message,dict)
            ## message published out of myapp i.e. quickfix app
            log.debug("FIX: %s" % message)
            method,session, msg = message['method'],message['session'],message['message']

            today = date.today().strftime("%y%m%d")

            with self.rdb_.pipeline() as pipeline:
                if not self.rdb_.sismember(SET_KEY,today):
                    pipeline.sadd(SET_KEY,today)

                tags = msg.split(SOH)

                tags = msg.split(SOH)
                assert tags[-1] == ''
                tags = tags[:-1]
                print tags
                print "==="
                res = OrderedDict([tag.split("=",1) for tag in tags])

                clOrdId = res['11']
                origClOrdId = res.get('41',"")
                msgType = res['35']

                hskey = "%s:%s:%s" % (msgType,clOrdId,origClOrdId)

                pipeline.hmset(today,{hskey:res})
                pipeline.execute()

        except Exception,e:
            exc_type,exc_value,exc_tb = sys.exc_info()
            tb = traceback.extract_tb(exc_tb)

            error = "failed to process: %s, with error: %s, tb: %s" %(message,e,tb)
            print error
            log.error(error)


class APIServer(zerorpc.Server):
    """ """

    def init(self,rdb):
        """ """
        self.rdb_ = rdb

    @zerorpc.stream
    def gen_messages(self,**kw):
        """ """
        today = date.today().strftime("%y%m%d")
        _date = kw.get("date",today)
        match = kw.get("match")
        if match:
            for item in self.rdb_.hscan_iter(_date,match=match):
                yield item
        else:
            for item in self.rdb_.hscan_iter(_date):
                yield item

    def list_summary(self,**kw):
        """ """
        _date = kw.get("date")
        members = self.rdb_.smembers(SET_KEY)

        print members
        res = {}
        for mem in members:
            res[mem] = self.rdb_.hlen(mem)
        return res


def run_as_service():
    """ """
    dbfile = os.path.join(settings.TMP_DIR,"fixdb.db")
    rdb = Redis(dbfile)
    service = Listener(rdb)
    subscriber = zerorpc.Subscriber(service)
    subscriber.connect(settings.PUBSUB_ENDPOINT)
    gevent.spawn(subscriber.run)

    server = APIServer()
    server.init(rdb)
    server.bind(settings.RDB_API_ENDPOINT)
    server.run()

if __name__ == "__main__":
    run_as_service()

