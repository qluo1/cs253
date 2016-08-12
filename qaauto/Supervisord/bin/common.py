import sys,os,types
## add libs in python path
LIBS = ['/gns/mw/lang/python/modules/2.7.2/supervisor-3.1.3/lib/python2.7/site-packages',
        '/gns/mw/lang/python/modules/2.7.2/meld3-1.0.2/lib/python2.7/site-packages',
        '/gns/mw/lang/python/modules/2.7.2/setuptools-19.7/lib/python2.7/site-packages']
for LIB in LIBS:
    if LIB not in sys.path:
        sys.path.append(LIB)

# set supervisor as  module
p =  os.path.join('/gns/mw/lang/python/modules/2.7.2/supervisor-3.1.3/lib/python2.7/site-packages','supervisor')
if p not in sys.path:
    sys.path.append(p)
ie = os.path.exists(os.path.join(p,'__init__.py'));
m = not ie and sys.modules.setdefault('supervisor',types.ModuleType('supervisor'));
mp = (m or []) and m.__dict__.setdefault('__path__',[]);
(p not in mp) and mp.append(p)

