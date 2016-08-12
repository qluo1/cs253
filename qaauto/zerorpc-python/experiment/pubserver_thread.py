"""
test native thread publish and zerorpc can publish

"""
from nose.tools import assert_raises
import gevent
import sys


from zerorpc import zmq
import zerorpc
import threading

endpoint = "ipc://test_pub"


class MySrv(zerorpc.Server):

    subscribers_ = set()

    @zerorpc.stream
    def on_message(self):
        print "on_message"
        try:
            print "try"
            queue = gevent.queue.Queue()
            self.subscribers_.add(queue)
            print "added"

            for msg in queue:
                print "yield",msg
                yield msg
        finally:
            print "finally"
            self.subscribers_.remove(queue)



    def _publish(self, msg):
        print "publish:", self.subscribers_
        for queue in self.subscribers_:
            if queue.qsize() < 100:
                print "push to queue:", queue.qsize()
                queue.put(msg)

    def _generator(self):
        """
        """
        def gen():
            print "gen"
            count = 0
            while True:
                count +=1
                self._publish(count)
                gevent.sleep(1)

        #gevent.spawn(gen)
        worker = threading.Thread(target=gen)
        worker.setDaemon(True)
        worker.star()

if __name__ == "__main__":

    srv = MySrv()
    srv.bind(endpoint)

    srv._generator()
    srv.run()

