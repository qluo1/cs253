""" entry point of web app. """
## setup local python path.
import cfg
import tornado
import tornado.httpserver
import tornado.web

from handlers import *

class Application(tornado.web.Application):

    def __init__(self,settings):
        #toc
        handlers = [(r'/',MainHandler,{})]
        tornado.web.Application.__init__(self,handlers,**settings)

if __name__ == "__main__":
    """ """
    from tornado.options import define, options, parse_command_line
    from conf import settings

    parse_command_line()

    define("port", default=settings.PORT, help="run on the given port", type=int)
    define("debug", default=settings.DEBUG, help="debug flag", type=bool)

    app_cfg = settings.APP_SETTINGS

    if options.debug:
        print "running in debug mode"
        app_cfg.update(dict(
            autoreload=True,
            static_hash_cache=False,
            compiled_template_cache=False
            )
        )

    app = Application(app_cfg)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

