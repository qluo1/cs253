from pprint import pprint
from conf import settings
import gevent
import zerorpc
import pyfix42
from datetime import datetime
from utils import SeqNumber

server_api = zerorpc.Client(settings.ORDER_API_ENDPOINT)
seqNum = SeqNumber(settings.TMP_DIR,"test")


class MessageListener(object):
    """ """
    def __init__(self, queue):
        """ """
        self.queue = queue
    def on_message(self,message):
        """ """
        try:
            msg = pyfix42.parse(message['message'])[0]
            pprint(msg)
            if msg['MsgType'] != 'NewOrderSingle':
                self.queue.put(msg)
        except Exception,e:
            print e

class Test_Order():
    """ """

    def test_check_session(self):
        """ """
        res = server_api.check_session_status("APOLLO.TEST")
        assert res
        print res


    def test_new_order_single_ITGAU(self):
        """ """
        ##setup listener
        queue = gevent.queue.Queue()
        listener = MessageListener(queue)
        subscriber = zerorpc.Subscriber(listener)
        subscriber.connect(settings.PUBSUB_ENDPOINT)
        gevent.spawn(subscriber.run)

        msg = {'MsgType'    : 'NewOrderSingle',
               'OrdType'    : 'Limit',
               'TimeInForce': 'Day',
               'Side'       : 'Buy',
               'Symbol'     : 'NAB',
               'Price'      : '25.10',
               'SecurityID' : 'NAB.AX',
               'IDSource'   : 'RIC code',
               'ClOrdID'    : "test_%d" % seqNum.next,
               'OrderQty'   : 109,
               'TransactTime': datetime.utcnow(),
               'OnBehalfOfCompID': 'TEST',
               }

        fix_msg = pyfix42.construct(msg)
        assert server_api.send_fix_order("APOLLO.TEST",fix_msg)
        try:
            res = queue.get(timeout=5)
            print "done"
        except gevent.queue.Empty, e:
            raise RuntimeError("subscriber didn't received anything??")


