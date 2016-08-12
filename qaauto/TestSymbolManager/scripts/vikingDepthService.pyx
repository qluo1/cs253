import threading
import random
import logging
import random
from datetime import datetime,timedelta
from dateutil import parser
import gevent
#from gsatest.conf import settings
from utils import tickSize
from vikingOrder import VikingOrder
from utils import FAK,DAY

log = logging.getLogger(__name__)

#from localconf import MARK_XREF,DEPTH_XREF,SETUP_DEPTH_DELAY
## default account for clear depth
MAX_SPREAD = 2
## less than 5m, i.e. FFL
MAX_VALUE = 3500000
#MARK_QTY = 888
MARK_QTY = None
MAX_TRY = 5
MARK_XREF = "W"
## delay for market data refreshed.
SETUP_DEPTH_DELAY = 2

from collections import defaultdict


def active_wait_timeout(fn, timeout=3.0):
    """ """

    assert hasattr(fn,'__call__')
    ## initial check
    if fn() == True:
        return
    start = datetime.now()
    while True:
        if fn():
            break
        now = datetime.now()
        if (now - start).total_seconds() > timeout:
            log.warn("timeout, %s, fn: %s " % (timeout,fn()))
            break
        gevent.sleep(0.01)


class DepthSytle:

    """ depth style. """

    ASXONLY = 0
    MIXED = 1
    ASXCHIA = 2  # ASX/Buy, CHIA/Sell
    CHIAASX = 3  # CHIA/Buy, ASX/Sell
    CHIAONLY = 4
    MIRROR = 5 ## setup CHIA mirror ASX

