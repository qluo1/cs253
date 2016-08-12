import logging
import tornado
import ujson as json

class MainHandler(tornado.web.RequestHandler):

    def initialize(self):
        """ """

    def get(self):
        #self.write("Hello, world")
        self.render("index.html")
## js unittest
class TestJSHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("test.html")


from conf import settings
from helper import current_running_test

class APIHandler(tornado.web.RequestHandler):
    """ for ajax call. """

    def get(self,action):
        """ """

        args = self.request.arguments

        if action == "current_run":

            ret = current_running_test(settings.RUNTIME_DIR)
            print ret

        else:
            ret = {'error': 'unknown action: %s' % action }
        self.set_header('Content-Type','appliation/json')
        self.write(json.dumps(ret))

