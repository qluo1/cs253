""" nvp data parser.

convert nvp raw data into MultiDict representation in python.

"""
import sys
from datetime import datetime,date
from pprint import pprint
import ctypes
from nvpDef import *
## gsatest 
#import localcfg
import MultiDict as MultiDict
from utils import chunks
try:
    from dateutil import parser
except ImportError:
    parser = None

import logging
log = logging.getLogger(__name__)

NVP_MARK=""

def construct_nvp_list(items):
    """ convert multidict into raw nvp."""

    assert items
    assert isinstance(items,MultiDict.OrderedMultiDict)
    out = []
    #import pdb;pdb.set_trace()
    for item in items.allitems():
        assert isinstance(item,tuple)
        assert len(item) == 2
        if isinstance(item[1],MultiDict.OrderedMultiDict):
            ## object start
            out += [1061,10,item[0]]
            out+= construct_nvp_list(item[1])
            ## object end
            out += [1062,10,item[0]]
        else:
            name,valType = nvp_names[item[0]]
            #if name == 1049: import pdb;pdb.set_trace()
            if valType == int:
                out += [name,0,item[1]]
            elif valType==ctypes.c_double:
                out += [name,9, item[1]]
            elif valType==ctypes.c_long:
                out += [name,3, item[1]]
            elif valType==float:
                out += [name,8, item[1]]
            elif valType==datetime:
                out += [name,13, item[1]]
            elif isinstance(valType,dict):
                try:
                    int(item[1])
                    out += [name,14, item[1]]
                except ValueError:
                    out += [name,10, item[1]]
            elif valType == str:
                out += [name,10, item[1]]
            else:
                out += [name,10,item[1]]
    return out

def construct_nvp_raw(items):
    """ """
    nvp_list = construct_nvp_list(items)
    nvp_list =[str(i) for i in nvp_list]
    # must end in mark
    return NVP_MARK.join(nvp_list) + NVP_MARK


