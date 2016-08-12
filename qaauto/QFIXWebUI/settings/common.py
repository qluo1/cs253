import os

cur_dir = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(cur_dir)
## all python backend
APP_DIR = os.path.join(PROJ_ROOT,"py")
## all js front end
JS_DIR = os.path.join(PROJ_ROOT,"js")
## 
STATIC_DIR = os.path.join(PROJ_ROOT,"static")
TEMPLATE_DIR = os.path.join(APP_DIR,"template")


