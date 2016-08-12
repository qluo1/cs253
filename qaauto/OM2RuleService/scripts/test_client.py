import zerorpc
import gevent
import localconf
from settings import RULE_ENDPOINT
from pprint import pprint

client = zerorpc.Client()
client.connect(RULE_ENDPOINT)


class Test_Client(object):

    def test_api_call(self):
        """ """
        print client.find_price_step(1.23,"exchange-continuous-limit")
        for price in (0.0001, 0.05, 0.14,0.20,0.25,0.36,0.55,1.05,2.05, 4.30, 5.00, 7.0, 8.9,10.8,15.6, 21.03,34,55.09,101.02,167.09):

            for businessUnit in (None, "PT","SS","DEFAULT","ALGO_DEFAULT","OPERATOR"):
                for exch in ("SYDE","CHIA","SIGA","ASXC"):
                    for tag in ("exchange-continuous-limit","exchange-continuous-pegged",
                                "exchange-open-auction-limit","exchange-open-auction-pegged",
                                "exchange-close-auction-limit","exchange-close-auction-pegged",
                                ):
                        print price, client.find_price_step(price,tag,exchange=exch,businessUnit=businessUnit)

    def test_load_from_folder(self):
        """ """
        folders = ["Snapshot_151012_06_45_23","Snapshot_160218_06_45_20"]
        for folder in folders:
            print folder, client.find_price_step(1.23,"exchange-continuous-limit",folder=folder)

    def test_load_snapshot(self):
        """ load PME snapshot"""
        snapshot = "Snapshot_160308_06_45_49"
        data = client.load_snapshot(folder=snapshot,with_data=True,return_data=True,dump=True)
        pprint(data)

    def test_load_sybase(self):
        """ """
        ret = client.load_sybase(with_data=True,dump=True)
        assert ret == None


    def test_load_sizeLimit(self):
        """ """
        #client.load_snapshot(folder="Snapshot_160222_06_45_22")

        print client.get_sizeLimit("CSL.AX")
        print client.get_sizeLimit("CSL.AX",businessUnit="DMA",exchange="CXAD")
        print client.get_sizeLimit("CSL.AX",businessUnit="DMA",exchange="SIGA")
        print client.get_sizeLimit("CSL.AX",businessUnit="DEFAULT")
        print client.get_sizeLimit("CSL.AX",businessUnit="SS")
        print client.get_sizeLimit("CSL.AX",businessUnit="PT")
        print client.get_sizeLimit("CSL.AX",businessUnit="PT",exchange="ASXC")

    def test_list_symbols(self):
        """ """
        client.load_sybase()
        client.load_snapshot(folder="Snapshot_160222_06_45_22")

        symbols = client.list_symbols(market="AX")
        print symbols
        cha_symbols = client.list_symbols(market="AX")
        print symbols
        print len(symbols)
        print len(cha_symbols)

    def test_query_priceStep(self):
        """ """
        from pprint import pprint
        #client.load_snapshot(folder="Snapshot_160229_06_45_45")
        #client.load_sybase()
        pprint(client.find_price_step(52.0,"exchange-open-auction-limit",symobl="TGR.AX"))
        pprint(client.find_price_step(52.0,"exchange-open-auction-limit",symobl="TGR.AX",businessUnit="OPERATOR"))
        #pprint(client.find_price_step(4.0,"exchange-close-auction-limit",symbol="TGR.AX"))
        #pprint(client.find_price_step(52.0,"exchange-continuous-limit"))
        #pprint(client.find_price_step(52.0,"exchange-open-auction-pegged",symbol="WOW.AX"))

