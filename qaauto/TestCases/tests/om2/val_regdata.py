""" helper for validate.

-- reg data
-- standing order instruction (si) data

"""
import os
import pytest


from conf import settings

def val_reg_data(orderInst,qualifier,xref,regdata):
    """ validate om2 order instruction with specified reg data ."""

    if regdata:
        assert type(regdata) == dict

    assert orderInst.orderId
    assert orderInst.orderCapacity
    assert orderInst.flowSpecificAustralia

    accounts = orderInst.accounts
    flowSpec = orderInst.flowSpecificAustralia
    capacity = orderInst.orderCapacity
    crossRef = None
    if qualifier == "xref":
        crossRef = flowSpec["iosAccountExchangeCrossReference"]

    if accounts:
        accountSyn = accounts[0]['accountAliases'][0]['accountSynonym']
        accountSynType = accounts[0]['accountAliases'][0]['accountSynonymType']
        ## this is based on am account number, xref might not match accountSynonym
        if accountSynType != "AmAccountNumber":
            assert accountSyn == xref
            assert crossRef.startswith(xref)

    ## capacity
    if regdata:
        if regdata['PARTICIPANTCAPACITY'] == "P":
            assert capacity == "Principal"
        elif regdata['PARTICIPANTCAPACITY'] == 'M':
            assert capacity == "Combined"
        else:
            assert capacity == "Agency"
    else:
        ## no regdata found
        assert capacity == "Agency"

    ## ucpkey
    if regdata and regdata['UCPKEY'] != '0':
        assert flowSpec['australiaUnintentionalCrossPreventionKey'] == int(regdata['UCPKEY'])
    else:
        assert 'australiaUnintentionalCrossPreventionKey' not in flowSpec

    ## orderOrigin
    if regdata and regdata['ASICORIGINOFORDER'] != None:
        assert flowSpec['asicOriginOfOrder'] == regdata['ASICORIGINOFORDER']
    else:
        ## regdata missing
        if regdata is None:
            assert flowSpec['asicOriginOfOrder'] == 'GSJP'
        else:
            assert 'asicOriginOfOrder' not in flowSpec

    ## wholeSaleIndicator
    if regdata and regdata['ASICWHOLESALEINDICATOR'] != '0':
        assert flowSpec['asicWholesaleIndicator'] == True
    else:
        assert 'asicWholesaleIndicator' not in flowSpec

    ## intermediarry
    if regdata and regdata['ASICINTERMEDIARYID'] != '0':
        assert flowSpec['asicIntermediaryId'] == int(regdata['ASICINTERMEDIARYID'])
    else:
        assert 'asicIntermediaryId' not in flowSpec

    print "regdata validated for %s: %s" % (xref,regdata)


from utils import translateOrderType

