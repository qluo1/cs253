""" subscribe DSS, ImageLive, TransationNotificaiton and save them into mongodb.

this is an internal client of IvComService.

"""
import os
import sys
import logging
import logging.config
from datetime import datetime
import traceback

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ROOT = os.path.dirname(CUR_DIR)
if SCRIPTS_ROOT not in sys.path:
    sys.path.append(SCRIPTS_ROOT)
PROJ_ROOT = os.path.dirname(SCRIPTS_ROOT)
LOG_DIR = os.path.join(PROJ_ROOT,"logs")

## setup local config
import cfg
from conf import settings
import zerorpc
from cfg import om2CompleteCatalog, om2CompleteCatalogEnums,json, dss_db,imagelive_db

from utils import enrich_enum

env = os.environ['SETTINGS_MODULE'].split(".")[-1]
## setup logging
logging.config.dictConfig(settings.MSGDUMPER_LOGGING)

log = logging.getLogger(__name__)

class  SubClient():
    """ test client implement of zerorpc callback. """

    ## setup order view
    orderViewName_ = "msgDumper_orderView"
    execViewName_ = "msgDumper_executionView"
    service_ = zerorpc.Client()
    service_.connect(settings.ORDER_API_URL)

    def onReplication(self,message):
        pass
        #print message

    def onDSS(self,message):
        """ save DSS message to mongodb. """

        log.debug("received dss %s" % message)
        try:
            msg,table,msgId,posDup = message['msg'],message['table'],message['msgId'],message['posDup']
            assert isinstance(msg,dict)
            ## process dss
            assert table == 'OrderExecutionUpdate'
            ## enrich and save to mongodb
            today = datetime.now().strftime("%Y%m%d")
            _msgId = "%s_%s" % (today,msgId)
            ## filter out duplicated event for OM2 DSS
            if not posDup or posDup and not _dss.find_one({'msgId':_msgId}):
                ## enrich message with ivcom enum
                enrich_enum(table,msg)
                ## a valid dss message
                if 'eventData' in msg and 'events' in msg['eventData']:
                    res = {'table':table,'msgId':_msgId,'msg':msg}
                    dss_db.save(res)
        except Exception,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log.error("failed onDss : %s, tb: %s" % (e,traceback.extract_tb(exc_traceback)))

    def onImagelive(self,message):
        """ save imagelive into mongodb. """

        viewName = message['viewName']
        if viewName in (self.orderViewName_, self.execViewName_):
            event = message['event']
            if event == "update":
                msg = message['message']
                recordId = message['recordId']
                init = message['isInitialization']
                version = message['version']
                ##
                now = datetime.now()
                today = now.strftime("%Y%m%d")

                if not init or not imagelive_db.find_one({'recordId': recordId,'version': version}):
                    ## if not init or init but not found in db then save it to db.
                    res = {'recordId': recordId, 'version': version, 'msg': msg,'date': today,'time':str(now)}
                    log.info("saved recordId: %s, version: %s, init: %s" %(recordId,version, init))
                    imagelive_db.save(res)
                else:
                    log.debug("ignore message: record: %s, version %s, init: %s" % ( recordId,version,init))
            else:
                log.info(message)

    def _setup_imageLiveView(self):
        """ internal helper to setup imageLiveView for order/execution."""

        from viewCreator import ViewCreator
        ## list handler
        sessions =  self.service_.list_sessions()
        providerName = "imageliveserver-%s" % env
        assert providerName in sessions, sessions

        try:
            self.service_.cancelImgLiveView(providerName, self.orderViewName_)
        except Exception,e:
            log.warn("cancel view failed: %s" % e)

        v = ViewCreator(self.orderViewName_)
        v.addTypeAndFields("order", ["currentOrder",
                                     "currentOrder/orderInstructionData",
                                     "currentOrder/orderStatusData",
                                     "currentOrder/relatedEntityIndexes",
                                     ])
        assert self.service_.createImgLiveView(providerName, *v())

        ## setup execution view
        try:
            self.service_.cancelImgLiveView(providerName, self.execViewName_)
        except Exception,e:
            log.warn("cancel view failed: %s" % e)

        v = ViewCreator(self.execViewName_)
        v.addTypeAndFields("execution", ["currentExecution","previousExecution"])
        assert self.service_.createImgLiveView(providerName, *v())

def run_app():
    """ """
    client = SubClient()
    subscriber = zerorpc.Subscriber(methods={
                                         '%s->replication' % env: client.onReplication,
                                         '%s->QAAUCE_Listener' % env: client.onDSS,
                                         'imageliveserver-%s' % env: client.onImagelive
                                         })
    log.info("subscribe to %s" % settings.PUBLIC_PUB_ENDPOINT)
    subscriber.connect(settings.PUBLIC_PUB_ENDPOINT)

    log.info("setup imageliveView")
    client._setup_imageLiveView()
    ## 
    subscriber.run()

if __name__ == "__main__":
    run_app()