class NVPData:

    """ multidict representation of nvp data. """

    def __init__(self,msg):
        """ parse incoming nvp string into nvpdata/multidict object. """

        self.root_ = self._parse(msg)

    def _parse(self,msg):
        """ parse nvp string to multidict.
        input: raw nvp string dump form oma client.
        output: multidict format of nvp, due to nvps allow duplicated keys.
        """
        try:
            log.debug("parsing: %s" % msg)
            ## split msg into list of nvps
            list_msg = msg.strip().split(NVP_MARK)
            nvps =list(chunks(list_msg,3))
            ## convert id to int
            log.debug("nvps list before: %s" % nvps)
            nvps = [[int(i[0]),i[2]] for i in nvps]
            log.debug("nvps list: %s" % nvps)

            stack = []
            root = MultiDict.OrderedMultiDict()
            stack.append(root)
            current_root = root
            #import pdb;pdb.set_trace()
            for item in nvps:
                assert item[0] in nvp_id_names
                name,tp =  nvp_id_names[item[0]]
                #print name, item[2], len(stack)
                if name == "OmaNvpObjectStart":
                    ## update current_root
                    objname = tp(item[1])
                    current_root[objname] = MultiDict.OrderedMultiDict()
                    ## push current root into stack
                    stack.append(current_root)
                    ## set current_root to new root
                    current_root = current_root[objname]
                elif name == "OmaNvpObjectEnd":
                    ## pop previous current_root out of  stack
                    current_root = stack.pop()
                else:
                    ## update current root for values
                    #if item[1] in ( u'',) : continue
                    if isinstance(tp,dict):
                        #print tp, item
                        tps = tp.values()[0]
                        if isinstance(item[1],int) and int(item[1]) in tps:
                            try:
                                current_root[name] = tps[int(item[1])][0]
                            except Exception,e:
                                log.warn("can't convert %s,%s" %(item,tp))
                                current_root[name] = item[1]
                        elif "," in item[1]:
                            ## group of values
                            values = item[1].split(",")
                            values = [tps[int(v)][0] for v in values]
                            current_root[name] = values
                        else:
                            ## only log if tps has configured items
                            if tps and item[1] != '-1':
                                ## ignore 1707 'NoMarketOrdinal
                                if item[0] != 1707:
                                    log.warn("%s item not found in types: %s" % (item,tps))
                            current_root[name] = item[1]
                    else:
                        try:

                            if tp == datetime or tp == date:
                                if parser:
                                    current_root[name] = parser.parse(item[1])
                                else:
                                    current_root[name] = item[1]
                            elif tp is None:
                                current_root[name] = item[1]
                            else:
                                if "," in item[1]:
                                    values = [tp(v) for v in item[1].split(",")]
                                    current_root[name] = values
                                else:
                                    current_root[name] = tp(item[1])
                        except Exception,e:
                            ## TODO handle datetime.date, datetime.datetime
                            ## if still log tp is None
                            ### ignore logging here  only useful for fix OMA mapping
                            #log.warn("can't convert %s, %s" % (item,tp))
                            current_root[name] = item[1]
        except Exception,e:
            log.exception(e)
            log.error("failed msg: %s" % msg)
            raise ValueError("parsing failed for %s" % msg)
        return root

    def toFormatedString(self,data=None, indent=0):
        """ from nvp dict to a formated string.

        recursively parsing data structure.
        """
        _data = data or self.root_
        #log.debug("data: %s" % data)
        assert _data and isinstance(_data,MultiDict.OrderedMultiDict)
        out = ""

        for k,v in _data.allitems():
            ## bug in jython v become _data when len(v) == 0
            #log.info("k: %s, v: %s" % (k,v))
            if isinstance(v,MultiDict.OrderedMultiDict) and len(v) != 0:
                out += "%s %s\n" % ("\t" * indent,k )
                out += self.toFormatedString(v,indent + 1)
            else:
                out += " %s %s\n" % ( "\t" *indent, (k,v))
        return out

    def __str__(self):
        return self.toFormatedString()

    def __getitem__(self,key):
        return self.root_[key]

    def get(self,key,default=None):
        return self.root_.get(key,default)

    def executionPoints(self):
        """ return executionPoints, as list. """
        assert self.root_
        assert isinstance(self.root_,MultiDict.OrderedMultiDict)





        try:
            execs = self.order.getall("OmaNvpExecutionPoint")
            return execs
        except Exception,e:
            return []

    def fixLineId(self):
        assert self.root_
        assert isinstance(self.root_,MultiDict.OrderedMultiDict)

        try:
            lineId = self.order.getall("OmaNvpFIXLineId")
            #('OmaNvpFIXLineId', 'BBRTEST.GSCO2')
            return lineId
        except Exception,e:
            return None

    @property
    def parentOrderId(self):
        assert self.root_
        assert isinstance(self.root_,MultiDict.OrderedMultiDict)

        rootParent  = self.order.get("RootParentWrapper")
        if rootParent:
            return (rootParent['OmaNvpUniqueTag'],rootParent['OmaNvpVersionNumber'])

    @property
    def orderId(self):
        assert self.root_
        assert isinstance(self.root_,MultiDict.OrderedMultiDict)
        return (self.order['OmaNvpUniqueTag'],self.order['OmaNvpVersionNumber'])

    @property
    def order(self):
        assert self.root_
        assert isinstance(self.root_,MultiDict.OrderedMultiDict)
        return self.root_.get('OmaOrder') or self.root_.get("OmaWave") or self.root_.get("OmaAggregateWave") or self.root_.get("OmaStandAloneExecution")

    @property
    def fill(self):
        assert self.root_
        assert isinstance(self.root_,MultiDict.OrderedMultiDict)
        return self.root_.get("OmaExecution")

    @property
    def executionId(self):
        if self.fill:
            return (self.fill['OmaNvpUniqueTag'],self.fill['OmaNvpVersionNumber'])


    @property
    def location(self):
        """ list all OmaLocationInformation.

        """
        ret = []
        for loc in self.order.getall("OmaLocationInformation"):
            system = loc["OmaNvpSystemName"]
            tag = loc['OmaNvpTag']
            tagDate = loc.get('OmaNvpTagDate')
            creator = loc.get('OmaNvpCreator')
            createTime = loc.get('OmaNvpCreationTime')
            ret.append(dict(system=system, 
                tag="%s%s"%(tag,tagDate) if tagDate else tag,
                creator=creator,
                createTime=createTime))

            return ret

    @property
    def omaStatus(self):
        """ oma status. """
        return self.order["OmaStatus"].items()


