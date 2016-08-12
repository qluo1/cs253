""" remote QFIXService configuration for local tesing session. 


"""
from common import *
import uuid

TIMEZONE = "Australia/Sydney"

## tornado config
PORT=8808
DEBUG=True
## 
TEMPLATE_DIR = os.path.join(WEB_ROOT,"template")
STATIC_DIR = os.path.join(WEB_ROOT,"static")

APP_SETTINGS = dict(
    cookie_secret=str(uuid.uuid4()),
    login_url="auth/login",
    template_path=TEMPLATE_DIR,
    static_path=STATIC_DIR,
    xsrf_cookies=True,
)

## om2 runtime dir
RUNTIME_DIR = "/local/data/home/eqtdata/sandbox/luosam/works/projects/QA/TestCases/autorunner/runtime"

