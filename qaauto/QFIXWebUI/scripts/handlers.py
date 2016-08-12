import logging
import tornado

class MainHandler(tornado.web.RequestHandler):

    def initialize(self):
        """ """

    def get(self):
        self.write("Hello, world")
