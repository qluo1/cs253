""" test case configuraiton.

- test side
- order type

"""
## SSE not supported by viking
TEST_SIDES = ['Buy','Sell','Short']
# VIKING doesn't support SSE
#sides = ['Buy','Sell','Short','SSE']

HOUSE_XREFS         = ('FC1','FC2','FA8','FC8','OP6')

CLIENT_XREFS        = ('A28','A29','A2L','PA4','PA5','PA6')
## client Nomura asset mgmt , ASXOnly SI
CLIENT_SI_XREFS  = ('JF35','JF37','JF36','JF38','JF39','JF4','JF5','JF6','JF25','DY6','DY7','DY8')
## still need by order basic
TEST_XREF           = 'FA8'

ORDER_TYPES = {
    ## direct order types
    'asx':  {'exch': 'SYDE', 'sor': None},
    ## asx peg order 
    'asx_mid':{'exch': 'SYDE', 'sor': None,'orderType':'Pegged','pegType':'Mid'},
    'asx_ask':{'exch': 'SYDE', 'sor': None,'orderType':'Pegged','pegType':'Ask'},
    'asx_bid':{'exch': 'SYDE', 'sor': None,'orderType':'Pegged','pegType':'Bid'},

    ## chia direct
    'chia': {'exch': 'CHIA', 'sor': None},
    ## chia peg order 
    'chia_mid':{'exch': 'CHIA', 'sor': None,'orderType':'Pegged','pegType':'Mid'},
    'chia_ask':{'exch': 'CHIA', 'sor': None,'orderType':'Pegged','pegType':'Ask'},
    'chia_bid':{'exch': 'CHIA', 'sor': None,'orderType':'Pegged','pegType':'Bid'},
    ## asxcp
    'asxc': {'exch': 'ASXC', 'sor': None},
    ## asxsweep
    'asxs': {'exch': 'ASXS', 'sor': None},
    ## cp block, sweep block
    'asxcb': {'exch': 'ASXC', 'sor': None, 'maq': 50},
    'asxsb': {'exch': 'ASXS', 'sor': None, 'maq': 50},

    ## sor order types, maq default
    'xasx': {'exch': 'SYDE', 'sor': 'ASXDirect'},
    'asxsweep': {'exch': 'SYDE', 'sor': 'ASXSWEEP'},
    'sor1': {'exch': 'SYDE', 'sor': 'ASXOnly'},
    'sor2': {'exch': 'SYDE', 'sor': 'BestPrice'},
    'sor3': {'exch': 'SYDE', 'sor': 'BestPriceUni'},

    ## default maq, future will move maq by default without specify maq = -1
    'sor4': {'exch': 'SYDE', 'sor': 'BestPriceMinQty', 'maq': -1},
    'sor5': {'exch': 'SYDE', 'sor': 'BestPriceMinQtyUni', 'maq': -1},
    'sor6': {'exch': 'SYDE', 'sor': 'BestPriceMinQtyNoLit', 'maq': -1},
    'sor7': {'exch': 'SYDE', 'sor': 'BestPriceMinQtyNoLitUni', 'maq': -1},

    ## maq specified
    'sor4_maq': {'exch': 'SYDE', 'sor': 'BestPriceMinQty', 'maq': 50},
    'sor5_maq': {'exch': 'SYDE', 'sor': 'BestPriceMinQtyUni', 'maq': 50},
    'sor6_maq': {'exch': 'SYDE', 'sor': 'BestPriceMinQtyNoLit', 'maq': 50},
    'sor7_maq': {'exch': 'SYDE', 'sor': 'BestPriceMinQtyNoLitUni', 'maq': 50},

    ## MinVlaue $120
    'sor_jcp':  {'exch': 'SYDE', 'sor': 'BestPriceMinValue'},

}

DARK_ORDER_TYPES = {
    ## dark pool
    'sigmax'        :   {'exch': 'SYDE', 'sor': 'SOR_AUSigmaX'},
    'audark'        :   {'exch': 'SYDE', 'sor': 'SOR_AUDark'},
    'audarkMxq'     :   {'exch': 'SYDE', 'sor': 'SOR_AUDarkMinQty'},
    'audupost'      :   {'exch': 'SYDE', 'sor': 'SOR_AULitPostIS'},
    'audupostMxq'   :   {'exch': 'SYDE', 'sor': 'SOR_AULitPostISMinQty'},
    'audarkcp'      :   {'exch': 'SYDE', 'sor': 'SOR_AUCentrePoint'},
    'audarkExchix'  :   {'exch': 'SYDE', 'sor': 'SOR_AUDarkExChix'},
    'audarkExchixMxq':  {'exch': 'SYDE', 'sor': 'SOR_AUDarkExChixMinQty'},
}

## single leg SIGMA
TRADE_REPORTS = {
    'asx':  {'exch': 'SYDE','sor': None, 'crossMatchId': None, },
    #'siga': {'exch': 'SIGA','sor': None, 'crossMatchId': None, },
    #'cxa':  {'exch': 'CHIA','sor': None, 'crossMatchId': None, },

}

## not fully supported
MKT_ORDERS = {
    ## asx market to limit
    'asxmklt':{'exch': 'SYDE', 'sor': None,'orderType':'MarketToLimit'},
    ## not supported
    'asxmkt': {'exch': 'SYDE', 'sor': None,'orderType':'Market'},

    ## not supported
    'cxamkt': {'exch': 'CHIA', 'sor': None,'orderType':'Market'},
    ## chia market on close, not supported yet JIRA 488
    'cxamoc': {'exch': 'CHIA', 'sor': None, 'orderType':'Market', 'tif': 'Close'},
    ## should be rejected
    'asxonly':{'exch': 'SYDE', 'sor': "ASXOnly",'orderType':'Market'},
    ## should be rejected
    'bestprice':{'exch': 'SYDE', 'sor': "BestPrice",'orderType':'Market'},
}

import itertools

##########################################
## all order type with sor specified
SOR = [k for k,v in itertools.chain(ORDER_TYPES.iteritems(),DARK_ORDER_TYPES.iteritems()) if v['sor']]

## sor unidirect
SOR_UNI = [k for k,v in ORDER_TYPES.iteritems() if v['sor'] and v['sor'].endswith("Uni")]

## direct order type
DIRECT = [k for k,v in ORDER_TYPES.iteritems() if v['sor'] is None]

SOR_DARK = [k for k,v in DARK_ORDER_TYPES.iteritems()]

##############################################
## exclude sor behave like direct
SOR_NODIRECT = [k for k in SOR if k not in ('xasx','sor_jcp','asxsweep') ]

##############################################
## SOR exclude direct/dark
SOR_NODIRECT_DARK = [k for k in SOR_NODIRECT if k not in SOR_DARK]

## order hit ASXC
ASXCP = ['asxc','asxcb','asx_mid','asx_bid','asx_ask','asxsweep','audarkcp']

#min asxc block size in value
ASXCB_ORDER_MINIMUM_SIZE = 200000

## client side blacklist
BLACKLIST_SYMBOLS = (
    'AAC.AX',  ## size limit
    'CIA.AX',
    'NAB.AX', ## go X3
    'ANZ.AX', ## go X3
    'UBJ.AX'  ## bad on CHIA
    'IEU.AX'  ## not working with Plutus

    )
