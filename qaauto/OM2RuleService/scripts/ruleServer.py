import os
import sys
import logging
import logging.config
## local project settings
import cfg
from conf import settings
import zerorpc
import gevent
from treelib import Tree

log = logging.getLogger("ruleService")
logging.config.dictConfig(settings.LOGGING)

from extract_flowTradingControl import (
                     find_priceStep,            ## one api -- load from folder or from sybase
                     load_rule_tree,            ## local local tree
                     #parsing_controls,          ## helper
                     find_rule_priceStep,       ## loal rule from local tree.
                     get_db_sizeLimits_item,    ## helper query sybase for sizeLimit.
                     gen_db_priceControl_item,  ## helper lod sybase price item.
                    )

## load RDS from json snapshot file
from load_snapshot import RDS_Snapshot

class RDSRuleServer(zerorpc.Server):
    """
    """
    ## price limit 
    tree_ = None
    ## size limit
    sizeLimits_ = None

    snapshots_ = {}

    def find_price_step(self,price,rule_tag,**kw):
        """
        """
        log.info("find price step: %s, %s, %s" %(price,rule_tag,kw))

        if self.tree_ == None:
            raise ValueError("dataset hasn't been loaded. call load_sybase or load_snapshot first.")

        return find_rule_priceStep(self.tree_,price,rule_tag=rule_tag,**kw)

    def load_snapshot(self,**kw):
        """ load priceStep and sizeLimits from snapshot for specified test envrionment,default PME_RDS.  """
        env = kw.get("env","PME_RDS")
        dump = kw.get("dump",False)
        with_data = kw.get("with_data",False)

        if env not in settings.OM2_PATHS:
            raise ValueError("RDS env not found: %s" % env)

        if env not in self.snapshots_:
            ## load rds from json 
            self.snapshots_[env] = RDS_Snapshot(env)

        data = self.snapshots_[env].rds_control

        self.sizeLimits_ = data['size']
        self.tree_ = data['price'].subtree("asia.stock.price-aggressive")
        ignore_tags =['JPNX','TKYO','HKGE','GEM','CHIJ','XSSC','SIX']
        ## dump for debug.
        if dump:
            self.tree_.dump_tree("price-tree-%s" % env,ignore_tags=ignore_tags)
            self.tree_.dump_tree("price-tree-data-%s" % env,with_data=True,ignore_tags=ignore_tags)
        return self.tree_.to_dict(with_data=with_data,ignore_tags=ignore_tags)

    def load_snapshot_account(self,**kw):
        """ return snapshot rds account."""
        env = kw.get("env","PME_RDS")

        if env not in settings.OM2_PATHS:
            raise ValueError("RDS env not found: %s" % env)
        ## load rds from json 
        if env not in self.snapshots_:
            ## load rds from json 
            self.snapshots_[env] = RDS_Snapshot(env)

        data = self.snapshots_[env].rds_account
        return data

    def load_sybase(self,**kw):
        """ load priceStep and sizeLimits from sybase. """

        dump = kw.get("dump",False)
        with_data = kw.get("with_data",False)
        return_data = kw.get("return",False)

        tree = Tree()
        count = 0
        for item in gen_db_priceControl_item():
            #print item
            keys = item.pop("LimitKey").split(".")
            ## patch symbol
            if keys[-1] in ("AX","CHA"):
                keys = keys[:-2] + [keys[-2] + "." + keys[-1]]

            #print keys, item
            ## patch sybase to snapshot
            limitVal = item.pop("LimitVal")
            item['LimitValue'] = limitVal
            if "LimitStr" in item:
                limitStr = item.pop("LimitStr")
                item['LimitValueStr'] = limitStr.strip()

            tree.add_node_from_list(keys,item)
            count +=1
        ignore_tags =['JPNX','TKYO','HKGE','GEM','CHIJ','CXAD','XSSC','SIX']
        log.info("total item loaded: %s" % count)
        self.tree_ =tree.subtree("asia.stock.price-aggressive")
        if dump:
            self.tree_.dump_tree("test-sybase.out",ignore_tags=ignore_tags)
            self.tree_.dump_tree("test-sybase-data.out",with_data=with_data,ignore_tags=ignore_tags)

        ## load sizeLimit
        self.sizeLimits_ = get_db_sizeLimits_item()

        if return_data:
            return tree

    def get_sizeLimit(self,symbol,**kw):
        """ version b. API """
        return self._get_sizeLimit_b(symbol,**kw)

    def _get_sizeLimit_a(self,symbol,**kw):
        """ without size limit on exchange. only got business unit."""

        if not symbol.endswith("AX") and not symbol.endswith("CHA"):
            raise ValueError("not valid symbol: %s. should end with .AX or .CHA" % symbol)

        if self.sizeLimits_ == None:
            raise ValueError("dataset hasn't been loaded. call load_sybase or load_snapshot first.")

        businessUnit = kw.get("businessUnit")

        if businessUnit:

            key = ".".join([businessUnit,symbol])
            if key in self.sizeLimits_:
                return {'sizeLimit': self.sizeLimits_[key], 'trace_size': key}

            log.warn("key: %s not found" % key)
            key = ".".join(["DEFAULT",symbol])

            if key in self.sizeLimits_:
                return {'sizeLimit': self.sizeLimits_[key], 'trace_size': key}
            log.warn("Key: %s not found" % key)

        if businessUnit in self.sizeLimits_:
            return {'sizeLimit': self.sizeLimits_[businessUnit], 'trace_size': businessUnit}

        raise ValueError("unable to find sizeLimit for : %s" % symbol)

    def _get_sizeLimit_b(self,symbol,**kw):
        """ with sizeLimit on both business unit and venue for sor child."""

        log.info("symbol: [%s], args: [%s]" %(symbol,kw))
        if not symbol.endswith("AX") and not symbol.endswith("CHA"):
            raise ValueError("not valid symbol: %s. should end with .AX or .CHA" % symbol)

        if self.sizeLimits_ == None:
            raise ValueError("dataset hasn't been loaded. call load_sybase or load_snapshot first.")

        businessUnit = kw.get("businessUnit","DEFAULT")
        ## sor child order will subject further size/rule check.
        exch = kw.get("exchange","SYDE")
        ##  valid exchange
        assert exch in ("SYDE","CHIA","ASXC","CXAD","SIGA")

        if businessUnit:

            key = ".".join([businessUnit,exch,symbol])
            if key in self.sizeLimits_:
                return {'sizeLimit': self.sizeLimits_[key], 'trace_size': key}

            log.warn("key: %s not found" % key)
            key = ".".join(["DEFAULT",exch,symbol])

            if key in self.sizeLimits_:
                return {'sizeLimit': self.sizeLimits_[key], 'trace_size': key}
            log.warn("Key: %s not found" % key)

        if businessUnit in self.sizeLimits_:
            return {'sizeLimit': self.sizeLimits_[".".join([businessUnit,exch])], 'trace_size': businessUnit}

        raise ValueError("unable to find sizeLimit for : %s, businessUnit: %s" % (symbol,businessUnit))

    def list_sizectrl_symbols(self,**kw):
        """ not a reliable source of instrument list."""
        market = kw.get("market","AX")
        if market not in ("AX","CHA"):
            raise ValueError("market must in AX or CHA: %s" % market)

        if self.sizeLimits_ == None:
            raise ValueError("dataset hasn't been loaded. call load_sybase or load_snapshot first.")

        symbols = set([".".join(s.split(".")[-2:]) for s in self.sizeLimits_.keys() if s.endswith(market)])

        return list(symbols)

    ## helper to return om2 binary version
    def get_om2_version(self):
        """ """
        ret = {}
        for k,v in settings.OM2_PATHS.iteritems():
            try:
                if not k.endswith("RDS"):
                    ret[k] = os.readlink(os.path.join(v,"bin/omengine"))
                else:
                    ret[k] = os.readlink(os.path.join(v,"bin/rdeshmfeeder"))
            except OSError,e:
                ret[k] = str(e)
        return ret


def run_as_service():
    """ """
    try:
        import traceback
        import signal
        from singleton import SingleInstance
        me = SingleInstance("ruleService")
        server = RDSRuleServer()
        ## default load sybase
        log.info("loading rule from sybase by default")
        server.load_sybase()
        #server.load_snapshot()
        ## load rds account for PME
        #server.load_snapshot_account()

        log.info("server binding: %s" % settings.RULE_ENDPOINT)
        server.bind(settings.RULE_ENDPOINT)

        def trigger_shutdown():
            """ shutdown event loop."""
            log.info("signal INT received, stop event loop.")
            server.stop()
            log.info("RPC server stopped")

        log.info("setup signal for INT/QUIT")
        ## register signal INT/QUIT for proper shutdown
        gevent.signal(signal.SIGINT,trigger_shutdown)
        print "running"
        log.info("running")
        server.run()
        log.info("finished cleanly.")
    except Exception,e:
        error = "run failed on exception: %s" % e
        print error
        log.exception(e)

if __name__ == "__main__":
    """ """
    run_as_service()

