import os
import sys
## GS ETH home
try:
    import jsonrpclib
except ImportError:

    GNS_JSON_RPC = "/gns/mw/lang/python/modules/2.7.2/jsonrpclib-0.1.3-gs1/lib/python2.7/site-packages"
    sys.path.append(GNS_JSON_RPC)
    import jsonrpclib

URL = 'http://dev.etch.site.gs.com:8081'
proxy = jsonrpclib.Server(URL+'/rpc')
proxyBatch = jsonrpclib.MultiCall(proxy)


#def get_om_buildId():
#    """ save and return om buildId. """
#
#
#    try:
#        store_build = proxy.saveBuild(
#            'AUCEL',                ## product
#            version,                ## version
#            version[16],            ## buildsep
#            ENV,                    ## type
#            [ENV,os.getlogin()])    ## tags
#    except jsonrpclib.jsonrpc.ProtocolError,e:
#        store_build = e.message[-1].split("=")[-1]
#
#    return store_build
#
