""" convert MDT quote update into a in-memory quote snapshot.

TODO :
- capture trades ?? broker/xref

"""
import copy
from cfg import json
from bson import json_util
from collections import namedtuple,deque
from datetime import datetime
import logging

log = logging.getLogger(__name__)

## ASX status map to MDT code
state_map = {
    "PRE_OPEN":     "POP",
    "OPEN":         "OPN",
    "PRE_CSPA":     "pOQ",
    "CSPA":         "AUC",
    "ADJUST":       "AUT",
    #ADJUST-ON	AUT
    "PURGE_ORDERS": "SC",
    #"SYSTEM-MAINTENANCE	SC
    "CLOSE":        "CLS",
    "LATE_TRADING":	"FAS",
    "SUSPEND":      "SUS",
    "PRE_NR":       "NDR",
    "TRADING_HALT": "TH",
    "REG_HALT":     "HRS",
    "ENQUIRE":      "NQ",
    "OPEN_NIGHT_TRADING":   "OVR",
    #"PRE-NIGHT-TRADING":    "pOQ",
    "INTERNATIONAL_HALT":   "AIS",
}


def lookup_state(code):
    """ from MDT code to ASX status, return ASX status code.  """
    for k, v in state_map.items():
        if code == v:
            return k

def convert_depth(depth):
    """ convert deque in depth back to tuple. """
    assert isinstance(depth,dict)
    for k in depth.keys():
        v = depth[k]
        if isinstance(v,dict):
            depth[k] = convert_depth(v)
        if isinstance(v,deque):
            if v[0][0] == 0:
                depth.pop(k)
            else:
                depth[k] = v[0]
    return depth

## basic quote class to parse and capture current snapshot
BID = namedtuple("BID", "bid,bidSize,numBids,undisclose")
ASK = namedtuple("ASK", "ask,askSize,numAsks,undisclose")

