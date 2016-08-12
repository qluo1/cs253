import os
from datetime import datetime,timedelta
import time
import json
from pprint import pprint

import cfg
import pymongo
import time
from conf import settings
env = os.environ['SETTINGS_MODULE'].split(".")[-1]

mongo_client = pymongo.MongoClient("mongodb://dss_client:dss_client@%s:%s" % settings.MONGO_CFG)
## dynamically set dss db based on instance.
mongo_database = eval("mongo_client.%s" % env)
## dss collection
dss_db = mongo_database.dss
_dss = dss_db
## image live collection
_imagelive = mongo_database.imagelive


from bson.code import Code
from collections import defaultdict
from docopt import docopt
import itertools
import os,time

## set local tz to melbourne
#
dss_filter = {'msg.currentExecution':1, 'msg.currentOrder':1,'msg.eventData':1,'msgId':1
              #,'msg.transactionalProduct':1
             }

def qdss_lookup(day,**kwargs):
    """
    """
    #print day,eventId
    days = datetime.now() - timedelta(days=int(day))

    direct = pymongo.ASCENDING
    #print "query day", days.date()
    if 'eventId' in kwargs:
        msgId = "%s_%s" % (days.strftime("%Y%m%d"),kwargs['eventId'])
        return _dss.find_one({"msgId":msgId},dss_filter)

    if 'orderId' in kwargs:
        res = _dss.find({'msg.currentOrder.orderStatusData.orderId': {'$regex':kwargs['orderId']+"$"}},fields=dss_filter,
                               sort=[('msg.eventData.eventTime',direct),
                                     ('msg.eventData.eventTimeMicrosecond',direct)],
                        )
        return [r for r in res]

    if 'xref' in kwargs:
        res = _dss.find({'$or': [ {'msg.currentOrder.orderStatusData.externalReferences.tag': kwargs['xref']},
                                     {'msg.currentOrder.pendingCorrection.externalReferences.tag': kwargs['xref']}] },
                                    sort=[('msg.eventData.eventTime',direct),
                                     ('msg.eventData.eventTimeMicrosecond',direct)],
                                     fields=dss_filter)
        return [r for r in res]
    if 'eventKey' in kwargs:
        res = _dss.find({'msg.eventData.eventId' :kwargs['eventKey']},dss_filter)
        return [r for r in res]


from utils import translateOrderType
from utils import ER

