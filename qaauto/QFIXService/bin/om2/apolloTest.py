# $Header: /home/cvs/eqtech/cep/src/apollo/apollosimulator/config/apolloTest.py,v 1.11 2014/12/17 08:44:54 ananas Exp $

from OmEngineState import OmEngineState
#from OmOrder import OmOrder
import OmTestCase
import apolloTestUtilities
import newOrderScenario
import newOrderRejectScenario
import newOrderFillScenario
import replaceOrderScenario
import replaceOrderRejectScenario
import cancelOrderScenario
import cancelOrderRejectScenario
import adaptorStatusHermesCommand
import massCancelHermesCommand
import circuitBreakerHermesCommand
import fixEngineLogQueryTests
import fixEngineLogScrapperTests
import inboundAdaptorOnHoldScenario
import outboundAdaptorOnHoldScenario
import outboundAdaptordownScenario
import inboundAdaptordownScenario
import putOutBoundIvComAdaptorOnHold
import putOutBoundFixAdaptorOnHold
import fixToIvComOrder
import makeOutBoundIvComAdaptorActive
import massCancelForIvComAdaptor
import putOutBoundIvComAdaptorDown
import fixOverIvComOrder
import dealerweb
import proxyAdaptorTestCases
import outboundFailoverScenario
import r2rDestinationStatusScenario
import adaptorDepdendency
import fixIvadaptorDepdendency
import os;
import time;
from time import localtime, strftime
import catalog

def apolloTest(testName, engineStripeName, numTests) :
    "This method creates the line handler test script - developer written test cases"
    testSuite = []
    engineState = OmEngineState(engineStripeName)
    counter = 1
    testCategory = os.getenv('testCategory')
    if testCategory == None or testCategory == "":
        testCategory = "standard"

    # R2R tests needs to run before we start acceptor since the test suite expects some resulting
    # messages as soon as connection is established
    if testCategory == "r2r":
        counter = r2rDestinationStatusScenario.runScenario(171, engineState, testSuite, counter)
        return testSuite

    acceptor = apolloTestUtilities.startAcceptor(engineState, testSuite)
    logon = apolloTestUtilities.runLogon(engineState, testSuite)

    # Putting IvCom Adaptor onHold so it is not picked for routing the order while we test fix-to-fix.
    if testCategory == "hc":
        putOutBoundIvComAdaptorOnHold.runScenario(engineState, testSuite, "TESTC1")
        putOutBoundIvComAdaptorOnHold.runScenario(engineState, testSuite, "TESTC2")

    counter = newOrderScenario.runScenario(1, engineState, testSuite, counter)
    counter = newOrderRejectScenario.runScenario(11, engineState, testSuite, counter)
    counter = newOrderFillScenario.runScenario(21, engineState, testSuite, counter)
    counter = replaceOrderScenario.runScenario(31, engineState, testSuite, counter)
    counter = replaceOrderRejectScenario.runScenario(41, engineState, testSuite, counter)
    counter = cancelOrderScenario.runScenario(51, engineState, testSuite, counter)
    counter = cancelOrderRejectScenario.runScenario(61, engineState, testSuite, counter)
    counter = adaptorDepdendency.runScenario(71, engineState, testSuite, counter, testCategory)
    counter = inboundAdaptorOnHoldScenario.runScenario(71, engineState, testSuite, counter)
    counter = outboundAdaptorOnHoldScenario.runScenario(81, engineState, testSuite, counter)
    counter = outboundFailoverScenario.runScenario(91, engineState, testSuite, counter, testCategory)
    counter = outboundAdaptordownScenario.runScenario(101, engineState, testSuite, counter, testCategory)
    counter = inboundAdaptordownScenario.runScenario(111, engineState, testSuite, counter, testCategory)

    if testCategory == "hc":
        # fix-to-fix test cases are completed here, now putting fix outbound adaptor onhold.
        putOutBoundFixAdaptorOnHold.runScenario(engineState, testSuite, "X3SIM.FIX")
        makeOutBoundIvComAdaptorActive.runScenario(engineState, testSuite, "TESTC1")
        counter = fixToIvComOrder.runScenario(121, engineState, testSuite, counter)
        # fix-to-ivcom testcases are over.
        # ivcom simulator doesnot allow random messages sent for any ivcom datastream.
        # when fix adaptor goes down, IvComOutbound adaptor sends mass cancel.
        # This mass cancel is already tested in inboundAdaptordownScenario
        # hence making IvComAdaptor down so we dont need to catch the mass cancel and compare it.
        putOutBoundIvComAdaptorDown.runScenario(engineState, testSuite, "TESTC1")
        # Now make the second ivcom adaptor active so that we can run the fixOverIv test cases
        makeOutBoundIvComAdaptorActive.runScenario(engineState, testSuite, "TESTC2")
        counter = proxyAdaptorTestCases.runScenario(131, engineState, testSuite, counter)
        counter = fixOverIvComOrder.runScenario(141, engineState, testSuite, counter)
        counter = dealerweb.runScenario(151, engineState, testSuite, counter)
        counter = fixIvadaptorDepdendency.runScenario(161, engineState, testSuite, counter)
        putOutBoundIvComAdaptorDown.runScenario(engineState, testSuite, "TESTC2")

    adaptorStatusHermesCommand.runScenario(engineState, testSuite)
    massCancelHermesCommand.runScenario(engineState, testSuite)
    circuitBreakerHermesCommand.runScenario(engineState, testSuite)
    fixEngineLogQueryTests.runScenario(engineState, testSuite)
    fixEngineLogScrapperTests.runScenario(engineState, testSuite)
    logout = apolloTestUtilities.runLogout(engineState, testSuite)

    return testSuite

# This is the set of methods that are accessible from lhsimulator.py
testsDict = {
    "apolloFunctionalTest" : apolloTest,
}

def create(testSuiteName, engineStripeName, numTests) :
    "This is the public interface, called by lhsimulator.py"
    if numTests < 1 :
        numTests = 1
    testSuiteFunc = testsDict.get(testSuiteName)
    if callable(testSuiteFunc) :
        return testSuiteFunc(testSuiteName, engineStripeName, numTests)
    print "test [" + testSuiteName + "] is not defined, please check the testSuiteName defined in /env/local_vars\n"