if __name__ == "__main__":
    """ unittest
    """

    data='106110OmaOrder126010qa_XTDb182015072910490231001140100291000.0106110ProductInformation106110ProductAliasList106110ProductAlias111001100310*CRADY106210ProductAlias106110ProductAlias111006100310RIO.AX148610AX166510SYDE106210ProductAlias106110ProductAlias111006100310RIO.CHA148610CHA166510CHIA106210ProductAlias106110ProductAlias1110032100310RIO AU166410AU106210ProductAlias106110ProductAlias1110032100310RIO AT166510SYDE106210ProductAlias106110ProductAlias111005100310AU000000RIO1106210ProductAlias106110ProductAlias1110022100310RIO148610AX166510SYDE106210ProductAlias106110ProductAlias1110031003106220103166410AU106210ProductAlias106210ProductAliasList111810RIO TINTO LIMITEDCMN-AU125010AUD141014161500146106110MarketMap106110Market170701161110SYDE168810N/A138291.0138391.0106210Market106110Market170702161110CHIA168810N/A138291.0138391.0106210Market106110Market170702161110NASD168810OTC13829100.01705010138391.0E-4106210Market106210MarketMap1454001637140169101000110839128110110710SYDE144600106210ProductInformation106110OmaLocationInformation103810qa_XTDb11471018104110DIAKOG1302122015072910391320150729-04:02:55104210DIAKOG113110DIAKOG115710qa_XTDb106210OmaLocationInformation106110OmaFeedSystems120410SYDEN/A12051111206142120700120910TSELINK12081012101101223110106210OmaFeedSystems1023001028100,25,281111104,83111210011611011109905140205102714210181101024141112410AUD1122140141514-110261320150930-00:00:00110710SYDE111910N/A1113140106110OmaStatus105114113109210qa_XTDb153310system11351620150808-11:00:10.5801317102015080810201411133101113610system215810qa_XTDb2015080813215900106210OmaStatus101190.0101290.0110290.0199000198990.0124090.0128890.0128990.0128290.0128390.0128490.012299-1.012309-1.01463111106110OmaCharge105010OmaCharge10961461098143109790.0106210OmaCharge106110PrimaryAccount1183140118110EAFC113891015321011831431181107340003001389101532101182142115210GSCO136610734000300EAFC1GSCO106210PrimaryAccount2180111218110Broker131490.0302410SS1967142190314-1106091000.0107790.0107990.0108190.019281001109140175310INST318510FC131891220150729100410Firm Order112010-1106110MarketDataList106110MarketDataInformation159791.373042159890.0117610USD117710AUD106790.0106890.0151990.0106990.0114490.0114590.0184800159910106210MarketDataInformation106210MarketDataList150190.0150291000.0150390.0150490.015061011505141106110OmaExchangeRate117610USD117710USD116891.0106210OmaExchangeRate131291000.0131390.0131590.0131690.0138291.0138391.0106110LocalRootParent103810qa_XTDb1147101813021220150729106210LocalRootParent165200101404101390.01577101628001578101624101626101702101703101649101651101531010165300152810Australia162900170400101910124290.0124390.010160-1192310197590.0197690.01831102180111141490.0138291.0174991000.0175090.0106210OmaOrder'

    nvpdata = NVPData(data)
    print nvpdata

    print nvpdata.executionPoints()
    print "SYDE" in nvpdata.executionPoints()


