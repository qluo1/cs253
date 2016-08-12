""" helper funcitons.

- patch GS FIX

"""

import pyfix42

def patch_fix_order(table,fields):
    """ """
    assert isinstance(fields,dict)
    ############################################
    ##patch/convert message to right FIX tag name

    ## strip whitespace
    for k,v in fields.items():
        fields[k] = v.strip()
    ## fix inconsistent case
    if 'Side' in fields:
        fields['Side'] = fields['Side'].title()

    if 'MsgType' in fields :
        fields['MsgType'] = pyfix42.RENUMS['MsgType'][fields['MsgType']]
    else:
        ## using table to set msgType
        if table.upper() == "ORDER - SINGLE":
            fields['MsgType'] = "NewOrderSingle"
        elif table.upper() == "ORDER CANCEL/REPLACE REQUEST":
            fields['MsgType'] = "OrderCancelReplaceRequest"
        elif table.upper() == "Order Cancel Request":
            fields['MsgType'] = "OrderCancelRequest"
        else:
            raise ValueError("unexpected order type:%s" % table)


    if 'HandlInst' in fields and fields['HandlInst'] in pyfix42.RENUMS['HandlInst']:
        fields['HandlInst'] = pyfix42.RENUMS['HandlInst'][fields['HandlInst']]
    ## need conversion
    if 'ExecInst' in fields and fields['ExecInst'] in pyfix42.RENUMS['ExecInst']:
        fields['ExecInst'] = pyfix42.RENUMS['ExecInst'][fields['ExecInst']]
    ## patch inconsistent
    if '8031' in fields:
        fields['Algorithm'] = fields.pop('8031')
    if '775' in fields:
        fields['BookingType'] = pyfix42.RENUMS['BookingType'][int(fields.pop('775'))]
    if "ContractForDifference" in fields:
        fields['BookingType'] = pyfix42.RENUMS['BookingType'][int(fields.pop('ContractForDifference'))]

    if "DoNotSmartRoute" in fields:
        fields['11007'] = fields.pop("DoNotSmartRoute")