class Quote:

    """ represent a single quote for MDT update.

    - parse each MDT quote data
    - IMAGE, new snapshot
    - UPDATE update quote based on trade or quote changes

    """

    def __init__(self,**kw):
        """ initialize a quote."""

        if 'symbol' in kw:
            self.symbol = kw['symbol']
        else:
            self.symbol = None
        if 'category' in kw:
            self.category = kw['category']
        else:
            self.category = ""

        self.name        = ""
        self.status      = None
        self.close       = None
        self.hstclsdate  = None
        self.tradeDate   = None
        self.tradeTime   = None
        self.bid         = None
        self.ask         = None
        self.last        = None
        self.turnover    = None
        self.vwap        = None
        self.state       = None
        self.open        = None
        self.high        = None
        self.low         = None
        self.match       = None
        self.timestamp   = None
        self.hstclsdateclose = None
        ## capture depth
        self.depth = {'ask': {},
                      'bid': {},
                      }
        ## image update timestamp
        self.image_timestamp = None

    def parse(self,data):
        """ parsing MDS data into quote. return self. """

        log.debug("parsing: %s" % data)
        try:
            if data["IMAGE"] == "IMAGE":
                """
                    for initial snapshot
                """
                ##reset quote
                self.name = data['DSPLY_NAME']
                self.symbol = data['SYMBOL']
                self.hstclsdateclose  = data['ADJUST_CLS']
                self.hstclsdate = data['HSTCLSDATE']
                self.open = data.get("OPEN_PRC")
                self.high = data.get("HIGH_1")
                self.low = data.get("LOW_1")
                if "ADJUST_CLS" in data:
                    self.close = data["ADJUST_CLS"]

                ## if last trade , set last as last trade price
                if "TRDPRC_1" in data and data['TRDPRC_1'] > 0:
                    self.last = data['TRDPRC_1']
                else:
                    # default to close
                    self.last = self.close
                self.turnover = data.get('TURNOVER') or data.get('TRNOVR_LNG')
                self.vwap = data.get('VWAP') or data.get("VWAP_LONG")
                ## capture image timestamp
                self.image_timestamp = datetime.now()

            if data["IMAGE"] == "UPDATE":
                """
                    for update
                """
                if self.image_timestamp is None:
                    log.warn("update received but image hasn't been refreshed: %s" % self.toJson())
                ## update quote based on trade
                if 'TRADE_ID' in data:
                    ## handle trade
                    # 'ACT_FLAG1': 'S',
                    # 'ACVOL_1': 82992.0,
                    # 'ACVOL_SC': '     ',
                    # 'ASK_ORD_ID': '5A8A728300025179',
                    # 'A_DEAL_SRC': 1.0,
                    # 'BID_ORD_ID': '5A8A728300025160',
                    # 'B_DEAL_SRC': 1.0,
                    # 'DC_POS': 3.0,
                    # 'EXT_TR_PRC': 2.54,
                    # 'EX_ORD_TYP': 0.0,
                    # 'FLOOR_VOL': 82992.0,
                    # 'GEN_VAL4': 2.54,
                    # 'GV4_TEXT': 'XT',
                    # 'IMAGE': 'UPDATE',
                    # 'NETCHNG_1': 0.06,
                    # 'NUM_MOVES': 80.0,
                    # 'PCTCHNG': 2.419355,
                    # 'PRCTCK_1': '\xde',
                    # 'SALTIM': '02:59:59.0',
                    # 'SALTIM_MS': 10799822L,
                    # 'SCHEMAID': 38,
                    # 'SEQNUM': 3476.0,
                    # 'STATUS': 'STATE_OK',
                    # 'SYMBOL': 'NHC.AX',
                    # 'TD_RPT_CDE': 0.0,
                    # 'TRADE_DATE': '2/17/2015',
                    # 'TRADE_ID': '1830003476',
                    # 'TRDPRC_1': 2.54,
                    # 'TRDVOL_1': 1.0,
                    # 'TRD_IND_1': '2',
                    # 'TURNOVER': 210845.0,
                    # 'VOL_X_PRC1': 2.540542,
                    # 'VWAP': 2.540542}
                    if 'TRDPRC_1' in data:
                        self.last = data['TRDPRC_1']
                        self.turnover = data.get('TURNOVER') or data.get("TRNOVR_LNG")
                        self.vwap = data.get('VWAP') or data.get("VWAP_LONG")
                        self.tradeDate = data.get("TRADE_DATE")
                        self.tradeTime = data.get("SALTIM")

                        ## update high / low
                        if self.high and self.last > self.high:
                            self.high = self.last
                        if self.low and self.last < self.low:
                            self.low = self.last
                        if self.high is None:
                            self.high = self.last
                        if self.low is None:
                            self.low = self.last
                    ## CANCEL Trade
                    elif 'IRGVOL' in data:
                        ## busted trade
                        """data: {'TD_RPT_CDE': 0.0,
                                  'TRD_IND_1': '2', 'BDEALSRC_C': 1.0, 'SYMBOL': 'RIM.AX',
                                  'GV4_TEXT': 'C*XT', 'ACVOL_SC': '     ', 'IRGVOL': 100.0,
                                  'BTRDTYP_C': 4.0, 'SCHEMAID': 38, 'TIMCOR': '23:59:30.0',
                                  'VOL_X_PRC1': 4.9406300000000005, 'TIMCOR_MS': 86370883L,
                                  'IMAGE': 'UPDATE', 'VWAP': 4.9406300000000005, 'EX_ORD_TYP': 0.0,
                                  'STATUS': 'STATE_OK', 'DC_POS': 1.0, 'GV1_TIME': '23:59:57.0',
                                  'FLOOR_VOL': 20651.0, 'ADEALSRC_C': 1.0, 'EXT_TR_PRC': 4.92, 'SEQNUM': 815.0,
                                  'ACVOL_1': 20651.0, 'ASKID_CNL': '5ABBAA81000102AB', 'TRADE_ID': '1310000809',
                                  'ATRDTYP_C': 4.0, 'BIDID_CNL': '5ABBAA810001024C', 'GEN_VAL4': 4.92, 'TURNOVER': 102029.0}
                                  """
                        log.info("ignore busted trade:%s" % data['TRADE_ID'])
                        self.turnover = data.get('TURNOVER') or data.get("TRNOVR_LNG")
                        self.vwap = data.get('VWAP') or data.get("VWAP_LONG")
                        pass
                    else:
                        log.error("unknown trade: %s" % data)

            #########################################
            ## common fields
            #########################################
            ## trading status (normal/halt/suspension
            if 'PRC_QL_CD' in data:
                self.state = lookup_state(data['PRC_QL_CD'])
            ## indicative price
            if 'GEN_VAL6' in data:
                self.match = data['GEN_VAL6']
            if 'OFFC_CODE2' in data:
                self.isin = data['OFFC_CODE2']

            if 'STATUS' in data:
                self.status = data['STATUS']
                self.status = data["STATUS"]
            if 'SYMBOL' in data:
                self.symbol = data["SYMBOL"]

            ## update bid/ask
            if 'ASK' in data:
                self.ask = ASK(data['ASK'],data['ASKSIZE'],data.get('NO_ASKMMKR'),data.get("ASK_TONE"))
            if 'BID' in data:
                self.bid = BID(data['BID'],data['BIDSIZE'],data.get('NO_BIDMMKR'),data.get("BID_TONE"))

            ## update timestamp
            self.timestamp = datetime.now()
            if self.bid is None or self.ask is None:
                log.warn("parsing quote failed: %s" % self.toJson())
            return self

        except Exception, e:
            ## handle parsing error here
            log.error("parsing error: %s, data: %s" % (e, data))
            log.exception(e)


    def parse_depth(self,data):
        """  parsing depth.

        DEBUG 2016-06-20 14:50:06,199 marketQuoteService 8247 MainThread full deth: {'BID_TIME': '03:45:38.412000', 'STATUS': 'STATE_OK', 'NO_L2_ROWS': 25, 'RDNDISPLAY': 117, 'PROD_PERM': 4222, 'OFFCL_CODE': 'ABP', 'B_DISQY_1': ' ', 'BID_TIM_MS': 13538412, 'B_NPLRS_1': 1.0, 'RDN_EXCHID': '   ', 'LOT_SIZE': 1.0, 'CURRENCY': 'AUD', 'QUOTIM_MS': 13538412, 'B_PRICE_1': 3.2, 'B_QTY_1': 12000.0, 'SYMBOL': 'ABP.CHAd', 'SCHEMAID': 62, 'RDN_EXCHD2': 'CHA', 'PREF_DISP': 5540, 'RECORDTYPE': 113, 'OFF_CD_IND': 'AUS', 'PROV_SYMB': 'ABP', 'MNEMONIC': 'ABP', 'TRD_UNITS': '3DP ', 'IMAGE': 'IMAGE'}

        DEBUG 2016-06-20 14:50:48,207 marketQuoteService 8247 MainThread full deth: {'NO_L2_ROWS': 25, 'RDNDISPLAY': 117, 'B_NPLRS_12': 6.0, 'B_NPLRS_10': 2.0, 'B_NPLRS_11': 1.0, 'PROD_PERM': 27, 'OFFCL_CODE': 'BHP', 'B_NPLRS_4': 2.0, 'B_NPLRS_5': 1.0, 'B_NPLRS_6': 1.0, 'B_NPLRS_7': 1.0, 'B_NPLRS_1': 3.0, 'B_NPLRS_2': 4.0, 'B_NPLRS_3': 1.0, 'RDN_EXCHID': 'ASX', 'B_NPLRS_8': 1.0, 'B_NPLRS_9': 1.0, 'B_PRICE_12': 1.23, 'B_PRICE_10': 10.0, 'B_PRICE_11': 8.88, 'B_QTY_11': 1.0, 'B_QTY_10': 101.0, 'B_PRICE_9': 12.34, 'CURRENCY': 'AUD', 'A_QTY_2': 110000.0, 'A_QTY_3': 10577.0, 'A_QTY_1': 680971.0, 'A_QTY_6': 10.0, 'A_QTY_4': 1000.0, 'A_QTY_5': 10.0, 'B_PRICE_8': 16.8, 'B_PRICE_1': 19.05, 'B_PRICE_2': 18.900000000000002, 'B_PRICE_3': 18.88, 'B_PRICE_4': 18.85, 'B_PRICE_5': 18.55, 'B_PRICE_6': 18.22, 'B_PRICE_7': 18.18, 'B_QTY_9': 1.0, 'B_QTY_8': 1.0, 'B_QTY_1': 113.0, 'B_QTY_3': 100.0, 'B_QTY_2': 1119.0, 'B_QTY_5': 1.0, 'B_QTY_4': 1010.0, 'B_QTY_7': 1555.0, 'SYMBOL': 'BHP.AXd', 'SCHEMAID': 62, 'RDN_EXCHD2': 'ASX', 'A_NPLRS_3': 2.0, 'A_NPLRS_2': 2.0, 'A_NPLRS_1': 7.0, 'A_NPLRS_6': 1.0, 'A_NPLRS_5': 1.0, 'A_NPLRS_4': 1.0, 'PREF_DISP': 4100, 'B_QTY_12': 6.0, 'A_PRICE_3': 19.1, 'A_PRICE_1': 19.06, 'A_PRICE_6': 22.0, 'A_PRICE_5': 20.0, 'A_PRICE_4': 19.150000000000002, 'OFF_CD_IND': 'AUS', 'PROV_SYMB': 'BHP', 'STATUS': 'STATE_OK', 'A_PRICE_2': 19.080000000000002, 'RECORDTYPE': 113, 'TRD_UNITS': '3DP ', 'B_QTY_6': 1557.0, 'IMAGE': 'IMAGE'}
        """
        assert isinstance(data,dict)
        log.debug("full depth: %s" % data)

        def filter_items(data,prefix):
            """ helper to extract relevent items."""
            assert isinstance(data,dict)
            return {int(k[len(prefix):]):v for k,v in data.iteritems() if k.startswith(prefix)}

        try:
            symbol = data['SYMBOL']
            state  = data['STATUS']
            image = data['IMAGE']
            assert symbol == self.symbol + "d"
            ## extract ask
            ask_prices = filter_items(data,"A_PRICE_")
            ask_qtys = filter_items(data,"A_QTY_")
            ask_tones = filter_items(data,"A_TONE_")
            no_asks = filter_items(data,"A_NPLRS_")
            ## enrich bid ask tone for undisclosed
            for k,v in ask_tones.iteritems():
                if v != 0 and ask_qtys[k] == 0:
                    ask_qtys[k] = v
            ##################

            ## extract bid
            bid_prices = filter_items(data,"B_PRICE_")
            bid_qtys = filter_items(data,"B_QTY_")
            bid_tones = filter_items(data,"B_TONE_")
            ## enrich bid tone for undiscolosed.
            for k,v in bid_tones.iteritems():
                if v != 0 and bid_qtys[k] == 0:
                    bid_qtys[k] = v
            no_bids = filter_items(data,"B_NPLRS_")

            ## update ask depth
            for k,v in ask_prices.iteritems():
                if k not in self.depth['ask']:
                    self.depth['ask'][k] = deque(maxlen=1)
                self.depth['ask'][k].append((v, ask_qtys[k],no_asks[k]))

            ## update bid depth
            for k,v in bid_prices.iteritems():
                if k not in self.depth['bid']:
                    self.depth['bid'][k] = deque(maxlen=1)
                self.depth['bid'][k].append((v,bid_qtys[k],no_bids[k]))

            if len(bid_prices) or len(ask_prices):
                log.info("depth updated: %s, %s" % (self.symbol,convert_depth(copy.deepcopy(self.depth))))

        except Exception,e:
            log.exception(e)

    def __str__(self):
        """ return string repr. """

        if self.symbol:
            return "symbol: %s, bid: %s, ask: %s, close: %s, status: %s, last: %s, vwap: %s, state: %s, timestamp: %s" % \
                (self.symbol, self.bid,self.ask,self.close,self.status,self.last, self.vwap,self.state, self.timestamp)

    def toJson(self):
        """ return json string repr. 

        using bson to handle datetime
        """
        return json.dumps(self.toData(),default=json_utils.default)

    def toData(self):
        """ return json string repr.  """

        bids = sorted([bid[0] for bid in self.depth['bid'].values() if bid[0][0] != 0],key=lambda x:x[0])
        asks = sorted([ask[0] for ask in self.depth['ask'].values() if ask[0][0] != 0],key=lambda x:x[0])

        return dict(name   = self.name,
                     symbol = self.symbol,
                     bid    = self.bid._asdict() if self.bid else None,
                     ask    = self.ask._asdict() if self.ask else None,
                     last   = self.last,
                     close  = self.close,
                     status = self.status,
                     vwap   = self.vwap,
                     turnover = self.turnover,
                     state  = self.state or '',
                     open   = self.open,
                     high   = self.high,
                     match  = self.match,
                     timestamp =  self.timestamp if self.timestamp else None,
                     imgTimestamp = self.image_timestamp if self.image_timestamp else None,
                     hstclsdate = self.hstclsdate,
                     hstclsdateclose = self.hstclsdateclose,
                     tradeDate = self.tradeDate,
                     depth  = {'bid': bids,
                               'ask': asks,
                               }
                )

