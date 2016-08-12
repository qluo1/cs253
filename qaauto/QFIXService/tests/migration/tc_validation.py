""" validation of received FIX ER(s) and expected results.

"""

import pyfix42


class NoAckFound(Exception):
    """ no er received."""


def validate_er(recv_res, expectedResults,**kw):
    """
    """
    if len(recv_res) == 0:
        raise NoAckFound()

    assert len(expectedResults) > 0

    assert len(expectedResults) == len(recv_res)

    for idx, result in enumerate(expectedResults):
        serviceType = result['serviceType']
        assert serviceType=="fix-line"
        res_serviceName = result['serviceName']

        res_message = result['message']
        res_fields = res_message['fields']
        res_messageId = res_message['messageId']
        res_table = res_message['table']

        expectedMatchField = result["expectedResultMatchField"]
        assert expectedMatchField in ("ClOrdID", "MsgType")

        print "expected[%d]: %s" %(idx,result)

        ## match ordStatus
        assert pyfix42.RENUMS['OrdStatus'][res_fields['OrdStatus']] == recv_res[idx]['OrdStatus']


    return True


