import os
import sys
from pprint import pprint
import cfg
from conf import settings
import zmq


class MDTClient(object):
    """ """
    def __init__(self):
        """ """
        context = zmq.Context()
        self.reqSock = context.socket(zmq.REQ)
        self.subSock = context.socket(zmq.SUB)
        self.reqSock.connect(settings.REP_SUB_ENDPOINT)
        self.subSock.connect(settings.PUB_QUOTE_ENDPOINT)
        self.subSock.setsockopt(zmq.SUBSCRIBE, "")
        self.poller = zmq.Poller()
        self.poller.register(self.reqSock, zmq.POLLIN)
        self.poller.register(self.subSock, zmq.POLLIN)

    def subscribe(self, symbol):
        """ """
        #import ipdb;ipdb.set_trace()
        msg = {'symbol': symbol}
        self.reqSock.send_json(msg)

    def watch_quote(self):
        """ """
        while True:

            socks = dict(self.poller.poll(1000))
            out = None

            if socks.get(self.reqSock) == zmq.POLLIN:
                out = self.reqSock.recv_json()
                assert out
            if socks.get(self.subSock) == zmq.POLLIN:
                out = self.subSock.recv_multipart()
                assert out

            if out:
                pprint(out)


if __name__ == "__main__":
    """ """
    if len(sys.argv) < 2:
        print "usage MNDTClient BHP.AX"
        exit(0)

    client = MDTClient()
    print "query symbol: %s" % sys.argv[1]
    client.subscribe(sys.argv[1].upper())
    client.watch_quote()


