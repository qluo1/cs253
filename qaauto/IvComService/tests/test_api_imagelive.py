"""test call for create imageLive view for OM2.

"""
ORDER_ENDPOINT = "tcp://d127601-081.dc.gs.com:29011"

import zerorpc

from viewCreator import ViewCreator
def run_create_view():
    """ """


    service = zerorpc.Client()
    service.connect(ORDER_ENDPOINT)

    ## list handler
    sessions =  service.list_sessions()

    print sessions
    providerName = "imageliveserver-QAEAUCEA"
    assert providerName in sessions
    try:
        service.cancelImgLiveView(providerName, "Test_orderView")
    except Exception,e:
        pass
    # some views to test things -- don't want to rely on external ones
    v = ViewCreator("Test_orderView")
    v.addTypeAndFields("order", ["currentOrder", "currentOrder/orderStatusData", "currentOrder/relatedEntityIndexes"])
    assert service.createImgLiveView(providerName, *v())

    try:
        service.cancelImgLiveView(providerName, "Test_executionView")
    except Exception,e:
        pass

    v = ViewCreator("Test_executionView")
    v.addTypeAndFields("execution", ["currentExecution","previousExecution"])
    assert service.createImgLiveView(providerName, *v())

run_create_view()

