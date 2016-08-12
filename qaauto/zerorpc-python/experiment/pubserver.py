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
from tests.testutils import *

class MyPubServer(Thread):

    def __init__(self, endpoint = random_ipc_endpoint()):
        """ """
        super(MyPubServer,self).__init__()
        self.endpoing_ = endpoint
        self.queue_ = Queue.Queue()
        self.daemon = False
        self.running_ = True
        self.start()

    def put(self,item):
        self.queue_.put(item)
        gevent.sleep(0.1)

    def run(self):
        """ """
        self.pub_ = zerorpc.Publisher()
        self.pub_.bind(self.endpoing_)

        while self.running_:

            try:

                item = self.queue_.get_nowait()
                #self.pub_.on_test(item)

                method = getattr(self.pub_,"on_test")
                method(item)

            except Queue.Empty:
                gevent.sleep(0.1)


    def stop(self):
        self.running_ = False
        self.join(10)

    def test_subclient(self):
        """ """

        class Client:
            def on_test(self,item):
                print "received", item

        service = zerorpc.Subscriber(Client())

        service.connect(self.endpoing_)
        self.client_ = service
        self.client_worker_ = gevent.spawn(service.run)

    def stop_client(self):

        self.client_.stop()
        self.client_worker_.kill()
        self.client_.close()

if __name__ == "__main__":

    pub = MyPubServer()

    pub.test_subclient()

    pub.put("1234")
    pub.put(123)
    pub.put({'a': 123})

    gevent.sleep(0.5)

    pub.put("after sleep")

    pub.stop()

    print "stopped"


    pub.stop_client()



