
from conf import settings
import zerorpc
#REMOTE_API_URL = "tcp://d153578-002.dc.gs.com:39010"
REMOTE_API_URL = "tcp://d48965-004.dc.gs.com:39010"

#service =  zerorpc.Client(settings.API_URL)
service =  zerorpc.Client(REMOTE_API_URL)

def test_list_asx_symbol():
    """ """
    ret = service.list_asx_symbols()
    assert ret
    print len(ret)

def test_list_chia_symbol():
    """ """
    ret = service.list_chia_symbols()
    assert ret
    print len(ret)

def test_list_asx_stock():
    """ """
    ret = service.list_asx_stocks()
    assert ret
    print len(ret)

def test_list_asx_warrant():
    """ """
    ret = service.list_asx_warrants()
    assert ret
    print len(ret)


def test_symbol_attrs():
    """ """
    ret = service.query_symbol_attrs("CBA.AX")
    assert ret
    print ret

    ret = service.query_symbol_attrs("CBA.CHA")
    assert ret
    print ret
    ret = service.query_symbol_attrs("BHP.AX")
    assert ret
    print ret

def test_list_symbol_with_mxq():
    """ """
    ret = service.list_symbol_with_mxq()
    assert ret
    print ret
def test_list_symbol_with_mxq():
    """ """
    ret = service.list_symbol_with_mxq()
    assert ret
    print ret

def test_list_symbol_without_mxq():
    """ """
    ret = service.list_symbol_with_mxq(False)
    assert ret
    print ret



def test_regdata():

    print "firm by xref"
    print len(service.get_firms(qualifier="xref"))
    print "client by xref"
    print len(service.get_clients(qualifier="xref"))
    print "wholeSaleIndicator flagged by xref"
    print len(service.get_wholeIndicator_flagged(qualifier="xref"))
    print "orderOrigin flagged by xref"
    print len(service.get_ordOrigin_flagged(qualifier="xref"))
    print "intermediary flagged by xref"
    print len(service.get_intermediary_flagged(qualifier="xref"))


    print " ========== OEID ============"
    print "firm "
    print len(service.get_firms(qualifier="oeid"))
    print "client "
    print len(service.get_clients(qualifier="oeid"))
    print "wholeSaleIndicator flagged "
    print len(service.get_wholeIndicator_flagged(qualifier="oeid"))
    print "orderOrigin flagged "
    print len(service.get_ordOrigin_flagged(qualifier="oeid"))
    print "intermediary flagged "
    print len(service.get_intermediary_flagged(qualifier="oeid"))


    print " ========== STARID ============"
    print "firm "
    print len(service.get_firms(qualifier="starid"))
    print "client "
    print len(service.get_clients(qualifier="starid"))
    print "wholeSaleIndicator flagged "
    print len(service.get_wholeIndicator_flagged(qualifier="starid"))
    print "orderOrigin flagged "
    print len(service.get_ordOrigin_flagged(qualifier="starid"))
    print "intermediary flagged "
    print len(service.get_intermediary_flagged(qualifier="starid"))

    print " ========== TAM ============"
    print "firm "
    print len(service.get_firms(qualifier="tam"))
    print "client "
    print len(service.get_clients(qualifier="tam"))
    print "wholeSaleIndicator flagged "
    print len(service.get_wholeIndicator_flagged(qualifier="tam"))
    print "orderOrigin flagged "
    print len(service.get_ordOrigin_flagged(qualifier="tam"))
    print "intermediary flagged "
    print len(service.get_intermediary_flagged(qualifier="tam"))


    print "query regdata by oeid"
    for i in service.get_wholeIndicator_flagged(qualifier="oeid"):
        print i, service.get_regdata_byKey(i,qualifier="oeid")


    print "query OP6"
    print service.get_regdata_byKey("FC1")

    print "si data by xref "
    for xref in  ('ZI8','DL72', 'FC3','D02'):
        print service.get_si_byXref(xref)

