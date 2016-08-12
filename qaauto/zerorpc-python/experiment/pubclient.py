
from zerorpc import zmq
import zerorpc
import threading

endpoint = "ipc://test_pub"

endpoint = "tcp://localhost:20161"


client = zerorpc.Client()
client.connect(endpoint)


#for msg in client.on_message():
#    print msg
#

for msg in client.on_viking():
    print msg

