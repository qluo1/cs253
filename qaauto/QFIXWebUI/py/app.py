import cfg
from conf import settings
import flask
import engineio
import socketio

app = flask.Flask(__name__,**settings.APP_SETTINGS)

@app.route("/")
def index():
    return "hello world"

if __name__ == "__main__":
    """ run a debug server. """
    app.run(settings.HOST,settings.PORT,settings.DEBUG)

