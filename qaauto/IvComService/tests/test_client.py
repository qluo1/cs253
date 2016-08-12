""" test client for subscriber. """
import zerorpc
import zmq
import gevent
import msgpack

PUB_ENDPOINT = "tcp://localhost:29010"

import logging

logging.basicConfig(filename="testclient.log",level=logging.DEBUG)

def run_sub_raw():
    """ test raw zmq client , receive all published message."""
    context = zmq.Context()
    sock = context.socket(zmq.SUB)
    sock.connect(PUB_ENDPOINT)
    sock.setsockopt(zmq.SUBSCRIBE,"")

    unpacker = msgpack.Unpacker(object_hook = zerorpc.events.decode_datetime)

    while True:
        data = sock.recv()
        unpacker.feed(data)
        msg = unpacker.unpack()
        print msg
        gevent.sleep(0)

#run_sub_raw()

class SubClient():
    """ test client implement of zerorpc callback. """

    def onReplication(self,message):
        """ """
        #print message
    def onDSS(self,message):
        """ """
        #print message
    def onImagelive(self,message):
        """ """
        #print message

    def onVkASX(self,message):
        """ """
        print message
    def onVkCXA(self,message):
        """ """
        print message

client = SubClient()
subscriber = zerorpc.Subscriber(methods={'QAEAUCEA->replication': client.onReplication,
                                         'QAEAUCEA->QAAUCE_Listener': client.onDSS,
                                         'imageliveserver-QAEAUCEA': client.onImagelive,
                                         'QAECXAA->TESTA': client.onVkCXA,
                                         'QAEASXA->TESTC': client.onVkASX,
                                         })
subscriber.connect(PUB_ENDPOINT)
subscriber.run()

