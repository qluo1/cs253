""" rework on fetch marekt data from excel file.

turn it into function.

"""
import logging
log = logging.getLogger(__name__)

import os,sys
try:
    import xlrd
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/xlrd-0.9.0/lib/python2.7/site-packages")
    import xlrd

import subprocess
try:
    import Sybase
except ImportError:
    sys.path.append("/gns/mw/lang/python/modules/2.7.2/sybase-0.39/lib/python2.7/site-packages")
    import Sybase

symbolServiceMapping = {
    'JNX'   :   {
                    'server'    :'qa-p2ps.tk.mds.services.gs.com',
                    'user'      :'apqaautomation',
                    'service'   :'DF_JNO_QA',
                    'fields'    :['PROV_SYMB','HST_CLOSE2']
                },
    'CHJ'   :   {
                    'server'    :'qa-p2ps.tk.mds.services.gs.com',
                    'user'      :'apqaautomation',
                    'service'   :'DF_CXJ_QA',
                    'fields'    :['PROV_SYMB','HST_CLOSE ']
                },
    'T'     :   {
                    'server'    :'qa-p2ps.tk.mds.services.gs.com',
                    'user'      :'apqaautomation',
                    'service'   :'DF_TSE_QA',
                    'fields'    :['GEN_TEXT16','HST_CLOSE2']
                },
    'HK'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'user'      :'oma_gsetqa_hk_6744',
                    'service'   :'IDN_SELECT_PLUS',
                    'fields'    :['BCAST_REF','HST_CLOSE']
                },
    'KS'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'user'      :'oma_gsetqa_kr_7599',
                    'servive'   :'qa-p2ps.hk.mds.services.gs.com',
                    'fields'    :['BCAST_REF','HST_CLOSE2']
                },
    'TW'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'user'      :'oma_gsetqa_hk_6744',
                    'service'   :'qa-p2ps.hk.mds.services.gs.com',
                    'fields'    :['BCAST_REF','HST_CLOSE2']
                },
    'NS'    :   {
                    'server'    :'qa-p2ps.mu.mds.services.gs.com',
                    #'user'      :'cipherdev',
                    'user'      :'omaqa',
                    'service'   :'QA_NSE_CM',
                    'fields'    :['','']
                },
    'SI'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'user'      :'oma_gsetqa_hk_6744',
                    'service'   :'IDN_SELECT_PLUS',
                    'fields'    :['BCAST_REF','ADJUST_CLS']
                },
    'KL'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'user'      :'oma_gsetqa_hk_6744',
                    'service'   :'IDN_SELECT_PLUS',
                    'fields'    :['BCAST_REF','GEN_VAL2']
                },
    'AX'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'service'   :'IDN_SELECT_PLUS',
                    'user'      :'oma_gsetqa_hk_6744',
                    'fields'    :['BCAST_REF','HST_CLOSE2']
                    #################
                    #'server'    :'qa-p2ps.sy.mds.services.gs.com',
                    #'user'      :'aucel_qa_12414',
                    #'service'   :'DF_ASX_QA',
                    ## field not match??
                    #'fields'    :['OFFCL_CODE','HST_CLOSE'],

                },
    'CHA'    :   {
                    'server'    :'qa-p2ps.sy.mds.services.gs.com',
                    'user'      :'aucel_qa_12414',
                    #'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    #'user'      :'oma_gsetqa_hk_6744',
                    'service'   :'DF_CXA_QA',
                    'fields'    :['BCAST_REF','HST_CLOSE2']
                },


    'SH'    :   {
                    'server'    :'qa-p2ps.hk.mds.services.gs.com',
                    'user'      :'oma_gsetqa_hk_6744',
                    'service'   :'IDN_SELECT_PLUS',
                    'fields'    :['BCAST_REF','HST_CLOSE']
                },
}

CodeMap = {
    'SEDOL' : 'SED',
    'ISIN number' : 'ISN',
    'RIC code' : 'RIC',
    'A' : 'BID',
    'CUSIP' :'CUS'
}

