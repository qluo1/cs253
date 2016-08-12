# $Header: /home/cvs/eqtech/cep/src/testCaseOm2Utilities/OmOrder.py,v 1.1 2013/02/13 17:06:38 krielq Exp $

from OmEngineState import OmEngineState

class OmOrder(object):
    "This class represents an order. Only the OmEngineState should construct objects of this type"

    def __init__(self, engineState):
        "this method initializes an order, the caller may optionally specify a dictionary of order attributes to override the default attributes"
        self.__engineState = engineState
        self.__id = engineState.nextOrderId()

    def orderId(self):
        "returns the order's id"
        if self.__engineState.useVariableTags():
            var = { 'variable': self.__id + '_' + str(self.__engineState.getTagSequenceNumberResetCount()) }
            return var

        return self.__id

    def orderIdAsText(self):
        "returns the order's id"
        return self.__id