def val_si_data(order,sor,sor_expect,defaultMxq,xref):
    """ validate si based on so_expect.

    note amend down for JCP, will keep origin BPMV if original orderValue > 120k.

    """
    orderInst = order.orderInst
    tradingAlgorithm = orderInst.tradingAlgorithm
    tradingAlgorithmParameters = orderInst.tradingAlgorithmParameters

    smartRouteConsent = orderInst.smartRouteConsent
    destinationParty = orderInst.destinationParty
    isLeafOrder = orderInst.isLeafOrder
    isSorManagedOrder = orderInst.isSorManagedOrder
    mxq = orderInst.minExecutableQuantity

    ## original order's orderValue
    ## list of [(clOrdid,[er,er]),]
    origOrder = order._clOrdIds[0][1][-1].order
    orderValue = origOrder.quantity * origOrder.limitPrice
    orderQty = orderInst.quantity

    ## patch for PME i.e. prod data
    #if xref == 'OF2' and os.environ['ENV'] == 'PME':
    #    sidata['ASICORIGINOFORDER'] = 'MIXED'

    ## patch JFB  for PME testing
    #if xref == 'JFB':
    #    sor_expect = "BestPriceMinValue"

    if sor_expect =='ASXDirect':
        assert tradingAlgorithm == 'ASXDIRECT'
        assert isLeafOrder == True

    elif sor_expect == 'ASXOnly':
        ## user specified maq
        if sor.endswith('maq'):
            assert translateOrderType(orderInst) == 'ASXOnlyMAQ'
            assert mxq == settings.ORDER_TYPES[sor]['maq']
        else:
            assert translateOrderType(orderInst) == sor_expect

        assert isSorManagedOrder == True

    elif sor_expect == 'BestPriceMinQtyNoLitUni':
        ## user specified maq
        if sor.endswith('maq'):
            assert translateOrderType(orderInst) == 'BPNoLitUniMAQ'
            assert mxq == settings.ORDER_TYPES[sor]['maq']
        else:
           ## if defaultMxq available, for mxq > orderQty, it should be override as orderQty
           if defaultMxq:
               assert translateOrderType(orderInst) == 'BPNoLitUniMAQ'
               assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
           else:
               assert  translateOrderType(orderInst) == 'BPNoLitUni'
        assert isSorManagedOrder == True

    elif sor_expect == 'BestPriceMinQtyUni':
       ## user specified maq
        if sor.endswith('maq'):
            assert translateOrderType(orderInst) == 'BPUniMAQ'
            assert mxq == settings.ORDER_TYPES[sor]['maq']
        else:
            ## if defaultMxq available and sor in minQty sor
            if defaultMxq:
                assert translateOrderType(orderInst) == 'BPUniMAQ'
                assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
            else:
                assert  translateOrderType(orderInst) == 'BPUni'

        assert isSorManagedOrder == True

    elif sor_expect == 'BestPriceMinValue':

        ## check original orderValue > 120k
        if orderValue >= 120000:
            #pytest.set_trace()
            ## no MAQ
            ## user specified maq
            if sor.endswith('maq'):
                assert mxq == settings.ORDER_TYPES[sor]['maq']
                assert  translateOrderType(orderInst) == "BPMVMAQ"
            else:
                ## for minQty sor or defaultMxq available
                if defaultMxq != None: # and sor in ('sor1', 'sor2','sor3','sor4','sor5','sor6','sor7'):
                    assert mxq == int(defaultMxq)
                    assert  translateOrderType(orderInst) == "BPMVMAQ"
                else:
                    assert  translateOrderType(orderInst) == "BPMV"

            assert orderInst.minExecutableNotionalValue == 120000
            assert isSorManagedOrder == True

        else:
            #if sor.endswith('maq'):
            #    assert  translateOrderType(orderInst) == "SYDE-Limit/MAQ"
            #else:
            assert  translateOrderType(orderInst).startswith("SYDE-Limit")
            assert isLeafOrder == True
            assert tradingAlgorithm == 'ASXDIRECT'
    ## for IOC sor
    elif sor_expect == 'BestPriceMinQtyNoLit':
        ## user specified maq
        if sor.endswith('maq'):
            assert translateOrderType(orderInst) == 'BPNoLitMAQ'
            assert mxq == settings.ORDER_TYPES[sor]['maq']
        else:
           ## if defaultMxq available, for mxq > orderQty, it should be override as orderQty
           if defaultMxq:
               assert translateOrderType(orderInst) == 'BPNoLitMAQ'
               assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
           else:
               assert  translateOrderType(orderInst) == 'BPNoLit'
        assert isSorManagedOrder == True
    ## for IOC sor
    elif sor_expect == 'BestPriceMinQty':
       ## user specified maq
        if sor.endswith('maq'):
            assert translateOrderType(orderInst) == 'BPMAQ'
            assert mxq == settings.ORDER_TYPES[sor]['maq']
        else:
            ## if defaultMxq available and sor in minQty sor
            if defaultMxq:
                assert translateOrderType(orderInst) == 'BPMAQ'
                assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
            else:
                assert  translateOrderType(orderInst) == 'BP'
        assert isSorManagedOrder == True
    elif sor_expect == "CENTREPOINT":
        sor_type = translateOrderType(orderInst)
        assert sor_type == sor_expect
    else:
        sor_type = translateOrderType(orderInst)
        #pytest.set_trace()
        #assert False,"unexpected sor_type:%s, inst: %s" % (sor_type,orderInst)
        assert sor_type.split("-")[0] in ("SYDE","CHIA",)


