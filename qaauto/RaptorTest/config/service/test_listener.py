import cfg
import gevent
import zerorpc
from conf import settings

class Listener(object):
    """ """
    def on_message(self,message):
        """ """
        print message


def run_as_service():
    """ """
    service = Listener()
    subscriber = zerorpc.Subscriber(service)
    subscriber.connect(settings.FIX_PUB_ENDPOINT)
    subscriber.run()

if __name__ == "__main__":
    run_as_service()

