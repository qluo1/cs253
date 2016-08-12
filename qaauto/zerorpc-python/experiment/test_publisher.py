import os
import sys
import time

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CUR_DIR)

if PARENT_DIR not in sys.path:
    sys.path.insert(0,PARENT_DIR)


from threading import Thread
import Queue
import zerorpc
import gevent
import gevent.queue as Queue
IMGLIVE_PUBSUB_ENDPOINT = "tcp://localhost:20182"

endpoint = 'ipc:///tmp/test_imglive'
endpoint = IMGLIVE_PUBSUB_ENDPOINT

class Client:
    def on_imagelive(self,item):
        print "received", item

print endpoint
service = zerorpc.Subscriber(Client())
service.connect(endpoint)
worker = gevent.spawn(service.run)

#gevent.sleep(100)
gevent.joinall([worker])

