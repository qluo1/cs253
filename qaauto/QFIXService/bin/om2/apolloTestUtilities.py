# $Header: /home/cvs/eqtech/cep/src/apollo/apollosimulator/config/apolloTestUtilities.py,v 1.5 2013/07/25 08:42:37 mohant Exp $
from OmEngineState import OmEngineState
from OmOrder import OmOrder
import OmTestCase
import os;
import time;
from time import localtime, strftime
import catalog

# Utilities functions used by test cases for logon and logout
# Should be run only once when starting, and once when finishing all test cases
def startAcceptor(engineState, testSuite):
    exchCompId = os.getenv('exchCompId')
    exchTargetId = os.getenv('exchTargetId')
    fixConnectionId = exchCompId + '.' + exchTargetId

    # Unique Test Case Name
    uniqueTestCaseName = 'FixAcceptor'
    fixAcceptor = engineState.createTestCase(uniqueTestCaseName)
    messageId = uniqueTestCaseName
    fixAcceptor.addMessageToCustomer(fixConnectionId, 'Logon', 'A', 'MsgType',
        {
            'MsgType' : 'A',
            'SenderCompID' : '{*}',
            'SendingTime'  : '{*}',
            'MsgSeqNum'    : '{*}',
            'HeartBtInt'    : '{*}',
            'EncryptMethod' : '{*}',
            'TargetCompID' : '{*}',
        }
    )

    testSuite.append(fixAcceptor.testCaseData())
    return fixAcceptor

def runLogon(engineState, testSuite):
    compId = os.getenv('compId')
    targetId = os.getenv('targetId')
    fixConnectionId = compId + '.' + targetId
    rtrConnectionId = 'ROUTER.LH'

    # Unique Test Case Name
    uniqueTestCaseName = 'FixLogonTest'
    fixLogon = engineState.createTestCase(uniqueTestCaseName)
    messageId = uniqueTestCaseName
    fixLogon.addMessageFromCustomer(fixConnectionId, 'Logon', messageId,
        {
            'MsgType' : 'A',
        }
    )
    # Add the expected Results
    fixLogon.addMessageToCustomer(fixConnectionId, 'Logon', 'A', 'MsgType',
        {
            'SenderCompID' : 'GSET',
            'SendingTime'  : '{*}',
            'MsgSeqNum'    : '{*}',
            'MsgType'      : 'A',
            'TargetCompID' : '{*}',
            'EncryptMethod' : '{*}',
            'HeartBtInt'    : '{*}',
        }
    )
    testSuite.append(fixLogon.testCaseData())
    return fixLogon

def runLogout(engineState, testSuite):
    compId = os.getenv('compId')
    targetId = os.getenv('targetId')
    fixConnectionId = compId + '.' + targetId
    rtrConnectionId = 'ROUTER.LH'

    # Explicitly send a logout message
    uniqueTestCaseName = 'Fix Logout'
    fixLogout = engineState.createTestCase(uniqueTestCaseName )
    messageId = uniqueTestCaseName
    fixLogout.addMessageFromCustomer(fixConnectionId, 'Logout', messageId,
        {
            'MsgType' : '5',
        }
    )
    testSuite.append(fixLogout.testCaseData())
    return fixLogout

# the lhtestUtilities.setTime() function takes parameter date and GMT time
# as a string with:
# "year(4 digits)month(2 digits)day(2 digits)-hour(24hr time):min:seconds"
# for example:
# "20100211-15:29:00"
def setTime(timeString = None) :
    if timeString is not None :
        givenTime = timeString
    else:
        givenTime = time.strftime("%Y%m%d-%X", time.localtime())
    return givenTime

# calculate the checkSum for a fixMessage
def calculateCheckSum(fixMessage):
    cks = 0
    for ch in fixMessage:
        cks += ord(ch)

    cks = cks % 256
    return cks
