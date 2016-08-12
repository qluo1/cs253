""" query om2 liquidity rules from sybase.

GS wiki reference

http://om.wiki.services.gs.com/wiki/index.php/AUCEL_ControlLimits#How_to_disable_a_product_from_trading_using_StockLiquidity_Control

select * from TradingControls..FlowSpecificTradingControls
where LimitKey like '%eq1d-size-notional-product%'
;

"""
import logging

from connection_info import  DB_Conns,Sybase
from pprint import pprint
from collections import defaultdict

log = logging.getLogger("liquidityRules")


class LiquidityRules:

    """ load OM2 priceStep rule data from db. """

    def __init__(self, conninfo= DB_Conns['CONTROL_T1']):
        """ init. """
        self.conn_info = conninfo
        print self.conn_info['server'], self.conn_info['user'], self.conn_info['pwd'],self.conn_info['database']
        self.conn_  = Sybase.connect(self.conn_info['server'],
                                     self.conn_info['user'],
                                     self.conn_info['pwd'],
                                     self.conn_info['database'])


    def query_liquidity_rules(self, cache={}):
        """ return rule data for all liquidity. """

        if 'rule' not in cache:

            cur = self.conn_.cursor()

            rules = {}

            sql = """ select LimitKey,LimitVal
                        from FlowSpecificTradingControls
                        where LimitKey like '%eq1d-size-notional-product%'
                        and IsActive = 1
                        order by LimitSubKey
            """

            cur.execute(sql)

            for r in cur.fetchall():
                k = ".".join(r[0].split(".")[-2:])
                #print k
                rules[k] = r[1]
            cur.close()
            #log.info("total liquidity rules: %d" % len(rules))
            cache['rule'] =  rules
            self.conn_.close()

        return cache['rule']


    def lookup_rule(self,symbol):
        """ return rule based on symbol. """

        symbol = symbol.upper()

        rules = self.query_liquidity_rules()

        if symbol in rules:
            return rules[symbol]
        else:
            if symbol.endswith(".AX"):
                return rules['notional-local.SYDE']
            if symbol.endswith(".CHA"):
                return rules['notional-local.CHIA']

        print "symbol: %s not found" % symbol
        return 0.0



if __name__ == "__main__":

    rules = LiquidityRules()

    data = rules.query_liquidity_rules()

    #pprint(data)
    print len(data.keys())

    print "WOW.AX", rules.lookup_rule("WOW.AX")
    print "CBA.CHA", rules.lookup_rule("CBA.CHA")
    print "CBA", rules.lookup_rule("CBA")
    print "junk.AX", rules.lookup_rule("JUNK.AX")


