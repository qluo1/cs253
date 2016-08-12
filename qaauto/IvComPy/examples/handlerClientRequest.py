'''
	Author: Luiz Ribeiro (Melbourne Technology Division)
	December, 2015
'''

from IvComPy import *
from handlerClientRequestInterface import HandlerClientRequestInterface
from utils import convert
from threading import Thread

class HandlerClientRequest(HandlerClientRequestInterface):
	'''
		A simple request handler that prints on the screen the messages received by the server.
	'''

	def unregister(self):
		#print 'Unregistering %s' % self.name
		return 0
	

	def onResponse(self, table, msg):
		print 'Received a message (request), what should I do?!'
		print str(msg)
		return None
		# self.executer_.submit(...)

