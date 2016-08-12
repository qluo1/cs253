import socket
import signal
import os
import sys
import argparse
from threading import Thread
from time import sleep

parser = argparse.ArgumentParser()
parser.add_argument('--incoming-binding-host')
parser.add_argument('--incoming-binding-port')
parser.add_argument('--outgoing-binding-host')
parser.add_argument('--outgoing-binding-port')
parser.add_argument('--outgoing-connecting-host')
parser.add_argument('--outgoing-connecting-port')
args = parser.parse_args()

assert args.incoming_binding_port is not None
assert args.outgoing_connecting_host is not None
assert args.outgoing_connecting_port is not None

incoming_binding = ('' if args.incoming_binding_host is None else args.incoming_binding_host, args.incoming_binding_port)
outgoing_binding = None if (args.outgoing_binding_host is None or args.outgoing_binding_port is None) else (args.outgoing_binding_host, args.outgoing_binding_port)
outgoing_connecting = (args.outgoing_connecting_host, args.outgoing_connecting_port)

# Arrowhead message format
ESP_HEADER_LEN = 72
DATA_LEN_OFFSET = 43

incoming_socket = socket.socket()
outgoing_socket = socket.socket()

incoming_socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
outgoing_socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

# To avoid the address in use problem
incoming_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
outgoing_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

incoming_socket.bind(incoming_binding)
incoming_socket.listen(1)
incoming_socket, addr = incoming_socket.accept()
print 'Connected by', addr

if outgoing_binding is not None:
    outgoing_socket.bind(outgoing_binding)
outgoing_socket.connect(outgoing_connecting)

# Use to detect if both threads are connected
connected = True

def __upThread():
    print '__upThread started, incoming -> outgoing'
    while True:
        msg = __recvMsg(incoming_socket)
        __sendMsg(outgoing_socket, msg)


def __downThread():
    print '__downThread started, outgoing -> incoming'
    while True:
        msg = __recvMsg(outgoing_socket)
        __sendMsg(incoming_socket, msg)

def __recvMsg(socket):
    msg1 = ''
    while len(msg1) < ESP_HEADER_LEN:
        chunk = socket.recv(ESP_HEADER_LEN - len(msg1))
        if chunk == '':
            connected = False
            raise RuntimeError("socket connection broken")
        msg1 = msg1 + chunk
    
    dataLen = int(msg1[DATA_LEN_OFFSET: DATA_LEN_OFFSET + 5])
    msg2 = ''
    while len(msg2) < dataLen:
        chunk = socket.recv(dataLen - len(msg2))
        if chunk == '':
            connected = False
            raise RuntimeError("socket connection broken")
        msg2 = msg2 + chunk

    return msg1 + msg2
    
def __sendMsg(socket, msg):
    msgLen = len(msg)
    totalsent = 0
    while totalsent < msgLen:
        sent = socket.send(msg[totalsent:])
        if sent == 0:
            connected = False
            raise RuntimeError("socket connection broken")
        totalsent += sent

up_thread = Thread(target=__upThread)
up_thread.setDaemon(True)

down_thread = Thread(target=__downThread)
down_thread.setDaemon(True)

up_thread.start()
down_thread.start()

def sigint_handler(signum, frame):
    print 'SIGINT received, closing sockets...'
    incoming_socket.close()
    outgoing_socket.close()
    sys.exit(0)
    
signal.signal(signal.SIGINT, sigint_handler)

while True:
    if not connected:
        print 'Socket is broken, exiting...'
        incoming_socket.close()
        outgoing_socket.close()
        sys.exit(0)
    sleep(1)
