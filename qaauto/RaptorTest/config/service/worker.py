""" worker thread for sending/receiving order/er via OMQ.


- incoming order via ORDER_REQ_ENDPOINT
- outgoing order in FIX as well as ER via ER_PUBSUB_ENDPOINT

note: all FIX messages (i.e. order/er) will be published to ER_PUBSUB_ENDPOINT.
"""
import sys
import logging
import threading
import traceback
import quickfix
import zerorpc
import gevent
import Queue
import os

from datetime import datetime

log = logging.getLogger(__name__)
## application configuration
import conf
from utils import Priority


class Worker(object):

    """ appliation worker.
    - handle order request via zerorpc server.
    - handle outgoing fix message publishing via zeorpc publisher in a dedicated thread.

    communicate with FIX applicaiton via work_queue.

    all variables configured at settings.
    """

    def __init__(self,work_queue,settings):

        assert isinstance(settings,conf.Settings)

        self.fix42_dict_ = quickfix.DataDictionary(settings.FIX42_DICT)
        self.work_queue_ = work_queue

        self.server_ = zerorpc.Server(methods={
                                        settings.FIX_API_ORDER: self.order_request,
                                        settings.FIX_API_STATUS: self.session_status,
                                       })
        log.info("worker binding: %s" % settings.FIX_API_ENDPOINT)
        self.server_.bind(settings.FIX_API_ENDPOINT)

        self.session_maps_ = settings.SESSION_MAPS

        self.worker_ = threading.Thread(name="worker",target=self.run)
        self.worker_.setDaemon(True)
        self.running_ = True
        ## save for later
        self.settings_ = settings
        ## start worker publisher
        self.worker_.start()

    def start(self):
        """ kick start rpc server."""
        self.server_.run()

    def order_request(self,session,message, **kw):
        """ handle incoming order request."""

        log.info("incoming order for session: %s" % (session))
        if session not in self.session_maps_:
            error ="session: %s not found in session_maps:%s" %(session,self.session_maps_)
            log.error(error)
            raise ValueError(error)

        ## not validate FIX message by default.
        validate = kw.get("validate",False)
        ## construct fix message and valid it
        fix_msg = quickfix.Message(message,self.fix42_dict_,validate)
        ## set sending time
        #utcnow = datetime.utcnow().strftime("%Y%m%d-%H%M%S.%f")
        #fix_msg.setField(52,utcnow)
        ## find session
        sender,target = self.session_maps_[session].split(":")[-1].split("->")

        header = fix_msg.getHeader()
        header.setField(quickfix.SenderCompID(sender))
        header.setField(quickfix.TargetCompID(target))

        res = True
        ## send fix message
        if not quickfix.Session.sendToTarget(fix_msg):
            log.error("sending failed for [%s]: %s" % (session,fix_msg))
            res = False

        log.debug("FIX message out -> [%s], %s" % (session,fix_msg))

        return res

    def session_status(self,session):
        """ """
        log.info("incoming status request for session: %s" % session )
        if session not in self.session_maps_:
            error ="session: %s not found in session_maps:%s" %(session,self.session_maps_)
            log.error(error)
            raise ValueError(error)

        session_name = self.session_maps_[session]
        begin, rest = session_name.split(":")
        sender, target = rest.split("->")

        the_session = quickfix.Session.lookupSession(quickfix.SessionID(begin,sender,target))

        ret = {}
        ret['loggedon'] =  the_session.isLoggedOn()
        ret['enabled'] = the_session.isEnabled()
        ret['sessionID'] = the_session.getSessionID().toString()
        ret['exepctedSenderNum'] = the_session.getExpectedSenderNum()
        ret['expectedTargetNum'] = the_session.getExpectedTargetNum()
        return ret


    def run(self):
        """ run thread to handle incoming order and send to fix session.  """

        log.info("publisher started at: %s." % self.settings_.FIX_PUB_ENDPOINT)
        _publisher = zerorpc.Publisher()
        _publisher.bind(self.settings_.FIX_PUB_ENDPOINT)
        ## reverse lookup
        _lookup_session = dict([(v,k) for (k,v) in self.session_maps_.iteritems()])
        while self.running_:
            ## process outgoing FIX message
            try:
                category, order = self.work_queue_.get(timeout=0.1)

                ## translate to short session name
                order['session'] = _lookup_session[order['session']]
                if category == Priority.order:
                    log.info("sumbitted FIX order -> [%s], %s" % (order['session'],order['message']))
                else:
                    log.info("received FIX ER <- [%s], %s" % (order['session'],order['message']))
                ## send to zerorpc
                method = getattr(_publisher,self.settings_.FIX_PUB_METHOD_NAME)
                method(order)
                log.debug("published order to name: %s" % self.settings_.FIX_PUB_METHOD_NAME)
            except Queue.Empty:
                gevent.sleep(0)
            except Exception,e:
                # handle error
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error = "failed on processing outgoing order: %s, tb: %s" % (e,traceback.extract_tb(exc_traceback))
                log.error(error)
        log.info("publisher stopped.")

    def stop(self,timeout=20):
        """ set stop flag and wait for it finish. """
        log.info("worker stop called.")

        ## close API server
        self.server_.close()
        ## shutdown publisher
        self.running_ = False
        if self.worker_.isAlive():
            self.worker_.join(timeout)

        assert not self.worker_.isAlive()

        log.info("worker stopped.")