def tail_DssEvents(last,**kwargs):
    """
        list DSS event for last 30 events
    """
    day     = int(kwargs['day'])
    f_xref  = kwargs['filter']
    head    = kwargs['head']
    #print day
    today = datetime.now() - timedelta(days=day)
    #print today
    crit ={'msg.currentOrder.orderStatusData.eventDate':today.strftime("%Y%m%d")}
    if f_xref :
        if len(f_xref) > 10 and "-" not in f_xref:
            crit['msg.currentOrder.orderStatusData.orderId'] = {'$regex': f_xref.strip() + "$"}
        else:
            crit['msg.currentOrder.orderStatusData.externalReferences.tag'] = {'$regex': '^' + f_xref.strip()}

    direct = pymongo.DESCENDING if not head else pymongo.ASCENDING
    res = _dss.find(crit,filds=dss_filter,
                        sort=[('msg.eventData.eventTime',direct),
                              ('msg.eventData.eventTimeMicrosecond',direct)],
                        limit=int(last))
    def gen_out(res):
        for r in reversed(list(res)):
            #print r
            eventId = r['msgId']
            ## trade dss as an object.
            er = ER(r['msg'])
            ## only one
            currentOrder = r['msg']['currentOrder']
            inst = currentOrder['orderInstructionData']
            symbol = inst['productId'].split(".")[0]
            orderStatusData = currentOrder['orderStatusData']
            orderId = orderStatusData['orderId']
            eventNumber = orderStatusData['eventNumber']
            created = orderStatusData['createDateTime']
            isRoot = orderStatusData.get('isRootOrder')
            primaryStatus = orderStatusData['primaryStatus']
            if 'childCount' in orderStatusData:
                primaryStatus = primaryStatus + "|%d"% orderStatusData['childCount']
            eventData = r['msg']['eventData']
            eventTime = time.localtime(eventData['eventTime'])
            events = eventData.get("events")
            ## parsing sor order type
            isSor = translateOrderType(er.order)
            childOrder = ''
            if 'relatedEntityIndexes' in currentOrder:
                #'relatedEntityIndexes': [{u'entityFirstVersion': 1,
                #                         u'entityId':
                #                         u'QAEAUCEA527320150615O',
                #                         u'relatedEntityFirstVersion':
                #                         1,
                #                         u'relatedEntityId':
                #                         u'QAEAUCEA527420150615O',
                #                         u'relatedEntityType':
                #                         u'ChildOrder'}],
                related = currentOrder['relatedEntityIndexes'][0]
                if related['relatedEntityType'] == 'ChildOrder':
                    childOrder = related['relatedEntityId']
                    ## update orderId with childOrder
                    orderId = orderId + "|" + childOrder[8:-9]

            ## convert back single event to list
            #if type(events) == dict: events = [events]
            tags = [i['tag'] for i in orderStatusData.get('externalReferences',[]) if i['systemName'].startswith("PlutusChild") or \
                                                                                      i['systemName'] == 'IOSAdapter' or \
                                                                                      i['systemName'] == 'MyIvComRF']
            internalEventTypes = [j['internalEventType'] for j in sorted(events,key=lambda t: t['internalEventSequenceNumber']) ]  if events else ['no events??']
            #import ipdb;ipdb.set_trace()
            ## add pendingCorrection
            if 'pendingCorrection' in currentOrder:
                tags.extend([i['tag'] for i in currentOrder['pendingCorrection']['externalReferences'] if i['systemName'].startswith("PlutusChild") or i['systemName'] == 'IOSAdapter'])

            externalEventType = eventData.get('externalEventType')
            creator = eventData.get('creatorId',"")


            #import ipdb;ipdb.set_trace()
            data = dict(
                    event = eventId,
                    eventNumber = eventNumber,
                    order = orderId,
                    symbol=symbol,
                    sor = isSor,
                    root = isRoot,
                    status = primaryStatus,
                    xref = ",".join(sorted(list(set(tags)))),
                    ## append externalEvent
                    events = "%s|%s" %(creator,externalEventType) + "->" + ",".join(internalEventTypes)  ,
                    eventTime = eventTime,
                    ##created = datetime.fromtimestamp(created).strftime("%b%d-%H:%M:%S"),
                    created = datetime.fromtimestamp(created).strftime("%H:%M:%S"),
                    )
            yield  data


    return gen_out(res)

