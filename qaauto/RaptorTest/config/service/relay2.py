import socket
import signal
import os
import sys
from threading import Thread
from time import sleep

#(RAW_IP, RAW_PORT) = ('3.3.3.1', 9445)
#(OUTGOING_LOCAL_IP, OUTGOING_LOCAL_PORT) = ('2.2.2.2', 11030)
(INCOMING_LOCAL_HOST, INCOMING_LOCAL_PORT) = ('5.5.5.2', 9446)
(TEST_IP, TEST_PORT) = ('10.100.193.40', 9446)

ESP_HEADER_LEN = 72
DATA_LEN_OFFSET = 43

incoming_socket = socket.socket()
outgoing_socket = socket.socket()

incoming_socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
outgoing_socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

incoming_socket.bind((INCOMING_LOCAL_HOST, INCOMING_LOCAL_PORT))
incoming_socket.listen(1)
incoming_socket, addr = incoming_socket.accept()
print 'Connected by', addr
#while True:
#    try:
#        incoming_socket.connect((TEST_IP, TEST_PORT))
#    except socket.error:
#        print 'Connection error, trying again in 5 sec'
#    sleep(5)

#outgoing_socket.bind((OUTGOING_LOCAL_IP, OUTGOING_LOCAL_PORT))
outgoing_socket.connect((TEST_IP, TEST_PORT))


def __upThread():
    print '__upThread started, incoming -> outgoing'
    while True:
        msg = __recvMsg(incoming_socket)
        __sendMsg(outgoing_socket, msg)
        pass


def __downThread():
    print '__downThread started, outgoing -> incoming'
    while True:
        msg = __recvMsg(outgoing_socket)
        __sendMsg(incoming_socket, msg)
        pass

def __recvMsg(socket):
    msg1 = ''
    while len(msg1) < ESP_HEADER_LEN:
        chunk = socket.recv(ESP_HEADER_LEN - len(msg1))
        if chunk == '':
            raise RuntimeError("socket connection broken")
        msg1 = msg1 + chunk
    
    dataLen = int(msg1[DATA_LEN_OFFSET: DATA_LEN_OFFSET + 5])
    msg2 = ''
    while len(msg2) < dataLen:
        chunk = socket.recv(dataLen - len(msg2))
        if chunk == '':
            raise RuntimeError("socket connection broken")
        msg2 = msg2 + chunk

    return msg1 + msg2
    
def __sendMsg(socket, msg):
    msgLen = len(msg)
    totalsent = 0
    while totalsent < msgLen:
        sent = socket.send(msg[totalsent:])
        if sent == 0:
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
    pass
    
