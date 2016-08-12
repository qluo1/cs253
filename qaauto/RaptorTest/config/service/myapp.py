import logging
import quickfix
from Queue import PriorityQueue

from utils import Priority
log = logging.getLogger(__name__)


class Application(quickfix.Application):

    """ quickfix application.
    - put outgoing order into order_queue.
    - put incoming er into er_queue.
    """

    def init(self,work_queue):
        """ """
        self.work_queue_ = work_queue

        super(quickfix.Application,self).__init__()

    ## quickfix interface
    def onCreate(self, sessionID):
        """ interface, on session crated. """
        log.info("session: %s onCreate" % sessionID)

    def onLogon(self, sessionID):
        """ interface, on session logon. """
        log.info("session: %s onLogon" % sessionID)

    def onLogout(self, sessionID):
        """ interface. on session logout. """
        log.info("session: %s onLogout" % sessionID)

    def toAdmin(self, message, sessionID):
        """ interface. toAdmin for session. """
        log.debug("session: %s toAdmin" % sessionID)

    def toApp(self, message, sessionID):
        """ interface. toApp for session. """
        log.info("session: %s toApp" % sessionID)
        try:
            self.work_queue_.put((Priority.order,
                                  dict(method='toApp',
                                       session=sessionID.toString(),
                                       message=message.toString()))
                                  )
        except Exception,e:
            log.error("failed to put outgoing queue: %s" % e)

    def fromAdmin(self, message, sessionID):
        """ interface. fromAdmin for session. """
        log.debug("session: %s fromAdmin" % sessionID)

    def fromApp(self, message, sessionID):
        """ interface. fromApp for session. """
        log.info("session: %s fromApp: %s" % (sessionID,message))
        try:
            self.work_queue_.put((Priority.er,
                                  dict( method='fromApp',
                                        session=sessionID.toString(),
                                        message=message.toString()))
                                  )
        except Exception,e:
            log.error("failed to put incoming queue: %s" % e)