class VkDepth(object):

    """ viking depth service.

    clear and build depth for specified symbol/last price.

    """

    _orders = defaultdict(list)

    def __init__(self, snapshot):
        """ """
        ## hold a market symbol snapshot.
        self._market_snapshot_ = snapshot

    def _clear_one_side(self,order_t,side,last,exch,force=False):
        """ clear one side of depth, return True/False. """

        order = order_t.copy()
        ## to clear depth: buy high/sell low
        price = last + tickSize(last,MAX_SPREAD) if side == 'Buy' else  last - tickSize(last,MAX_SPREAD)
        max_qty = int(MAX_VALUE/ price) - 1
        ## in case price less than 0
        assert  price > 0
        ### get current depth info 
        symbol = order['symbol']
        ## query quote again
        asx_quote,cha_quote = self._get_symbol_quote(symbol)
        if exch == "SYDE":
            cur_quote = asx_quote
        else:
            cur_quote = cha_quote

        if side == "Buy":
            cur_depth_price, cur_depth_size = cur_quote['ask']['ask'], cur_quote['ask']['askSize']
        else:
            cur_depth_price, cur_depth_size  = cur_quote['bid']['bid'],cur_quote['bid']['bidSize']
        ## default clear lit
        clear_lit = True
        if side == "Buy":
            ## clear sell side, 
            if (cur_depth_price == 0 or cur_depth_price > price):
                clear_lit = False
        else:
            ## clear buy side
            if (cur_depth_price == 0 or cur_depth_price < price):
                clear_lit = False

        log.debug("clear_lit: %s, side: %s, cur_quote: %s , price : %s" %( clear_lit,side,cur_quote, price))
        ## sor/IOC order for clear depth
        order.update({'side':side,
                  'price':price,
                  'qty':max_qty,
                  'allOrNone':False,
                  'tif':"ImmediateOrCancel",
                  'exch': exch})

        ############################################
        ## conditional clear lit 
        if clear_lit or force:
            done = False
            count = 0
            while not done:
                count += 1
                the_order = VikingOrder()
                if the_order.new(**order):
                    active_wait_timeout(lambda: 'VikingDoneForDay' in the_order.acks)
                    if the_order.filledQty == 0:
                        done = True
                else:
                    log.debug("_clear_one_side: %d, %s, %s, %s" % (count,side,the_order,the_order._acks))
                    raise ValueError("new vk order failed: %s, %s" % (the_order,the_order._acks))

                if count > MAX_TRY:
                    raise ValueError("too many retries for order: %s" % order)

        #############################################
        ## always clear dark
        ## CP-Market/IOC order for clear depth
        order["orderType"] = "Pegged"
        order["pegType"] = "Ask" if order["side"] == "Buy" else "Bid"
        done = False
        count = 0
        while not done:
            count += 1
            the_order = VikingOrder()
            if the_order.new(**order):
                active_wait_timeout(lambda: 'VikingDoneForDay' in the_order.acks)
                if the_order.filledQty == 0:
                    done = True
            else:
                log.debug("_clear_one_side: %d, %s, %s, %s" % (count,side,the_order,the_order._acks))
                raise ValueError("new vk order failed: %s, %s" % (the_order,the_order._acks))

            if count > MAX_TRY:
                raise ValueError("too many retries for order: %s" % order)

        return True

    def _prepare_asx_depth(self,pid,order_t,spread):
        """ establish ASX depth, with passive bid/ask.

        to clear CP market, it need bid/ask available in ASX depth.

        """
        symbol = order_t['symbol']
        asx_quote, cha_quote = self._get_symbol_quote(symbol)
        last = asx_quote['last']

        buyPrice = last - tickSize(last,spread)
        sellPrice = last + tickSize(last,spread)

        ORDER_QTY = 60000

        ## sor/IOC order for clear depth
        buyOrder = {'side':"Buy",
                    'price':buyPrice,
                    'qty': ORDER_QTY,
                    'tif':"Day",
                    'exch': "SYDE"}
        buyOrder.update(order_t)

        sellOrder = {'side':"Sell",
                     'price':sellPrice,
                     'qty': ORDER_QTY,
                     'tif':"Day",
                     'exch': "SYDE"}
        sellOrder.update(order_t)
        ##establish  buy side
        buy = VikingOrder()
        sell = VikingOrder()

        if buy.new(**buyOrder) and \
           sell.new(**sellOrder) and \
           buy.filledQty  < ORDER_QTY and \
           sell.filledQty < ORDER_QTY :
           self._orders[pid].append(buy)
           self._orders[pid].append(sell)
           return True
        else:
            ## clean up, error occurred.
            log.warn("prepare depth cancel buy order: %s, %s" % (buy, buy._acks))
            buy.cancel()
            log.warn("prepare depth cancel sell order: %s, %s" % ( sell,sell._acks))
            sell.cancel()
        return False

    def _setup_depth(self,pid,order_t,last,tick,style):
        """ internal helper to build market depth based spec, return True/False.

        input:
            - order template
            - last price
            - tick spread

        build depth with asx/bid, chia/ask

        """
        buy = order_t.copy()
        sell = order_t.copy()

        if tick >= 1:

            buy.update({'side':'Buy',
                        'price':last-tickSize(last,tick),
                        'qty':MARK_QTY or random.randint(800,900),
                        'tif': DAY })
            sell.update({'side':'Sell',
                        'price':last+tickSize(last,tick),
                        'qty':MARK_QTY or random.randint(800,900),
                        'tif': DAY })

        else:
            buy.update({'side':'Buy',
                        'price':last,
                        'qty':MARK_QTY or random.randint(800,900),
                        'tif': DAY})
            sell.update({'side':'Sell',
                        'price':last+tickSize(last,1),
                        'qty':MARK_QTY or random.randint(800,900),
                        'tif': DAY})

        ## setup depeth spread in style
        if style == DepthSytle.MIXED:
            buy['exch'] = random.choice(['SYDE','CHIA'])
            sell['exch'] = random.choice(['SYDE','CHIA'])
        elif style == DepthSytle.CHIAONLY:
            buy['exch'] = sell['exch'] = 'CHIA'
        elif style == DepthSytle.ASXCHIA:
            buy['exch'] = 'SYDE'
            sell['exch'] = 'CHIA'
        elif style == DepthSytle.CHIAASX:
            buy['exch'] = 'CHIA'
            sell['exch'] = 'SYDE'
        else:
            buy['exch'] = 'SYDE'
            sell['exch'] = 'SYDE'

        ## buy
        buy_order = VikingOrder()
        sell_order = VikingOrder()
        done =  buy_order.new(**buy) and sell_order.new(**sell)
        ## setup mirror for CHA
        if style == DepthSytle.MIRROR:
            ## mirror CHIA
            buy['exch'] = 'CHIA'
            sell['exch'] = 'CHIA'
            sell_order_cxa = VikingOrder()
            buy_order_cxa = VikingOrder()
            done = done and buy_order_cxa.new(**buy) and sell_order_cxa.new(**sell)

        if done :
            ## track for clean up
            self._orders[pid].append(buy_order)
            self._orders[pid].append(sell_order)
        else:
            log.warn("cancel buy order: %s, %s" %(buy_order,buy_order._acks))
            buy_order.cancel()
            log.warn("cancel sell order: %s, %s" % ( sell_order,sell_order._acks))
            sell_order.cancel()
            return False

        log.debug("_setup_depth %s, %s" % (buy_order,sell_order))
        return done

    def _mark_last(self,order_t,last,timeout=1.0):
        """ make a trade to preserve last price, return True/False.

        input: order template
            last price
            DSS watcher

        """
        buy = order_t.copy()
        sell = order_t.copy()
        buy.update({'side':'Buy', 'price':last,'qty':1,'tif': DAY ,'exch':'SYDE'})
        sell.update({'side':'Sell', 'price':last,'qty':1,'tif': DAY,'exch': 'SYDE'})

        ## work around UCP trade
        if MARK_XREF:
            buy['xref'] = MARK_XREF
            sell['xref'] = MARK_XREF

        buy_order = VikingOrder()
        sell_order = VikingOrder()
        assert buy_order.new(**buy)
        assert sell_order.new(**sell)
        log.debug("_mark_last: %s, %s" % (buy_order,sell_order))
        ##active waiting for orderFill
        active_wait_timeout(lambda: buy_order.filledQty != 0,timeout=5.0)
        ## check fill sucessful
        if buy_order.filledQty == sell_order.filledQty == 1:
            return True
        raise ValueError("fail to mark last. buy:%s, sell:%s" %(buy_order.filledQty, sell_order.filledQty))

    def _get_symbol_quote(self,symbol):
        """ for symbol return market quote for asx/chia. """

        assert self._market_snapshot_
        if "." in symbol:
            ticker,exch = symbol.split(".")
        else:
            ticker = symbol

        asx_ticker = ticker + ".AX"
        cha_ticker = ticker + ".CHA"
        ## give greenlet thread a chance to run
        gevent.sleep(0)
        assert asx_ticker in self._market_snapshot_ and cha_ticker in self._market_snapshot_

        asx_quote = self._market_snapshot_[asx_ticker][0]
        cha_quote = self._market_snapshot_[cha_ticker][0]

        return (asx_quote, cha_quote)

    def clear_depth(self,pid,**kwargs):
        """ clear depth based on spec, return True/False for internal error.

        input: symbol, last
        """
        symbol  = kwargs['symbol']
        build   = kwargs.get('build') or False
        tick    = kwargs.get("tick") or 2  # default tick spread 2 tick each side
        style   = kwargs.get("style") or DepthSytle.ASXONLY

        asx_quote, cha_quote = self._get_symbol_quote(symbol)
        last = asx_quote['last']
        ## force clear depth if quote too old.
        timestamp = asx_quote['timestamp']
        force = datetime.now() - timestamp > timedelta(hours=8)
        log.info("clear_depth: %s, %s, %s" % (kwargs, asx_quote,cha_quote))

        if not symbol and last:
            raise ValueError("symbol[%s] & last price[%s] required!" % (symbol,last))

        xref    = kwargs.get('xref') or "X"
        ## last great than 5c
        assert last > 0.05

        # order template
        order_t = dict(symbol=symbol,
                        xref=xref
                        )

        ## multi thread cause RPC call failed.
        done = False
        ##cleanup any outstanding order from previous setup depth.
        self.cleanup_orders(pid)
        ## prepare passive bid/ask before clear depth, need to clear ASX CP.
        if not self._prepare_asx_depth(pid,order_t,MAX_SPREAD + 1):
            raise ValueError("Fail to prepare passive depth")

        # clear depth
        if random.random() > 0.45:
            # push last up
            done = self._clear_one_side(order_t,'Sell',last,"CHIA") and \
                   self._clear_one_side(order_t,'Buy',last,"CHIA") and \
                   self._clear_one_side(order_t,'Sell',last,"SYDE",force) and \
                   self._clear_one_side(order_t,'Buy',last,"SYDE",force)
        else:
            # push last down
            done = self._clear_one_side(order_t,'Buy',last,"CHIA") and \
                   self._clear_one_side(order_t,'Sell',last,"CHIA") and \
                   self._clear_one_side(order_t,'Buy',last,"SYDE",force) and \
                   self._clear_one_side(order_t,'Sell',last,"SYDE",force)
        ## cancel prepare asx depth outstanding orders.
        self.cleanup_orders(pid)

        # preserve last price
        if done and self._mark_last(order_t,last):
            done = True

        # if all good, then build depth
        if done and build:
            done = self._setup_depth(pid,order_t,last,tick,style)
            ## if build depth, need delay for depth quote data being reflected
            gevent.sleep(SETUP_DEPTH_DELAY)

        return done

    def cleanup_orders(self,pid):
        """ clean up resting orders. """

        for order in self._orders[pid]:
            log.debug("cleanup_orders: %s" % order)
            order.cancel()
        self._orders[pid] = []

