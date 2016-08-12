""" query om2 priceStep rules from sybase.

GS wiki reference

http://om.wiki.services.gs.com/wiki/index.php/AUCEL_ControlLimits#How_to_disable_a_product_from_trading_using_StockLiquidity_Control

select *
from FlowSpecificTradingControls
where LimitKey like 'asia.stock.price-aggressive.eq1d-au-price-step.%.continuous'
;

"""
import logging

from connection_info import  DB_Conns,Sybase
from pprint import pprint
from collections import defaultdict

log = logging.getLogger("priceStepData")

AUCTION = ("PRE_CSPA","PRE_OPEN","CSPA","PRE_NR")

class PriceStepData:

    """ load OM2 priceStep rule data from db. """

    ## reuse connection, close at exit
    conn_info = DB_Conns['CONTROL_T1']
    conn_  = Sybase.connect(conn_info['server'],
                            conn_info['user'],
                            conn_info['pwd'],
                            conn_info['database'])

    def query_priceSteps_open(self, cache={}):
        """ return rule data from priceStep OPEN. """

        if 'rule' not in cache:

            cur = self.conn_.cursor()

            rules = defaultdict(dict)

            sql = """ select LimitKey,LimitSubKey,LimitVal
                        from FlowSpecificTradingControls
                        where LimitKey like 'asia.stock.price-aggressive.eq1d-au-price-step.%.continuous'
                        and IsActive = 1
                        order by LimitSubKey
            """

            cur.execute(sql)

            for r in cur.fetchall():
                k = r[0].split(".")
                #print k
                rules[r[1]][k[-2]] = r[2]
            cur.close()
            data =  sorted([(k,v) for (k,v) in rules.items()],key=lambda t: t[0],reverse=True)
            #import pdb;pdb.set_trace()
            cache['rule'] = data

        return cache['rule']


    def query_priceSteps_auction(self,cache={}):
        """ return rule data from priceStep AUCTION. """

        if 'rule' not in cache:

            cur = self.conn_.cursor()

            rules = defaultdict(dict)

            sql = """ select LimitKey,LimitSubKey,LimitVal
                        from FlowSpecificTradingControls
                        where LimitKey like 'asia.stock.price-aggressive.eq1d-au-segment-auction.%.auction'
                        and IsActive = 1
                        order by LimitSubKey
            """
            log.debug("price step auction: %s" % sql)

            cur.execute(sql)

            for r in cur.fetchall():
                k = r[0].split(".")
                #print k
                rules[r[1]][k[-2]] = r[2]
            cur.close()

            cache['rule'] = sorted([(k,v) for (k,v) in rules.items()],key=lambda t: t[0],reverse=True)

        return cache['rule']

    def query_per_last(self,state, cache={}):
        """ return rule data for per from last.

        asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.CHIA                               5.001           7
        asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.SYDE                               5.001           7
        asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.CHIA.exchange-open-auction-limit   5.001           7
        asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.SYDE.exchange-open-auction-limit   5.001           7
        asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.CHIA.exchange-close-auction-limit  5.001           7
        asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.SYDE.exchange-close-auction-limit  5.001           7

        """

        if 'rule' not in cache:

            cur = self.conn_.cursor()
            rules = {}
            if state == 'PRE_OPEN':
                sql = """ select LimitKey,LimitSubKey,LimitVal
                            from FlowSpecificTradingControls
                            where LimitKey like 'asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.SYDE.exchange-open-auction-limit'
                            and IsActive = 1
                            order by LimitSubKey
                """
            elif state == 'PRE_CSPA':
                sql= """ select LimitKey,LimitSubKey,LimitVal
                            from FlowSpecificTradingControls
                            where LimitKey like 'asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.SYDE.exchange-close-auction-limit'
                            and IsActive = 1
                            order by LimitSubKey
                """
            else:

                sql = """ select LimitKey,LimitSubKey,LimitVal
                            from FlowSpecificTradingControls
                            where LimitKey like 'asia.stock.price-aggressive.eq1d-au-segment-auction.aggressive-band-last.SYDE'
                            and IsActive = 1
                            order by LimitSubKey
                """
            cur.execute(sql)

            for r in cur.fetchall():
                k = r[0].split(".")
                #print k
                rules[r[1]] = r[2]

            cur.close()

            cache['rule'] = sorted([(k,v) for (k,v) in rules.items()],key=lambda t: t[0],reverse=True)

        return cache['rule']



    def find_rule_priceStep(self,price,state='OPEN'):
        """ return rule for price in continus trading.

        assume price in dollar.

        """
        if state.upper() in ('OPEN',):
            rules = self.query_priceSteps_open()
        elif state.upper() in AUCTION:
            rules = self.query_priceSteps_auction()
        else:
            ## unhandled state, CHA treat as OPEN
            rules = self.query_priceSteps_open()

        log.debug("rules: %s" % rules)
        log.info("find_rule_priceStep: %f, %s" % (price,state))

        for idx, rule in enumerate(rules):

            if price > rule[0]:
                log.info("found rule for price %f, : %s " % (price,str(rule)))
                return rule
        ## workaround 0.001 price
        if price > 0 and price <= 0.001:
            return rule[-1]

    def find_rule_per_last(self,price,state):
        """ return per from last %.  """

        rules = self.query_per_last(state)
        for idx, rule in enumerate(rules):

            if price > rule[0]:
                return rule

import atexit
atexit.register(PriceStepData.conn_.close)

if __name__ == "__main__":
    """

    (500.001,
    {'last-price-step-limit': 10.0,
    'overlap-price-step-limit': 100.0,
    'price-step-limit': 10.0}),

    (999.001,
    {'last-price-step-limit': 20.0,
    'overlap-price-step-limit': 200.0,
    'price-step-limit': 20.0})]

    """

    r = PriceStepData()

    #pprint(r.query_priceSteps_open())
    #pprint(r.query_priceSteps_auction())
    #pprint(r.query_per_last())

    pprint(r.find_rule_priceStep(0.02))
    pprint(r.find_rule_priceStep(2.3))


    pprint(r.find_rule_priceStep(34.5,state='AUCTION'))

    print r.find_rule_per_last(34.5)
    print r.find_rule_priceStep(0.002)
    print r.find_rule_priceStep(0.001)