def val_reg_data_2(orderInst,regdata,**kw):
    """ validate om2 order instruction with specified reg data ."""

    if regdata:
        assert type(regdata) == dict

    extra = kw['extra']
    oeid = extra.get("customerOeId")
    starid = extra.get("clientStarId")
    xref = kw.get("xref")
    tam = kw.get("account")
    synthetic = extra.get("syntheticType")

    #import pdb;pdb.set_trace()
    assert orderInst.orderId
    assert orderInst.orderCapacity

    accounts = orderInst.accounts

    assert orderInst.flowSpecificAustralia
    flowSpec = orderInst.flowSpecificAustralia

    if xref:
        assert accounts
        accountSyn = accounts[0]['accountAliases'][0]['accountSynonym']
        accountSynType = accounts[0]['accountAliases'][0]['accountSynonymType']
        crossRef = flowSpec["iosAccountExchangeCrossReference"]
        assert crossRef.startswith(xref)

    if oeid:
        assert orderInst.clientParty
        assert orderInst.clientParty['clientOeId'] == oeid

    if starid:
        assert orderInst.clientParty
        assert orderInst.clientParty['clientStarId'] == starid

    if tam:
        accountSyn = accounts[0]['accountAliases'][0]['accountSynonym']
        accountSynType = accounts[0]['accountAliases'][0]['accountSynonymType']
        assert accountSynType == "AmAccountNumber"
        assert accountSyn == tam

    capacity = orderInst.orderCapacity
    ## capacity
    if regdata['PARTICIPANTCAPACITY'] == "P":
        assert capacity == "Principal"
    elif regdata['PARTICIPANTCAPACITY'] == 'M':
        assert capacity == "Combined"
    else:
        assert capacity == "Agency"

    ## ucpkey
    if 'UCPKEY' in regdata and regdata['UCPKEY'] != '0':
        assert flowSpec['australiaUnintentionalCrossPreventionKey'] == int(regdata['UCPKEY'])
    else:
        assert 'australiaUnintentionalCrossPreventionKey' not in flowSpec

    ## orderOrigin could be missing  i.e. None
    if 'ASICORIGINOFORDER' in regdata:
        if regdata['ASICORIGINOFORDER'] != None:
            assert flowSpec['asicOriginOfOrder'] == regdata['ASICORIGINOFORDER']
        else:
            assert 'asicOriginOfOrder' not in flowSpec
    else:
        ## default or default_p
        if not synthetic:
            assert flowSpec['asicOriginOfOrder'] == 'GSJP'
        else:
            assert 'asicOriginOfOrder' not in flowSpec

    ## wholeSaleIndicator
    if 'ASICWHOLESALEINDICATOR' in regdata and regdata['ASICWHOLESALEINDICATOR'] != '0':
        assert flowSpec['asicWholesaleIndicator'] == True
    else:
        assert 'asicWholesaleIndicator' not in flowSpec

    ## intermediarry
    if 'ASICINTERMEDIARYID' in regdata and regdata['ASICINTERMEDIARYID'] != '0':
        assert flowSpec['asicIntermediaryId'] == int(regdata['ASICINTERMEDIARYID'])
    else:
        assert 'asicIntermediaryId' not in flowSpec

    print "regdata validated for %s, \n order: %s" % (regdata,kw)