QuikMap = {
    'TKYO' : 'T',
    'CHJ' : 'CHJ',
    'JPNX' : 'JNX',
    'BO' : 'BO',
    'INDE' : 'NS',
    'SINE' : 'SI',
    'TOTC' : 'TWO',
    'HK' : 'HK',
    'SYDE' : 'AX',
    'CHIA' : 'CHA'
}


def run_gen_price(excelFile, outdir):
    """

    input excel file

    output:

        priceControlFile,
        symbols file
    """
    log.info("run_gen_price: %s, %s" % (excelFile,outdir))
    symbolsfilepath = os.path.join(outdir,"symbols.")
    priceControlFile = os.path.join(outdir,"PriceControl.data")
    assert os.path.exists(excelFile)

    if os.path.exists(priceControlFile):
        os.remove(priceControlFile)

    book = xlrd.open_workbook(excelFile)
    first_sheet = book.sheet_by_index(0)
    rows = first_sheet.nrows
    cols = first_sheet.ncols
    symbols = dict()
    symByMkt = dict()
    symFiles = list()
    RicSymbolMap = list()

    """
    Get all the Symbols used in the excel file
    """
    for row in range(rows):
        for col in range(cols):
            field = first_sheet.cell(row,col).value
            if field == 'SecurityID':
                value = str(first_sheet.cell(row+1,col).value)
                if '.' in value:
                    value = value.split('.')[0] if value.split('.')[1] == '0' else value
                symbols[value]=dict()

    """
    Getting test case detail for each of the symbol.
    """
    for row in range(rows):
            value = ''
            for col in range(cols):
                    field = first_sheet.cell(row,col).value
                    if field == 'SecurityID':
                            value = str(first_sheet.cell(row+1,col).value)
                            if '.' in value:
                                value = value.split('.')[0] if value.split('.')[1] == '0' else value
                            break
            for col in range(cols):
                    field = first_sheet.cell(row,col).value
                    if field == 'ExDestination':
                        symbols[value][field] = str(first_sheet.cell(row+1,col).value)
                    if field == 'IDSource':
                        symbols[value][field] = str(first_sheet.cell(row+1,col).value)

    log.info("collected symbols: %s" %  symbols)

    """
    Fetching Ric Codes for all the symbols in the excel
    """
    con = Sybase.connect("APEQTSQ1","rds_ro","rds_ro",database="product")
    for key in symbols:
        log.info("%s, ExDestination: %s,-----" % (key,symbols[key]['ExDestination']))
        RicCode=key.strip()
        if '.' not in key and symbols[key]['IDSource']!= 'QUIK':
            sql="select synonym_c from synonym where product_id_i in (select product_id_i from synonym where synonym_c='{0}' and synonym_type_cd_c='{1}') \
                    and synonym_type_cd_c='RIC' and (syn_market_cd_c='{2}' or synonym_type_cd_c='{2}')"
            cur = con.cursor()
            sql_formatted =sql.format(key,CodeMap[symbols[key]['IDSource']],symbols[key]['ExDestination'])
            log.info("%s, %s" %(key,sql_formatted))
            cur.execute(sql_formatted)
            RicCode = cur.fetchone()
            log.info( "%s, %s" % (RicCode,key.strip()))
        if symbols[key]['IDSource'] == 'QUIK':
            RicCode=RicCode+"."+QuikMap[symbols[key]['ExDestination']]
        RicSymbolMap.append((RicCode[0].rstrip() if isinstance(RicCode,tuple) else RicCode,key.strip()))

    con.close()
    log.info("ric symbol map: %s" % RicSymbolMap)

    """
    Creating symbol files based on Market so that the prices for all symbols related to one market can be fetched at once.
    """
    for item in symbolServiceMapping:
        filteredSymbols = [ sym[0] for sym in RicSymbolMap if sym[0] != None and '.' in sym[0] and sym[0].split(".")[1] == item]
        symByMkt[item] = list(set(filteredSymbols))
        if symByMkt[item]:
            filename = symbolsfilepath+item
            symFiles.append(filename)
            with open(filename, "w+") as f:
                for field in symByMkt[item]:
                    f.write(field+"\n")

    log.info("symByMkt: %s" % symByMkt)
    log.info("symFiles: %s" % symFiles)

    """
    Fetching prices for symbols and writing them to PriceControl.Data file.
    """
    #import pdb;pdb.set_trace()
    for file in symFiles:
        rmds_command = """/sw/ficc/wraps/bin/sfc_listen -p """ + \
                symbolServiceMapping[file.split(".")[-1]]['server'] + """ -O -S """ + \
                symbolServiceMapping[file.split(".")[-1]]['service'] + """ -u """ + \
                symbolServiceMapping[file.split(".")[-1]]['user'] + """ -b """ + \
                file + """ | egrep \""""+ \
                symbolServiceMapping[file.split(".")[-1]]['fields'][0] +"""|""" + \
                symbolServiceMapping[file.split(".")[-1]]['fields'][1] +"""\" """
        log.info("Running : %s " %rmds_command)
        p = subprocess.Popen(rmds_command, stdout=subprocess.PIPE, shell=True)
        stdout, stderr  = p.communicate()
        symbolData = stdout.split("\n")
        symbolData.remove("")
        log.info(symbolData)
        it = iter(symbolData)
        with open(priceControlFile, "a") as f:
            for prices in it:
                sym = next(it)
                # This block added by Neelam to check which field is price and pick accordingly 
                tmp = sym.split(":")[0].strip()
                if tmp in ('HST_CLOSE','HST_CLOSE2'):
                    price = sym.split(":")[1]
                    sym = prices
                    sym = prices.split(":")[1]
                else :
                    sym = sym.split(":")[1]
                    print "sym :",sym
                    price  = prices.split(":")[1]
                log.info("sym: %s, price:%s " %( sym, price))
                for i,j in RicSymbolMap:
                    log.info("%s, %s, %s" %( i,j,price))
                    if i != None and i.split('.')[0] == sym.strip().split('.')[0] and file.split('.')[1] == i.split('.')[1]:
                        log.info("i %s,j %s price: %s " % (i,j,price))
                        f.write(j+":"+price+"\n")

    with open(priceControlFile, "a") as f:
        for i,j in RicSymbolMap:
            if i == None:
                log.info(j+":0")
                f.write(j+":"+"0\n")
    ## all ok
    return True


