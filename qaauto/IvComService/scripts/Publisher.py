""" implement zerorpc publisher.

zerorpc publisher with gevent hub  must be within same thread.

therefore, create a self serving thread for handle all publishing tasks.

the purpose of this class is to make client side easy.
"""
import os
import sys
import traceback
from threading import Thread
import logging
import gevent
import zerorpc
import gevent.queue as Queue
## enrich published message 
from utils import enum_lookup, enrich_enum

log = logging.getLogger(__name__)

class OMPublisher(Thread):

    def __init__(self, endpoints={}):
        """ init publisher with endponts.

        endpoints: key is method_name, value is zmq endpoint url.

        endponts can also registered dynamically.

        publisher shall publish message to the named method.
        """
        log.info("init publisher endpoints: %s" % endpoints)
        super(OMPublisher,self).__init__()
        self.queue_ = Queue.Queue()
        #self.queue_ = Queue.PriorityQueue()
        self.daemon = False
        self.running_ = False
        assert isinstance(endpoints,dict)
        self.endpoints_ = endpoints

    def register(self,name,url):
        """ dynamic register a named_method to an endpoint. """

        if name not in self.endpoints_:
            self.endpoints_[name] = url
        else:
            log.error("name: %s already exist." % name)

    def start(self):
        if self.running_ == False:
            self.running_= True
            super(OMPublisher,self).start()
        log.info("isalive %s" % self.isAlive())

    def publish(self,method, message):
        """ publish message to a named endpoint. """

        if method in self.endpoints_.keys():
            self.queue_.put((method, message))
        else:
            log.error("method name:%s  not registered. %s" % (method,self.endpoints_))

    def run(self):
        """ create zerorpc publishing within local thread context."""
        try:
            pubs = {}
            for name,url in self.endpoints_.iteritems():
                log.info("binding name: %s,  to endpoint:%s" % (name,url))
                pubs[name] = zerorpc.Publisher()
                pubs[name].connect(url)

            log.info("publisher initial with endpoints: %s" % pubs)
            while self.running_:
                ## update pubs dynamically
                for name in list(set(self.endpoints_.keys()) - set(pubs.keys())):
                    ## got new registered endpoint
                    pubs[name] = zerorpc.Publisher()
                    log.info("add binding %s: to %s" %(name,self.endpoints_[name]))
                    pubs[name].connect(self.endpoints_[name])
                    #log.debug("pubs: %s" % pubs)
                try:
                    ## get method_name and data
                    name,data = self.queue_.get(timeout=0.5)
                    log.debug("publishing %d, %s, %s" % (self.queue_.qsize(),name,data))
                    pub = pubs[name]

                    ##  enrich dss message
                    if isinstance(data,dict) and 'message' in data and 'currentOrder' in data['message']:
                        enrich_enum('OrderExecutionUpdate',data['message'])
                    method = getattr(pub,name)
                    ## publish the data on the named_method.
                    log.debug("call method: %s, with data: %s"  % (name,data))
                    method(data)
                except Queue.Empty:
                    pass
        except Exception,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log.info("failed on process imageLive msg: %s, tb: %s" % \
                        (e, traceback.extract_tb(exc_traceback)))

    def stop(self):
        self.running_ = False
        self.join()


if __name__ == "__main__":
    """
    """
    endpoint = 'ipc:///tmp/test_imglive'
    logging.basicConfig(filename="./testpublisher.log",level=logging.DEBUG)

    publisher = OMPublisher({'on_imagelive': endpoint})
    publisher.start()

    ## test client
    class Client:
        def on_imagelive(self,item):
            print "received", item

    service = zerorpc.Subscriber(Client())
    service.connect(endpoint)
    gevent.spawn(service.run)

    ## publishing.
    publisher.publish("on_imagelive", "123")
    publisher.publish("on_imagelive",123)
    publisher.publish("on_imagelive",{'a': 123})
    gevent.sleep(3)

    ## continue publishing
    for x in range(1000):
        publisher.publish("on_imagelive",x)

    gevent.sleep(3)
    publisher.stop()
    service.stop()
    service.close()


