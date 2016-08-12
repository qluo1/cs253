import os
from datetime import datetime,timedelta

class TestAttributes:
    "This class tracks some of the expected state of the om engine"

    def __init__(self, stripeName):
        "This method initializes the engine's state"
        self.__SenderCompID = os.environ['SenderCompID']
        self.__TargetCompID = os.environ['TargetCompID']

        self._nextOrderID = 1

#Accessors

    def getsendcompid(self):
        return self.__SenderCompID

    def gettargetcompid(self):
        return self.__TargetCompID

    def getOrderID(self):
        "This method return next order id "
        import time
        self._getOrderID = str(1240) + '_' + time.strftime("%Y-%m-%d-%X", time.gmtime()) + '_' + str(self._nextOrderID)
        self._nextOrderID  += 1
        return  self._getOrderID

    def getCurrTime(self):
        "This method return current time "
        import time
        return time.strftime("%Y-%m-%d-%X", time.gmtime())

    def getTradeDate(self):
        """ """
        import time
        return time.strftime("%Y-%m-%d", time.gmtime())


    def getDestination(self):
        """ """
        return "PPEXDMa"

    def getExpTime(self):
        "This method return current time "
        now = datetime.now()
        diff = timedelta(days=5)
        future = now + diff
        return future.strftime("%Y%m%d-%X")