def val_si_data_2(order,regdata,defaultMxq,**kw):
    """ validate si based on regdata.

    note amend down for JCP, will keep origin BPMV if original orderValue > 120k.

    """
    #import pdb;pdb.set_trace()
    sor_expect = regdata['SORSTRATEGYOVERRIDE'].upper()
    sor = kw['sor']

    orderInst = order.orderInst
    tradingAlgorithm = orderInst.tradingAlgorithm
    tradingAlgorithmParameters = orderInst.tradingAlgorithmParameters

    smartRouteConsent = orderInst.smartRouteConsent
    destinationParty = orderInst.destinationParty
    isLeafOrder = orderInst.isLeafOrder
    isSorManagedOrder = orderInst.isSorManagedOrder
    mxq = orderInst.minExecutableQuantity

    ## original order's orderValue
    ## list of [(clOrdid,[er,er]),]
    origOrder = order._clOrdIds[0][1][-1].order
    orderValue = origOrder.quantity * origOrder.limitPrice
    orderQty = orderInst.quantity

    ## translate order inst into sor_type
    sor_type = translateOrderType(orderInst).upper()
    ## expect maq
    expect_maq = 'maq' in kw and kw['maq'] > 0 or 'maq' in kw and kw['maq'] == -1 and defaultMxq > 0 
    ## ignore not defaultMaq SOR
    if expect_maq and sor_expect not in ("ASXDIRECT","ASXONLY", "BESTPRICE","BESTPRICEMINVALUE"):
        assert  mxq in (kw['maq'] , defaultMxq)

    if sor_expect =='ASXDIRECT':
        assert tradingAlgorithm == 'ASXDIRECT'
        assert isLeafOrder == True

    elif sor_expect == 'ASXONLY':
        ## user specified maq
        if 'maq' in kw and kw['maq'] > 0:
            assert sor_type == 'ASXONLYMAQ'
        else:
            assert sor_type == sor_expect

        assert isSorManagedOrder == True

    elif sor_expect == 'BESTPRICE':
        ## user specified maq
        if 'maq' in kw and kw['maq'] > 0:
            assert sor_type == 'BPMAQ'
        else:
            assert sor_type =='BP'

    elif sor_expect == "BESTPRICEMINQTY":
        ## user specified maq
        if 'maq' in kw and kw['maq'] > 0:
            assert  sor_type == 'BPMAQ'
            assert mxq == kw['maq']
        else:
            ## if defaultMxq available and sor in minQty sor
            if defaultMxq:
                assert sor_type == 'BPMAQ'
                assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
            else:
                assert  sor_type == 'BP'

    elif sor_expect == 'BESTPRICEMINQTYUNI':
        ## user specified maq
        if 'maq' in kw and kw['maq'] > 0:
            assert  sor_type == 'BPUNIMAQ'
            assert mxq == kw['maq']
        else:
            ## if defaultMxq available and sor in minQty sor
            if defaultMxq:
                assert sor_type == 'BPUNIMAQ'
                assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
            else:
                assert  sor_type == 'BPUNI'
        assert isSorManagedOrder == True

    elif sor_expect == "BESTPRICEMINQTYNOLIT":
        ## user specified maq
        if 'maq' in kw and kw['maq'] > 0:
            assert  sor_type == 'BPNOLITMAQ'
            assert mxq == kw['maq']
        else:
            ## if defaultMxq available and sor in minQty sor
            if defaultMxq:
                assert sor_type == 'BPNOLITMAQ'
                assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
            else:
                assert  sor_type == 'BPNOLIT'

        assert isSorManagedOrder == True
    elif sor_expect == 'BESTPRICEMINQTYNOLITUNI':
        ## user specified maq
       if 'maq' in kw and kw['maq'] > 0:
           assert sor_type == 'BPNOLITUNIMAQ'
           assert mxq == kw['maq']
       else:
           ## if defaultMxq available, for mxq > orderQty, it should be override as orderQty
           if defaultMxq:
               assert sor_type == 'BPNOLITUNIMAQ'
               assert mxq == int(defaultMxq) if int(defaultMxq) < orderQty else orderQty
           else:
               assert  sor_type  == 'BPNOLITUNI'


    elif sor_expect == 'BESTPRICEMINVALUE':

        ## check original orderValue > 120k
        if orderValue >= 120000:
            #pytest.set_trace()
            ## no MAQ
            ## user specified maq
            if 'maq' in kw and kw['maq'] > 0:
                assert mxq == kw['maq']
                assert  sor_type == "BPMVMAQ"
            else:
                ## for minQty sor and defaultMxq available
                if defaultMxq: # and 'maq' in kw and kw['maq'] == -1:
                    assert mxq == int(defaultMxq)
                    assert  sor_type == "BPMVMAQ"
                else:
                    assert  sor_type == "BPMV"

            assert orderInst.minExecutableNotionalValue == 120000
            assert isSorManagedOrder == True

        else:
            #if sor.endswith('maq'):
            #    assert  translateOrderType(orderInst) == "SYDE-Limit/MAQ"
            #else:
            assert  sor_type.startswith("SYDE-LIMIT")
            assert isLeafOrder == True
            assert tradingAlgorithm == 'ASXDIRECT'

    else:
        #pytest.set_trace()
        assert False,"unexpected sor_type:%s, inst: %s" % (sor_type,orderInst)


    print "validated SI sor override: reg: %s, \n order: %s" % (regdata,kw)

