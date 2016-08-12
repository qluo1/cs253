""" save oma order into redis database.

- save each order/fill
- save orderId into set i.e. 1st 7 characters of the orderId. qa_XTDb2020150908, will be saved to qa_XTDb

"""
import os
import sys
import time
import logging
import threading
import traceback
import signal
from datetime import datetime,timedelta
import localcfg

from pynvp.nvpData import NVPData

## setup logging
log = logging.getLogger(__name__)

class NVPTracker(object):

    """ NVPtracker.

    - ack as subscribeer for all NVPS
    - process all NVPS into redis
    - update in-memory register
    """

    _register = None

    def __init__(self,settings,db, register=None):
        """ subscribe ER feeds. """
        ## app settings
        self.settings_ = settings
        ## callback 
        self._register = register
        ## redis db
        self.db_ = db

    def _on_nvp(self,data):
        """ callback for incoming nvp data. """

        log.debug("received nvp data:%s" % data)
        try:
            server = data["serverName"]
            nvp = data["nvp"]
            opType = data["opType"]
            tag = data["tag"]

            nvpData = NVPData(nvp)
            ## ignore Invalid
            if opType == 'OmaInvalid':
                log.error("opType is OmaInvalid: %s" % nvpData)
                return
            # expire in days
            ttl = int(self.settings_.NVP_TTL * 24 * 3600)
            if nvpData.get("OmaOrder"):
                orderId = nvpData["OmaOrder"]["OmaNvpUniqueTag"]
                version = nvpData["OmaOrder"]["OmaNvpVersionNumber"]
                #print "nvp data received: ", service,opType,orderId,version
                ## note fill with both OmaOrder and OmaExecution
                if nvpData.get("OmaExecution"):
                    key =b"%s|%s|fill" % (orderId,version)
                    if not self.db_.exists(key):
                        self.db_.setex(key,nvp,ttl)
                        log.info("add order/fill: %s" % key)
                else:
                    key =b"%s|%s" % (orderId,version)
                    if not self.db_.exists(key):
                        self.db_.setex(key,nvp,ttl)
                        log.info("add order: %s " % key)

                # save to set , set name match OmaNvpSystemName
                system = nvpData["OmaOrder"]['OmaStatus']["OmaNvpStatusSystem"]
                if not orderId.startswith(system):
                    locations = nvpData["OmaOrder"].getall("OmaLocationInformation")
                    for loc in locations:
                        name = loc.get("OmaNvpSystemName")
                        if orderId.startswith(name):
                            system = name
                            break
                if not self.db_.sismember(system,orderId):
                    self.db_.sadd(system, orderId)
                    log.info("save to set: %s, %s" % (system,orderId))
            ## add pt wave
            elif nvpData.get("OmaWave"):
                orderId = nvpData["OmaWave"]["OmaNvpUniqueTag"]
                version = nvpData["OmaWave"]["OmaNvpVersionNumber"]
                #print "nvp data received: ", service,opType,orderId,version
                key =b"%s|%s" % (orderId,version)
                if not self.db_.exists(key):
                    self.db_.setex(key,nvp,ttl)
                    ## save to set 
                    system = nvpData["OmaWave"]['OmaLocationInformation']["OmaNvpSystemName"]
                    #system = orderId[:7]
                    log.info("add order: %s, save to set: %s" % (key,system))
                    self.db_.sadd(system, orderId)

            elif nvpData.get("OmaAggregateWave"):
                #ignore for aggrWave for child order
                log.info("unprocessed : %s" % nvpData)
            ## replicated for OmaOrder
            elif nvpData.get("OmaStandAloneExecution"):
                if nvpData.get("OmaStandAloneExecution"):
                    orderId = nvpData["OmaStandAloneExecution"]["OmaNvpUniqueTag"]
                    version = nvpData["OmaStandAloneExecution"]["OmaNvpVersionNumber"]
                    #print "nvp data received: ", service,opType,orderId,version
                    if nvpData.get("OmaExecution"):
                        key =b"%s|%s|fill" % (orderId,version)
                        if not self.db_.exists(key):
                            self.db_.setex(key,nvp,ttl)
                            log.info("add order/fill: %s" % key)
                    else:
                        key =b"%s|%s" % (orderId,version)
                        if not self.db_.exists(key):
                            self.db_.setex(key,nvp,ttl)
                            log.info("add order: %s " % key)

                    # save to set , set name match OmaNvpSystemName
                    system = nvpData["OmaStandAloneExecution"]['OmaStatus']["OmaNvpStatusSystem"]
                    if not orderId.startswith(system):
                        locations = nvpData["OmaStandAloneExecution"].getall("OmaLocationInformation")
                        for loc in locations:
                            name = loc.get("OmaNvpSystemName")
                            if orderId.startswith(name):
                                system = name
                                break
                    if not self.db_.sismember(system,orderId):
                        self.db_.sadd(system, orderId)
                        log.info("save to set: %s, %s" % (system,orderId))
            else:
                log.error("unexpected nvp: %s, data: %s" % (nvpData,data))

            ## update internal in-memory register
            if self._register:
                self._register._process_nvp(system,nvpData.root_)

        except Exception,e:
            log.exception(e)


if __name__ == "__main__":
    """ utility program dump oma nvp order/execution into redis. """
    import signal
    import gevent
    import zerorpc

    from conf import settings
    logging.basicConfig(filename="logs/nvpdump.log",
                        level=logging.DEBUG,
                        format='%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s')

    tracker = NVPTracker(settings,localcfg.rdb)
    methods = {}
    for name,item in settings.OMA_SVRS.iteritems():
        if item['active']:
            methods[name] = tracker._on_nvp

    _subscriber = zerorpc.Subscriber(methods=methods)
    _subscriber.connect(settings.PUB_ENDPOINT)

    try:
        _subscriber.run()
    except KeyboardInterrupt,e:
        _subscriber.stop()