def query_symbol_quote(symbol,**kw):
    """ """

    debug = kw.get("debug",False)
    ticker,exch = symbol.split(".")

    if debug:
        print exch,ticker
    assert exch in symbolServiceMapping.keys()

    rmds_command = "/sw/ficc/wraps/bin/sfc_listen -p " + \
            symbolServiceMapping[exch]['server'] + " -O -S " + \
            symbolServiceMapping[exch]['service'] + " -u " + \
            symbolServiceMapping[exch]['user'] + " " + symbol
    if debug:
        print rmds_command
    p = subprocess.Popen(rmds_command, stdout=subprocess.PIPE, shell=True)
    stdout, stderr  = p.communicate()
    if debug:
        print stdout
    symbolData = [d for d in stdout.split("\n") if d !=""]

    data = {}
    for item in symbolData:
        ## stop on statistics line
        item = item.strip()
        if item.startswith("+") or item.startswith("["):continue
        if item.startswith("Statistics"): break
        if ":" in item:
            try:
                k,v = item.split(":",1)
            except Exception,e:
                print item
                continue
            if v.strip() != "":
                data[k.strip()] = v.strip()
    return data


if __name__ == "__main__":
    """ """
    import argparse
    import pprint

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--symbol",help="symbol name")
    parser.add_argument("-d", "--debug",help="debug flag",action="store_true",default=False)

    args = parser.parse_args()
    #print args

    debug = args.debug
    if args.symbol:
        data = query_symbol_quote(args.symbol,debug=debug)
        pprint.pprint(data)
    else:
        parser.print_help()