def qdss_trade_byDay(day=0):
    """
        query DSS trade by day
        : day - last number of days
    """
    day = datetime.now() - timedelta(days=day)
    res = _dss.find({'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d"), 'currentExecution': {"$exists":True}})
    return res

## general reduce function
reducer = Code("""
            function(key,values) {
                var total = 0;
                for (var i=0; i< values.length;i++){
                    total+=values[i];
                }
                return total;
            }
            """)
def qdss_timebucket(duration=60,**kwargs):
    """
        calculate nums of DSS per time-bucket, and plot it
        - duration: time-bucket size in seconds
        - day: which day 0 i.e. today
        - start: sart eventId

        require: matplotlib
    """
    start = int(kwargs['start'])
    day = int(kwargs['day'])
    the_day = datetime.now() - timedelta(days=day)
    print the_day.strftime("%Y%m%d")
    ## figure the 1st DSS for the day
    res = _dss.find({'msgId': {'$regex':'^' + the_day.strftime("%Y%m%d")}},dss_filter,sort=[('msg.eventData.eventTime',pymongo.ASCENDING)],limit=1)
    try:
        first = res[0]
    except IndexError,e:
        print "noting found for :%s" % the_day
        return

    #print start, first['msgId']
    begin = first['msg']['eventData']['eventTime']
    #print begin,time.ctime(begin)

    ## workout time-bucket based on 1st dss eventTime
    mapper = Code("""
            function() {
                var split = this.msgId.split("_");
                var msgId = parseInt(split[1]);
                if (msgId > %d) {
                    emit(Math.round((this.msg.eventData.eventTime - %d)/%d),1);
                }
            }
    """%(start, begin, duration))
    #print mapper

    import matplotlib.pyplot as plt
    res = _dss.map_reduce(mapper,reducer,out="test",query={'msgId': {'$regex': '^' + the_day.strftime("%Y%m%d")}})
    results = [r.values() for r in res.find()]
    x,y = [],[]
    for _x,_y  in results:
        x.append(_x)
        #x.append(time.localtime(begin+_x*duration))
        y.append(_y)
    loc, labels = plt.xticks()
    #import pdb;pdb.set_trace()
    fig = plt.figure()
    fig.suptitle("bucket for date: %s" % the_day.strftime("%Y%m%d"))
    plt.plot(x,y,'r-o',linewidth=2.0)
    plt.ylabel('Nums of DSS per time-bucket')
    total_dss = sum(y)
    _from = time.localtime(begin+x[0]*duration)
    _to =   time.localtime(begin+x[-1]*duration)
    plt.xlabel('time-bucket: %s seconds, duration:[%s - %s], total dss: %d' % (duration,time.strftime("%H:%M:%S",_from),time.strftime("%H:%M:%S",_to),total_dss))
    plt.savefig("./bucket_%s.png" % the_day.strftime("%Y%m%d"))
    plt.show()

def stat_dss_internalEventType(day=-1):
    """
    """
    mapper = Code("""
                function() {
                    this.msg.eventData.events.forEach(function(e) {
                       emit(e.internalEventType,1);
                    });
                }
                """)
    if day >= 0:
        day = datetime.now() - timedelta(days=day)
        query = {'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")}
        result =  _dss.map_reduce(mapper,reducer,"results",query=query)
    else:
        result =  _dss.map_reduce(mapper,reducer,"results")

    #import pdb;pdb.set_trace()

    return [r.values() for r in result.find()]

def stat_dup_eventId(day=-1):
    """
    """
    mapper = Code("""
                function() {
                    emit(this.msg.eventData.eventId ,1);
                }
                """)
    if day >=0:
        day = datetime.now() - timedelta(days=day)
        print day.strftime("%Y%m%d")
        query = {'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")}
        result =  _dss.map_reduce(mapper,reducer,"results",query=query)
    else:
        result = _dss.map_reduce(mapper,reducer,"results")

    return [r.values() for r in result.find({'value':{'$gt': 2}})]

def stat_dss_stream(day=-1):
    """
        static for DSS by datastream qa or _dev
    """
    mapper = Code("""
                function() {
                    this.msg.currentOrder.orderStatusData.externalReferences.forEach(function(e) {
                        if (e.systemName == 'PlutusChild'){
                            emit(e.systemName,1);
                            }

                        if (e.systemName == "PlutusChild_DEV"){
                            emit(e.systemName,1);
                        }
                    });
                }
                """)
    if day >= 0:
        day = datetime.now() - timedelta(days=day)
        query = {'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")}
        result =  _dss.map_reduce(mapper,reducer,out="results",query=query)
    else:
        result =  _dss.map_reduce(mapper,reducer,out="results")

    #print result
    return [r.values() for r in result.find()]

def stat_summary_trades(day=-1):
    """ static for all trades for the day.  """

    _mapper = Code("""
                function(){
                    if (this.msg.currentExecution) {
                        var exec = this.msg.currentExecution.executionData;
                        var order = this.msg.currentOrder.orderInstructionData;
                        var prodId = order.productId.split(".")[0]
                        emit( prodId + "-" + exec.buySell + "-" + exec.executionPoint,
                              {
                                'val': exec.executionPrice * exec.quantity,
                                'vol': exec.quantity,
                                'count': 1
                              }
                             );
                    }
                }
                """)
    _reducer = Code("""
                function(key,values){
                    var res = {'val': 0, 'vol': 0,'count': 0};
                    for (var i=0; i<values.length; i++) {
                            res.val += values[i].val;
                            res.vol += values[i].vol;
                            res.count += values[i].count;
                        }
                    return res;
                }
                """)
    if day >=0:
        day = datetime.now() - timedelta(days=day)
        print day
        query={'$and': [{'msg.currentExecution':{'$exists':True}},  {'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")}]}
        result = _dss.map_reduce(_mapper,_reducer,out="results",query=query)

    else:
        result = _dss.map_reduce(_mapper,_reducer,out="results")

    #print result
    #import pdb;pdb.set_trace()
    return [r.values() for r in result.find()]


def stat_order_ack(days=-1):
        """
            map reduce version of order ack
        """
        import numpy as np
        import matplotlib.pyplot as plt

        _mapper = Code("""
            function() {
                var orderId = this.msg.currentOrder.orderStatusData.orderId;

                this.msg.eventData.events.forEach(function(e){
                    if (e.internalEventType == 'OrderEntry'){
                        emit(orderId, e);
                    }
                    if (e.internalEventType == 'OrderAccept'){
                        emit(orderId,e);
                    }
                    if (e.internalEventType =='OrderReject'){
                        emit(orderId,e);
                    }
                });
            }
         """)

        _reducer = Code("""
            function(key,values) {
                var entry =  {};
                var accept = {};
                var ack = 1;
                for (var i=0; i<values.length;i++){
                    if(values[i].internalEventType == 'OrderEntry'){
                        entry = values[i];
                    }
                    if(values[i].internalEventType == 'OrderAccept'){
                        accept = values[i];
                    }
                    if(values[i].internalEventType == 'OrderReject'){
                        accept = values[i];
                        ack = 0;
                    }
                }
                if (ack ==1 ) {
                    return {'ack': (accept.internalEventTime-entry.internalEventTime) + (accept.internalEventTimeMicrosecond-entry.internalEventTimeMicrosecond)/1000000};
                }else{
                    return {'nak':  (accept.internalEventTime-entry.internalEventTime) + (accept.internalEventTimeMicrosecond-entry.internalEventTimeMicrosecond)/1000000};
                }
            }
        """)

        if days >=0:
            day = datetime.now() - timedelta(days=days)
            print day
            query ={'$and':[{'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")},{'msg.eventData.events.internalEventType': {'$nin': ['OrderEntryFailure']}}]}
            result = _dss.map_reduce(_mapper,_reducer,out="results",query=query)

        else:
            query = {'msg.eventData.events.internalEventType': {'$nin': ['OrderEntryFailure']}}
            result = _dss.map_reduce(_mapper,_reducer,out="results")

        #print result
        res = [r.values() for r in result.find()]

        acks = np.array([r[1].values()[0] for r in res if r[1].keys()[0] =='ack'])
        naks = np.array([r[1].values()[0] for r in res if r[1].keys()[0] =='nak'])

        import pandas as pd

        #import pdb;pdb.set_trace()
        print "describe acks"
        packs = pd.Series(acks)
        print packs.describe()
        print "describe naks"
        pnaks =  pd.Series(naks)
        print pnaks.describe()

        #import pdb;pdb.set_trace()
        fig = plt.figure()
        fig.suptitle("NewAck at date : %s" % day.strftime("%Y%m%d"))
        ## plot
        plt.subplot(2,1,1)
        plt.hist(packs.dropna(), color='b',bins=50,alpha=0.75)
        plt.xlabel("ack in seconds")
        plt.ylabel("num of orders")
        plt.subplot(2,1,2)
        plt.hist(pnaks.dropna(),color='r',bins=50,alpha=0.75)
        plt.ylabel("num of orders")
        plt.xlabel("nak in seconds")
        plt.savefig('./newAck_%s.png' % day.strftime("%Y%m%d"))
        plt.show()

def _extract_amend(orders):
    """
        helper for stat_order_amend
        - input: orders i.e. all sor or direct orders amend history
        - for each order, sort based on timestamp
        - then calculate amend ack duration for each order
        - then calculate overall summary
    """
    #import pdb;pdb.set_trace()
    ## workout difference accept - reqest for each order
    results = {
            'acks': {},
            'naks': {}
            }
    acks_diff_overall = []
    naks_diff_overall = []

    for o in orders:
        ordId = o[0]['orderId']
        sor = _translateAlgoType(o[0]['sor'],o[0]['sorParams'],o[0]['minQty'] )if  o[0]['sor'] else  ''
        if len(o) % 2 != 0:
            print "skip order with odd number events: ", ordId,sor,len(o)
            continue
        ## sort
        o = sorted(o,key=lambda item: item['internalEventTime']+item['internalEventTimeMicrosecond']/1000000.0)
        ## split to ack/nak lists
        acks = []
        naks = []
        for idx,e in enumerate(o):
            if e['internalEventType'] =='AcceptOrderCorrect':
                acks.append(o[idx-1])
                acks.append(o[idx])
            elif e['internalEventType'] == 'RejectOrderCorrect':
                naks.append(o[idx-1])
                naks.append(o[idx])
            else:
                pass

        #import pdb;pdb.set_trace()
        if len(acks) > 0:
            res = filter(lambda r: r['internalEventType'] == 'RequestOrderCorrect',acks)
            ack = filter(lambda r: r['internalEventType'] == 'AcceptOrderCorrect', acks)
            res_time = [r['internalEventTime'] + r['internalEventTimeMicrosecond']/1000000.0 for r in res]
            ack_time = [r['internalEventTime'] + r['internalEventTimeMicrosecond']/1000000.0 for r in ack]
            if len(res_time) != len(ack_time):
                print "skip order:  ack not match req ", ordId,sor
                continue

            diff = np.array(ack_time) - np.array(res_time)
            #import pdb;pdb.set_trace()
            [acks_diff_overall.append(item) for item in diff]

            avg,median,max,min,std,size = np.average(diff), np.median(diff),np.max(diff),np.min(diff),np.std(diff),len(res_time)
            results['acks'][ordId] = (sor,size,avg,median,max,min,std)

        if len(naks) > 0:
            res = filter(lambda r: r['internalEventType'] == 'RequestOrderCorrect',naks)
            nak = filter(lambda r: r['internalEventType'] == 'RejectOrderCorrect',naks)
            res_time = [r['internalEventTime'] + r['internalEventTimeMicrosecond']/1000000.0 for r in res]
            nak_time = [r['internalEventTime'] + r['internalEventTimeMicrosecond']/1000000.0 for r in nak]
            if len(res_time) != len(nak_time):
                print "skip order:  ack not match req ", ordId,sor
                continue

            diff = np.array(nak_time) - np.array(res_time)
            [naks_diff_overall.append(item) for item in diff]

            avg,median,max,min,std,size = np.average(diff), np.median(diff),np.max(diff),np.min(diff),np.std(diff),len(res_time)
            results['naks'][ordId] = (sor, size,avg,median,max,min,std)

    if acks_diff_overall:
        results['acks_diff_overall'] = {'mean': np.mean(acks_diff_overall),'median': np.median(acks_diff_overall),'min': np.min(acks_diff_overall),
                                    'max':np.max(acks_diff_overall),'std':np.std(acks_diff_overall),'count':len(acks_diff_overall)}
    if naks_diff_overall:
        results['naks_diff_overall'] = {'mean': np.mean(naks_diff_overall),'median': np.median(naks_diff_overall),'min': np.min(naks_diff_overall),
                                    'max':np.max(naks_diff_overall),'std':np.std(naks_diff_overall),'count':len(naks_diff_overall)}

    return results

def _unpack_values(values):
    """
       recursively unpack mongo return values
    """
    assert type(values) == list
    ret = []
    for v in values:
        assert type(v) == dict
        if 'values' in  v:
            ret.extend(_unpack_values(v['values']))
        elif 'orderId' in v:
            ret.append(v)
        else:
            assert False, "unexpected value: %s" %v

    return ret

def stat_order_amend(days=-1):
        """
            map reduce version of order amend
        """
        _mapper = Code("""
            function() {
                var orderId = this.msg.currentOrder.orderStatusData.orderId;
                var sorType = this.msg.currentOrder.orderInstructionData.tradingAlgorithm;
                var sorParams = this.msg.currentOrder.orderInstructionData.tradingAlgorithmParameters;
                var minQty = this.msg.currentOrder.orderInstructionData.minExecutableQuantity;

                if (this.msg.eventData.events)
                {
                this.msg.eventData.events.forEach(function(e){
                    e['sor'] = sorType;
                    e['sorParams'] = sorParams;
                    e['minQty'] = minQty;
                    if (e.internalEventType == 'RequestOrderCorrect'){
                        emit(orderId, e);
                    }
                    if (e.internalEventType == 'AcceptOrderCorrect'){
                        emit(orderId,e);
                    }
                    if (e.internalEventType =='RejectOrderCorrect'){
                        emit(orderId,e);
                    }
                });
                }
            }
         """)

        _reducer = Code("""
            function(key,values) {
                if( values.length > 0)
                {
                    return {'values': values};
                }
            }
        """)

        if days >=0:
            day = datetime.now() - timedelta(days=days)
            print day
            query ={'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")}
            result = _dss.map_reduce(_mapper,_reducer,out="results",query=query)
        else:
            print "day is required"
            return

        np.set_printoptions(precision=10)
        ## extract all order amend history
        res = [r['value']['values'] for r in result.find()]
        res_1 = []
        for r in res:
            ## need unpack further
            res_1.append(_unpack_values(r))

        #import ipdb;ipdb.set_trace()
        sors = filter(lambda i:i[0]['sor'] is not None ,res_1)
        dirs = filter(lambda i:i[0]['sor'] is None, res_1)

        res_sors = {}
        res_dirs = {}
        #import ipdb;ipdb.set_trace()
        if sors:
            res_sors = _extract_amend(sors)
        if dirs:
            res_dirs = _extract_amend(dirs)

        return {'sors': res_sors, 'dirs': res_dirs}

def qdss_delete(days):
    """ clean up mongo db.

    - remove dss item older than certain days
    - remove order item older than certain days

    """
    days = int(days)
    if days == 0:
        print "warn: will keep today's data,delete all previous days data"
        days = 1

    the_day = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days= days)
    the_day_in_seconds = (the_day - datetime(1970,1,1)).total_seconds()
    print "remove %s dss item older than :%s" % (os.environ['SETTINGS_MODULE'].split(".")[-1],the_day)
    res = _dss.remove({'msg.eventData.eventTime': {'$lt': the_day_in_seconds}})
    print res
    print "remove %s imagelive item older than: %s" % (os.environ['SETTINGS_MODULE'].split(".")[-1], the_day)
    res = _imagelive.remove({'msg.currentOrder.orderStatusData.primaryStatus': 'Complete' ,
                             'msg.currentOrder.orderStatusData.orderCompletionTime': {'$lt': the_day_in_seconds}})
    print res

def stat_trades_pending(day=-1,plutus=False):
    """ static for all trades for the day.  """

    if plutus:
        _mapper = Code("""
                function(){
                    if (this.msg.currentExecution) {
                        var exec = this.msg.currentExecution.executionData;
                        var order = this.msg.currentOrder.orderInstructionData;
                        var prodId = order.productId.split(".")[0]
                        var orderStatus = this .msg.currentOrder.orderStatusData;
                       if (orderStatus.primaryStatus == 'Working' && orderStatus.quantityRemaining == null && order.sourceSystemName == 'PlutusChild' &&
                           order.quantity - exec.quantity != Math.max(orderStatus.splitQuantityRemaining,orderStatus.childQuantityPending))
                         {
                            emit(order.orderId ,1);
                         }
                    }
                }
                """)
    else:
        _mapper = Code("""
                function(){
                    if (this.msg.currentExecution) {
                        var exec = this.msg.currentExecution.executionData;
                        var order = this.msg.currentOrder.orderInstructionData;
                        var prodId = order.productId.split(".")[0]
                        var orderStatus = this .msg.currentOrder.orderStatusData;
                       if (orderStatus.primaryStatus == 'Working' && orderStatus.quantityRemaining == null &&
                           order.quantity - exec.quantity != Math.max(orderStatus.splitQuantityRemaining,orderStatus.childQuantityPending))
                         {
                            emit(order.orderId ,1);
                         }
                    }
                }
                """)

    _reducer = Code("""
                function(key,values){
                    return key;
                }
                """)
    if day >=0:
        day = datetime.now() - timedelta(days=day)
        print day
        query={'$and': [{'msg.currentExecution':{'$exists':True}},  {'msg.currentOrder.orderStatusData.eventDate': day.strftime("%Y%m%d")}]}
        result = _dss.map_reduce(_mapper,_reducer,out="results",query=query)

    else:
        result = _dss.map_reduce(_mapper,_reducer,out="results")

    #print result
    #import pdb;pdb.set_trace()
    return [r.values() for r in result.find()]

if __name__ == "__main__":
    doc = """Usage:
       query_dss.py test
       query_dss.py [options] stat
       query_dss.py [options] dupEvent
       query_dss.py [options] tradeSummary
       query_dss.py [options] (event <eventId>|order <orderId>|xref <xref> |eventKey <eventKey>)
       query_dss.py [options] tail
       query_dss.py [options] bucket
       query_dss.py [options] newAck
       query_dss.py [options] amendAck
       query_dss.py [options] delete
       query_dss.py [options] pendingTrade

       options:
       -d D, --day D        specify day [default: 0] i.e. today, 1 for previous day, etc
       -n N, --num N        specify number of dss [default: 10]
       -f F, --filter F     specify xref filter i.e. for all xref
       -t --head            tail header
       -j --json            dump as json
       -s <eventId>, --start <eventId>    specify start from eventId [default: 1]
       --freq <freq>        specify frequency [default: 60] i.e. 1 minute
       --csv                export trade summary as csv
       --plutus             pendingTrade for plutus only
    """
    from pprint import pprint
    from prettytable import PrettyTable
    results = docopt(doc,version="0.0.1",options_first=False)
    #print results

    day = int(results.get("--day"))

    if results['test']:
        qdss_byEventDay()
        qdss_timebucket(60,start=1,day=1)

    if results['newAck']:
       stat_order_ack(days=day)

    if results['amendAck']:
       res = stat_order_amend(days=day)
       ## sors and dirs
       sors = res['sors']
       dirs = res['dirs']

       def _print_result(name,res):
           """
               inner helper
           """
           title =['orderId','seq','sor','count','mean','median','max','min','std']
           table = PrettyTable(title)

           print " ========  ack %s summary ============" % name
           if 'acks_diff_overall' in res:
               pprint(res['acks_diff_overall'])

               for k,v in sorted(res['acks'].items(),key=lambda i:int(i[0][8:-9])):
                    table.add_row([k,k[8:-9],v[0],v[1],round(v[2],4),round(v[3],4),round(v[4],5),round(v[5],5),round(v[6],5)])
               print table

           print " ======== nack %s summary ============" % name
           if 'naks_diff_overall' in res:
               pprint(res['naks_diff_overall'])

               tbl_nak = PrettyTable(title)
               for k,v in sorted(res['naks'].items(),key=lambda i: int(i[0][8:-9])):
                    tbl_nak.add_row([k,k[8:-9],v[0],v[1],round(v[2],4),round(v[3],4),round(v[4],5),round(v[5],5),round(v[6],5)])
               print tbl_nak

       if sors: _print_result("sor",sors)
       if dirs: _print_result("dirs",dirs)


    if results['bucket']:
        start = int(results['--start'])
        duration = int(results['--freq'])
        qdss_timebucket(duration,start=start,day=day)

    if results['stat']:
        print "day %d's total dss by internalEventType" % day
        pprint(stat_dss_internalEventType(day))
        ##
        print "day %d's dss by stream" % day
        pprint(stat_dss_stream(day))

    if results['dupEvent']:
        ## print duplicate eventId
        stat = stat_dup_eventId(day)
        #stat = stat_order_ack(day)
        pprint(stat)
        #print len(stat)

    if results['tradeSummary']:
        stat = stat_summary_trades(day)
        #pprint(stat)
        ## export as csv or prettytable
        title =['symbol','side','exchange','count','qty','value']

        trade_count = 0
        if results['--csv']:
            import csv
            import StringIO
            out = StringIO.StringIO()
            writer = csv.writer(out,lineterminator="\n")
            writer.writerow(title)
            for r in stat:
                symbol,side,exchange = r[0].split("-")
                vals = r[1]
                writer.writerow([symbol,side,exchange,int(vals['count']),int(vals['vol']),'%.15g' % vals['val']])
                trade_count += vals['count']

            print out.getvalue()

        else:
            table = PrettyTable(title)
            table.align['count'] = table.align['qty'] = table.align['value'] = 'r'
            for r in stat:
                symbol,side,exchange = r[0].split("-")
                vals = r[1]
                table.add_row([symbol,side,exchange,int(vals['count']),int(vals['vol']),'%.15g' % vals['val']])
                trade_count += vals['count']
            print table

        print "total trades: ",trade_count

    if results['event']:
        event = results['<eventId>']
        out = qdss_lookup(day,eventId=event)
        pprint(out['msg'])
    if results['order']:
        order = results['<orderId>']
        out = qdss_lookup(day,orderId=order)
        #import pdb;pdb.set_trace()
        pprint([{o['msgId'].split("_")[-1]: o['msg']} for o in out])
    if results['xref']:
        xref = results['<xref>']
        out = qdss_lookup(day,xref=xref)
        pprint([o['msg'] for o in out])
    if results['eventKey']:
        key = results['<eventKey>']
        out = qdss_lookup(day,eventKey=key)
        pprint([o['msg'] for o in out])

    if results['tail']:
       number = results['--num']
       head = results['--head']
       filter = results['--filter']
       table = PrettyTable(['event','env','order','symbol','sor','status','events','xref','created','eventTime'])

       table.align['status'] = table.align['events'] = table.align['sor'] = "l"
       table.align['xref'] = table.align['status'] = "l"
       for r in tail_DssEvents(number,day=day,filter=filter,head=head):
           table.add_row([r['event'][9:] ,r['order'][0:3], r['order'][8:],r['symbol'],r['sor'],\
                          r['status'],r['events'],r['xref'],r['created'],time.strftime("%H:%M:%S",r['eventTime'])])
           #table.add_row([r['event'][9:] ,r['order'],r['sor'],r['status'],r['events'],r['xref'],r['created'],time.strftime("%H:%M:%S",r['eventTime'])])
       print table


    if results['delete']:
        qdss_delete(day)

    if results['pendingTrade']:
        if results['--plutus']:
           pprint(stat_trades_pending(day,True))
        else:
           pprint(stat_trades_pending(day))

