# Sample command $ python DSAMigration.py path_to_algo_params_csv path_to_migration_status_csv
import sybpydb
import getpass
import logging
import os.path
import os
import sys, traceback
import csv
import datetime

logging.basicConfig(filename=os.path.basename(__file__) + ".log", level=logging.DEBUG)
logger = logging.getLogger(os.path.basename(__file__))

PREFERENCE_DB_SERVERS = { 'prod' : 'APEQTSP1',       'qa' : 'APEQTSQ1' }
USERS =                 { 'prod' : 'lushiy',     'qa' : 'qa_client_db' }
FARM_DBS =        { 'prod' : 'farm_client_db', 'qa' : 'qa_client_db' }
BETA_DBS =        { 'prod' : 'beta_client_db', 'qa' : 'qa_client_db' }

DB_ENVIRONMENT = os.getenv('DB_ENVIRONMENT', 'qa')
DB_USER = os.getenv('DB_USER', USERS[DB_ENVIRONMENT])
DB_SERVER = os.getenv('DB_SERVER', PREFERENCE_DB_SERVERS[DB_ENVIRONMENT])
DB_FARM = os.getenv('DB_FARM', FARM_DBS[DB_ENVIRONMENT])
DB_BETA = os.getenv('DB_BETA', BETA_DBS[DB_ENVIRONMENT])

class QueryResults(object):
    def __init__(self, header, rows):
        self.header = header
        self.rows = rows

def get_connection(server, password):
    return sybpydb.connect(servername=server, user=DB_USER, password=password)

def run_query(server, sql, password):

    conn = get_connection(server, password)
    cur = conn.cursor()
    logger.debug("Execute SQL query: [" + sql + "]")
    cur.execute(sql)

    try:
        rows = cur.fetchall()
        logger.debug(str(len(rows)) + " returned")
        description = cur.description
    except sybpydb.DatabaseError, e:
        logger.debug("Error: [" + str(e) + "]")
        print "run_query-Error: " + str(e)
        return False

    cur.close()
    conn.close()
    results = QueryResults(description, rows)
    return results

def execute_sql(server, sql, password, sqlParam=None):

    try:
        conn = get_connection(server, password)
        cur = conn.cursor()
        logger.debug("Received SQL query: [" + sql + "], " + str(sqlParam))
        if sqlParam:
            cur.execute(sql, sqlParam)
        else:
            cur.execute(sql)
        conn.commit()
    except StandardError, e:
        logger.debug("Error: [" + str(e) + "]")
        print "   execute_sql Error: " + str(e)
        return False

    cur.close()
    conn.close()
    return True


def getColumnDict(cursorDescription):
    columnDictionary = {}
    for i in range(len(cursorDescription)):
        columnDictionary[cursorDescription[i][0]] = i
    return columnDictionary

def loadMigrationStatusFromDB(srv, pwd):
    sql = "select client_id, service_offering, booking_style, property_value from " + DB_FARM + ".dbo.client_property where property_name='ANZMIGRATED'"
    result = run_query(server = srv, sql=sql, password=pwd)
    if not result:
        return False

    columnDict = getColumnDict(result.header)
    serviceOfferingMap = {3 : 'GSAT', 4 : 'DMA'}
    bookingStyleMap = {0 : 'Cash', 1 : 'CFD'}
    clientMigrationStatusMap = {}

    num_GSAT_Cash = 0
    num_GSAT_CFD = 0
    num_DMA_Cash = 0
    num_DMA_CFD = 0
    num_DMA_Migrated = 0
    for row in result.rows:
        bookingStyle = bookingStyleMap[row[columnDict['booking_style']]]
        serviceOffering = serviceOfferingMap[row[columnDict['service_offering']]]
        starId = row[columnDict['client_id']]
        if not clientMigrationStatusMap.get((starId, bookingStyle, serviceOffering)):
            clientMigrationStatusMap[(starId, bookingStyle, serviceOffering)] = 0

        val = row[columnDict['property_value']]
        clientMigrationStatusMap[(starId, bookingStyle, serviceOffering)] += 1 if val == 'A' else 0

    duplicationMap = {}
    listOfMigratedGSATClients = []
    for key in clientMigrationStatusMap:
        serviceOffering = key[2]
        bookingStyle = key[1]
        num_GSAT_Cash += 1 if bookingStyle == 'Cash' and serviceOffering == 'GSAT' and clientMigrationStatusMap[key] >= 8 else 0
        num_GSAT_CFD += 1 if bookingStyle == 'CFD' and serviceOffering == 'GSAT' and clientMigrationStatusMap[key] >= 8 else 0
        if serviceOffering == 'GSAT' and clientMigrationStatusMap[key] >= 1:
            listOfMigratedGSATClients.append(key[0] + ':' + bookingStyle)
        num_DMA_Cash += 1 if bookingStyle == 'Cash' and serviceOffering == 'DMA' and clientMigrationStatusMap[key] >= 8 else 0
        num_DMA_CFD += 1 if bookingStyle == 'CFD' and serviceOffering == 'DMA' and clientMigrationStatusMap[key] >= 8 else 0
        if not duplicationMap.get(key[0]):
            duplicationMap[key[0]] = True
            num_DMA_Migrated += 1
    print '   migrated client:' + str(listOfMigratedGSATClients)

    return clientMigrationStatusMap

def isClientCashGSATMigrated(starId, clientMigrationStatusMap):
    return clientMigrationStatusMap.get((starId, 'Cash', 'GSAT'), 0) >= 8

def isClientCFDGSATMigrated(starId, clientMigrationStatusMap):
    return clientMigrationStatusMap.get((starId, 'CFD', 'GSAT'), 0) >= 8

def loadAlgoMappingMapFromDB(password):
    sql = ("SELECT * FROM " + DB_FARM + ".dbo.client_algorithm WHERE market = 'SYDE' OR market = 'CHIA'")
    result = run_query(server = DB_SERVER, sql=sql, password=password)
    if not result:
        return False

    columnDict = getColumnDict(result.header)
    algoMappingMap = {}
    for row in result.rows:
        algoMapping = {}
        algoMapping['client_id'] = row[columnDict['client_id']]
        algoMapping['market'] = row[columnDict['market']]
        algoMapping['algorithm_in'] = row[columnDict['algorithm_in']]
        algoMapping['sub_market'] = row[columnDict['sub_market']]
        algoMapping['product_group'] = row[columnDict['product_group']]
        algoMapping['algorithm_out'] = row[columnDict['algorithm_out']]
        algoMapping['algorithm_parameters'] = row[columnDict['algorithm_parameters']]
        algoMapping['custom_param'] = row[columnDict['custom_param']]
        if not algoMappingMap.get(algoMapping['client_id']):
            algoMappingMap[algoMapping['client_id']] = []
        algoMappingMap[algoMapping['client_id']].append(algoMapping)

    countHasAlgoParam = 0
    countHasCustomParam = 0
    for key in algoMappingMap:
        for algoMapping in algoMappingMap[key]:
            if algoMapping['algorithm_parameters'] != " ":
                countHasAlgoParam += 1
    print "   num of distinct star id = " + str(len(algoMappingMap))
    return algoMappingMap

def loadAlgoMappingMapFromCSV(filename):
    csvFile = open(filename, 'rb')

    algoMappingMap = {}
    try:

        for row in csv.DictReader(csvFile):
            algoMapping = {}
            algoMapping['client_id'] = row['client_id']
            algoMapping['market'] = row['market']
            algoMapping['sub_market'] = row['sub_market']
            algoMapping['product_group'] = row['product_group']
            algoMapping['custom_param'] = row['custom_param']
            algoMapping['algorithm_in'] = row['algorithm_in']
            algoMapping['algorithm_out'] = row['algorithm_out']
            algoMapping['algorithm_parameters'] = row['algorithm_parameters']
            algoMapping['n_algorithm_out'] = row['n_algorithm_out']
            algoMapping['n_algorithm_parameters'] = row['n_algorithm_parameters']
            if not algoMappingMap.get(algoMapping['client_id']):
                algoMappingMap[algoMapping['client_id']] = []
            algoMappingMap[algoMapping['client_id']].append(algoMapping)
    finally:
        csvFile.close()

    countHasAlgoParam = 0
    countHasCustomParam = 0
    for key in algoMappingMap:
        for algoMapping in algoMappingMap[key]:
            if algoMapping['algorithm_parameters'] != " ":
                countHasAlgoParam += 1
    print "   csv:num of distinct star id = " + str(len(algoMappingMap))
    return algoMappingMap


def validateMigrationStatusMapBetweenCSVandDB(dbMigrationStatusMap, csvMigrationStatusMap):
    hasFoundMismatchedMigrationStatus = False
    for key in csvMigrationStatusMap:
        if key[3] == 'PRESENT':
            starId = key[0]
            if key[1] == 'Cash' and (csvMigrationStatusMap[key] != isClientCashGSATMigrated(starId, dbMigrationStatusMap)):
                print '   GSAT Cash Migration status mismatch for starid ' + starId
                hasFoundMismatchedMigrationStatus = True
            if key[1] == 'CFD' and (csvMigrationStatusMap[key] != isClientCFDGSATMigrated(starId, dbMigrationStatusMap)):
                print '   GSAT CFD Migration status mismatch for starid ' + starId
                hasFoundMismatchedMigrationStatus = True

    return False if hasFoundMismatchedMigrationStatus else True

def loadMigrationStatusMapFromCSV(filename):
    csvFile = open(filename, 'rb')
    csvMigrationStatusMap = {}
    try:
        for row in csv.DictReader(csvFile):
            if csvMigrationStatusMap.get(row['client_id']):
                print '   duplication found in the migration csv for starid:' + row['client_id']
            starId = row['client_id']
            csvMigrationStatusMap[(starId, 'Cash', 'GSAT', 'PRESENT')] = row['IS_GSAT_CASH_MIGRATED'] == 'Y'
            csvMigrationStatusMap[(starId, 'Cash', 'GSAT', 'TARGET')] = row['SHOULD_GSAT_CASH_MIGRATED'] == 'Y'
            csvMigrationStatusMap[(starId, 'CFD', 'GSAT', 'PRESENT')] = row['IS_GSAT_CFD_MIGRATED'] == 'Y'
            csvMigrationStatusMap[(starId, 'CFD', 'GSAT', 'TARGET')] = row['SHOULD_GSAT_CFD_MIGRATED'] == 'Y'
    finally:
        csvFile.close()
    return csvMigrationStatusMap

def loadActionItemsFromMigrationStatusMap(csvMigrationStatusMap):
    actionItemsMap = {}
    for key in csvMigrationStatusMap:
        if key[3] == 'PRESENT':
            presentStatus = csvMigrationStatusMap[key]
            targetStatus = csvMigrationStatusMap[(key[0], key[1], key[2], 'TARGET')]
            if presentStatus != targetStatus:
                # client needs to migrate/unmigrate
                actionItemsMap[(key[0], key[1], key[2])] = targetStatus
    return actionItemsMap

def writeCSVMigrationStatusMapToFile(filename, csvMigrationStatusMap):
    csvOut = open(filename, 'wb')
    try:
        fieldname = ['client_id', 'IS_GSAT_CASH_MIGRATED', 'SHOULD_GSAT_CASH_MIGRATED', 'IS_GSAT_CFD_MIGRATED', 'SHOULD_GSAT_CFD_MIGRATED']

        writer = csv.DictWriter(csvOut, fieldnames=fieldname, extrasaction='ignore')

        headers = {}
        for n in fieldname:
            headers[n] = n
        writer.writerow(headers)

        for key in csvMigrationStatusMap:
            rowToWrite = {}
            starId = key[0]
            cashCFD = key[1]
            dmaAlgo = key[2]
            if key[3] == 'PRESENT':
                if dmaAlgo == 'GSAT' and cashCFD == 'Cash':
                    cashGSATmigrateStatus = 'Y' if csvMigrationStatusMap[key] else 'N'
                    cfdKey = (starId, 'CFD', dmaAlgo, 'PRESENT')
                    cfdGSATmigrationStatus = 'Y' if csvMigrationStatusMap[cfdKey] else 'N'
                    rowToWrite['IS_GSAT_CASH_MIGRATED'] = cashGSATmigrateStatus
                    rowToWrite['SHOULD_GSAT_CASH_MIGRATED'] = cashGSATmigrateStatus
                    rowToWrite['IS_GSAT_CFD_MIGRATED'] = cfdGSATmigrationStatus
                    rowToWrite['SHOULD_GSAT_CFD_MIGRATED'] = cfdGSATmigrationStatus
                    rowToWrite['client_id'] = starId
                    writer.writerow(rowToWrite)

    finally:
        csvOut.close()

def writeCSVAlgoMappingMapToFile(filename, csvAlgoMappingMap):
    csvOut = open(filename, 'wb')
    try:
        fieldname = ['client_id', 'market', 'sub_market', 'product_group', 'algorithm_in',
            'custom_param', 'algorithm_out', 'algorithm_parameters',
            'n_algorithm_out', 'n_algorithm_parameters']

        writer = csv.DictWriter(csvOut, fieldnames=fieldname, extrasaction='ignore')
        headers = {}
        for n in fieldname:
            headers[n] = n
        writer.writerow(headers)

        for key in csvAlgoMappingMap:
            for algoMapping in csvAlgoMappingMap[key]:
                writer.writerow(algoMapping)

    finally:
        csvOut.close()

def isPrimaryKeyMatched(left, right):
    return left['market'] == right['market'] and \
            left['sub_market'] == right['sub_market'] and \
            left['client_id'] == right['client_id'] and \
            left['product_group'] == right['product_group'] and \
            left['custom_param'] == right['custom_param'] and \
            left['algorithm_in'] == right['algorithm_in']


def updateCSVAlgoMappingMap(dbAlgoMapping, targetMigrationStatus, csvAlgoMappingMap):
    for row in csvAlgoMappingMap[dbAlgoMapping['client_id']]:
        if isPrimaryKeyMatched(row, dbAlgoMapping):
        # found the record in csv map, update it with the value in db
            if targetMigrationStatus:
                # move from unmigrated -> migrated, current db reflects params for unmigrated status
                row['algorithm_out'] = dbAlgoMapping['algorithm_out']
                row['algorithm_parameters'] = dbAlgoMapping['algorithm_parameters']
            else:
                # move from migrated -> unmigrated, current db reflects params for migrated status
                row['n_algorithm_out'] = dbAlgoMapping['algorithm_out']
                row['n_algorithm_parameters'] = dbAlgoMapping['algorithm_parameters']

def updateClientDb(key, targetStatus, dbAlgoMappingMap, csvAlgoMappingMap, password):

    print "      start " + ('migrate' if targetStatus else 'unmigrate') + ' for ' + str(key)
    starId = key[0]
    cashCFD = key[1]
    dmaAlgo = key[2]
    product_group_key = ''

    if dmaAlgo == 'GSAT' and cashCFD == 'Cash':
        product_group_key = 'AUSHARESCASH'
    if dmaAlgo == 'GSAT' and cashCFD == 'CFD':
        product_group_key = 'AUSHARESCFD'

    # we've previously chekced the number of algo params between db and csv, they matched

    countAlgoParams = 0
    print "      update algo params in csv from db for " + str(key)
    for dbAlgoMapping in dbAlgoMappingMap[starId]:
        if dbAlgoMapping['product_group'] == product_group_key:
            # update csv algo params from DB, always assume what's in the db now is correct
            updateCSVAlgoMappingMap(dbAlgoMapping, targetStatus, csvAlgoMappingMap)
            countAlgoParams += 1

    if countAlgoParams == 0:
        print '      [Error]no algo prams found in both db and csv for ' + str(key) + ', The client might not even trade this flow at all. Please report back to business'
        print '      [Error]the above error should never appear since it should be in the pre-check'
        return

    print "      update new algo params to db for " + str(key)

    algorithm_out_key = 'algorithm_out'
    algorithm_parameters_key = 'algorithm_parameters'

    if targetStatus:
        algorithm_out_key = 'n_algorithm_out'
        algorithm_parameters_key = 'n_algorithm_parameters'

    exeResult = False
    for csvAlgoMapping in csvAlgoMappingMap[starId]:
        if csvAlgoMapping['product_group'] == product_group_key:
            sql = "UPDATE " + DB_FARM + ".dbo.client_algorithm SET algorithm_out=?, algorithm_parameters=?, version_user=? where client_id=? and market=? and sub_market=? and product_group=? and algorithm_in=? and custom_param=?"
            exeResult = execute_sql(server = DB_SERVER, sql=sql, password=password, sqlParam=(csvAlgoMapping[algorithm_out_key], csvAlgoMapping[algorithm_parameters_key], DB_USER, starId, csvAlgoMapping['market'], csvAlgoMapping['sub_market'], csvAlgoMapping['product_group'], csvAlgoMapping['algorithm_in'], csvAlgoMapping['custom_param']))
            sql = "UPDATE " + DB_BETA + ".dbo.client_algorithm SET algorithm_out=?, algorithm_parameters=?, version_user=? where client_id=? and market=? and sub_market=? and product_group=? and algorithm_in=? and custom_param=?"
            exeResult = execute_sql(server = DB_SERVER, sql=sql, password=password, sqlParam=(csvAlgoMapping[algorithm_out_key], csvAlgoMapping[algorithm_parameters_key], DB_USER, starId, csvAlgoMapping['market'], csvAlgoMapping['sub_market'], csvAlgoMapping['product_group'], csvAlgoMapping['algorithm_in'], csvAlgoMapping['custom_param']))
            if not exeResult:
                print '   [Error] failed to update algo params, skip further sqls'
                return False


    exeResult = False
    print "      update ANZMIGRATED for " + str(key)
    sql = "DELETE FROM " + DB_FARM + ".dbo.client_property WHERE client_id='" + starId +"' AND property_name='ANZMIGRATED' " + "AND service_offering=3 AND booking_style=" + ("1" if cashCFD == 'CFD' else "0");
    exeResult = execute_sql(server = DB_SERVER, sql=sql, password=password)
    sql = "DELETE FROM " + DB_BETA + ".dbo.client_property WHERE client_id='" + starId +"' AND property_name='ANZMIGRATED' " + "AND service_offering=3 AND booking_style=" + ("1" if cashCFD == 'CFD' else "0");
    exeResult = execute_sql(server = DB_SERVER, sql=sql, password=password)
    if not exeResult:
        print '      failed to delete ANZMIGRATED for ' + str(key) + ', terminating the script'
        return False


    for market in ['SYDE', 'CHIA']:
        for product in ['0,7', '7,6', '6,6', '0,4']:
            exeResult = False
            #FARM
            sql = "INSERT INTO " + DB_FARM + ".dbo.client_property (client_id,book_id,market,sub_market,service_offering,product_type,product_sub_type,property_name,property_value,version_user,booking_style,schema_version,access_id,access_id_type) VALUES('" + starId + "',' ','" + market + "','N/A',3," + product + "," + "'ANZMIGRATED','" + ('A' if targetStatus else 'N') + "','lushiy'," + ("1" if cashCFD == 'CFD' else "0") + ",2,' ',8)"
            exeResult = execute_sql(server = DB_SERVER, sql=sql, password=password)
            #BETA
            sql = "INSERT INTO " + DB_BETA + ".dbo.client_property (client_id,book_id,market,sub_market,service_offering,product_type,product_sub_type,property_name,property_value,version_user,booking_style,schema_version,access_id,access_id_type) VALUES('" + starId + "',' ','" + market + "','N/A',3," + product + "," + "'ANZMIGRATED','" + ('A' if targetStatus else 'N') + "','lushiy'," + ("1" if cashCFD == 'CFD' else "0") + ",2,' ',8)"
            exeResult = execute_sql(server = DB_SERVER, sql=sql, password=password)

            if not exeResult:
                print '      failed to insert ANZMIGRATED for ' + str(key) + ', terminating the script'
                return False

    print "      completed for " + str(key)
    return True

def backupFile(filename):
    dir = './bak/'
    if not os.path.exists(dir):
        os.makedirs(dir)
    bakFilename = dir + 'bak_' + datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%dT%H%M%S") + '_' + filename
    print '===Backup the migration status csv to ' + bakFilename
    os.rename(filename, bakFilename)

def query_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def writeMigrationSummary(actionItemsMap, csvAlgoMappingMap):
    dir = './summary/'
    if not os.path.exists(dir):
        os.makedirs(dir)
    filename = dir + 'summary_' + datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%dT%H%M%S") + '.html'
    htmlfile = open(filename, 'w')

    htmlfile.write('<p> Migration Summary - ' + datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%dT%H%M%S") + '</p>')
    htmlfile.write('<p></p>')

    for key in actionItemsMap:
        product_group_key = 'AUSHARESCASH' if key[1] == 'Cash' else 'AUSHARESCFD'
        htmlfile.write('<p><b> client ' + str(key) + (' Migrated' if actionItemsMap[key] else ' Unmigrated') + '</b> </p>')
        htmlfile.write('<table>')
        htmlfile.write('<tr>')
        htmlfile.write('<th>' + 'client_id'  + '</th>')
        htmlfile.write('<th>' + 'market'  + '</th>')
        htmlfile.write('<th>' + 'product_group'  + '</th>')
        htmlfile.write('<th>' + 'algorithm_in'  + '</th>')
        htmlfile.write('<th>' + 'custom_param'  + '</th>')
        htmlfile.write('<th>' + 'algorithm_out'  + '</th>')
        htmlfile.write('<th>' + 'algorithm_parameters'  + '</th>')
        htmlfile.write('</tr>')
        for csvAlgoMapping in csvAlgoMappingMap[key[0]]:
            if csvAlgoMapping['product_group'] != product_group_key:
                continue
            htmlfile.write('<tr>')
            htmlfile.write('<td>' + csvAlgoMapping['client_id']  + '</td>')
            htmlfile.write('<td>' + csvAlgoMapping['market']  + '</td>')
            htmlfile.write('<td>' + csvAlgoMapping['product_group']  + '</td>')
            htmlfile.write('<td>' + csvAlgoMapping['algorithm_in']  + '</td>')
            htmlfile.write('<td>' + csvAlgoMapping['custom_param']  + '</td>')
            htmlfile.write('<td>' + (csvAlgoMapping['n_algorithm_out'] if actionItemsMap[key] else csvAlgoMapping['algorithm_out']) + '</td>')
            htmlfile.write('<td>' + (csvAlgoMapping['n_algorithm_parameters'] if actionItemsMap[key] else csvAlgoMapping['algorithm_parameters']) + '</td>')
            htmlfile.write('</tr>')
        htmlfile.write('</table>')
        htmlfile.write('<hr>')

def main(argv):
    print "GSET DSA Migration Script"
    print "========================="
    print "Environment: " + DB_ENVIRONMENT
    print "Dataserver(s): " + DB_SERVER
    print "Account: " + DB_USER

    print "===Attemp to connect to the database"
    password = getpass.getpass()
    try:
        conn = get_connection(server = DB_SERVER, password=password)
        conn.close()
    except:
        print "Unable to connect to the database. Check the password and try again."
        return

    inputMigrationStatusFilename = argv[2]
    inputAlgoParamsFilename = argv[1]
    print "===Successfully connected to the database"

    print "===Load Algo mapping map from DB"
    dbAlgoMappingMap = loadAlgoMappingMapFromDB(password)
    if not dbAlgoMappingMap:
        print '   [Error] sql error, terminating the script'
        return

    print '===Load Algo mapping map from CSV'
    csvAlgoMappingMap = loadAlgoMappingMapFromCSV(inputAlgoParamsFilename)

    print '===Load Migration Status from DB'
    dbMigrationStatusMap = loadMigrationStatusFromDB(DB_SERVER, password)
    if not dbMigrationStatusMap:
        print '   [Error] sql error, terminating the script'

    print '===Load migration status map from CSV'
    csvMigrationStatusMap = loadMigrationStatusMapFromCSV(inputMigrationStatusFilename)

    print '===Validate migration status between DB and CSV'
    if not validateMigrationStatusMapBetweenCSVandDB(dbMigrationStatusMap, csvMigrationStatusMap):
        print '   terminate the process due to mismatched migration status, please verify the contents in csv'
        return

    print '===Load action items'
    actionItemsMap = loadActionItemsFromMigrationStatusMap(csvMigrationStatusMap)
    if len(actionItemsMap) == 0:
        print '   No action items, terminating the script'
        return

    print '===Validate algo mapping between DB and CSV for action items only'
    isErrorOccured = False
    for key in actionItemsMap:
        starId = key[0]
        cashCFD = key[1]
        dmaAlgo = key[2]
        targetStatus = actionItemsMap[key]
        if not dbAlgoMappingMap.get(starId):
            # key doesn't exist in DB, the client might be deleted
            print '   [Error]client ' + starId + ' not exist in DB'
            isErrorOccured = True
        else:
            if len(csvAlgoMappingMap[starId]) != len(dbAlgoMappingMap[starId]):
                # num of aglo params don't match,algo param might be added or deleted
                print '   [Error]client ' + starId + ' has more/less algo params in db'
                isErrorOccured = True
            else:
                for csvAlgoMapping in csvAlgoMappingMap[starId]:
                    isMatchedRecordFound = False
                    for dbAlgoMapping in dbAlgoMappingMap[starId]:
                        if isPrimaryKeyMatched(csvAlgoMapping, dbAlgoMapping):
                            isMatchedRecordFound = True
                    if not isMatchedRecordFound:
                        print '   [Error]client ' + starId + ' has mismatched algo params primary key in db'
                        isErrorOccured = True

            product_group_key = ''
            if dmaAlgo == 'GSAT' and cashCFD == 'Cash':
                product_group_key = 'AUSHARESCASH'
            if dmaAlgo == 'GSAT' and cashCFD == 'CFD':
                product_group_key = 'AUSHARESCFD'

            countAlgoParams = 0
            for dbAlgoMapping in dbAlgoMappingMap[starId]:
                if dbAlgoMapping['product_group'] == product_group_key:
                    countAlgoParams += 1
            if countAlgoParams == 0:
                print '      [Error]no algo prams found in both db and csv for ' + str(key) + ', The client might not even trade this flow at all. Please report back to business'
                isErrorOccured = True

    if isErrorOccured:
        print '   [Error]errors occured when Validate algo mapping between DB and CSV, please double check, terminating the script'
        return

    print '===All validations completed, ready to start migrating/unmigrating GSAT clients'


    print ' Action items:' + str(actionItemsMap)
    if not query_yes_no("Please confirm if you want to start migrate/unmigrate the above clients", default="no"):
        print '   Exiting the script'
        return

    print '===Start to migrate/unmigrate the following clients:\n' + str(actionItemsMap)
    for key in actionItemsMap:
        targetStatus = actionItemsMap[key]

        print "===Processing " + str(key) + '  ->' + str(actionItemsMap[key])
        if not updateClientDb(key, targetStatus, dbAlgoMappingMap, csvAlgoMappingMap, password):
            print '   [Error] severe sql errors above for ' + str(key) + ', but continue the next one'

    print '===Reload migration status map from DB'
    dbMigrationStatusMap = loadMigrationStatusFromDB(DB_SERVER, password)

    print '===Start migration status post-actions validation process'
    errorMap = {}
    isErrorOccured = False
    for key in actionItemsMap:
        starId = key[0]
        cashCFD = key[1]
        dmaAlgo = key[2]
        expectedResult = actionItemsMap[key]
        if dmaAlgo == 'GSAT' and cashCFD == 'Cash':
            result = isClientCashGSATMigrated(starId, dbMigrationStatusMap)
            if expectedResult == result:
                print '   Client GSAT Cash ' + starId + ' migration status verified'
            else:
                print '   [Error]Client ' + starId + ' GSAT Cash migration status mismatched. Expected=' + str(expectedResult) + ' Present=' + str(result)
                errorMap[(starId, 'MigrationStatus')] = 'GSAT Cash ' + str(expectedResult) + ':' + str(result)

        if dmaAlgo == 'GSAT' and cashCFD == 'CFD':
            result = isClientCFDGSATMigrated(starId, dbMigrationStatusMap)
            if expectedResult == result:
                print '   Client GSAT CFD ' + starId + ' migration status verified'
            else:
                print '   [Error]Client ' + starId + ' GSAT CFD migration status mismatched. Expected=' + str(expectedResult) + ' Present=' + str(result)
                errorMap[(starId, 'MigrationStatus')] = 'GSAT CFD ' + str(expectedResult) + ':' + str(result)

        if not errorMap.get((starId, 'MigrationStatus'), None):
            # no error for this client
            print '   Update migration status in csv map for client ' + starId + ' ' + cashCFD
        else:
            print '   Client ' + starId + ' might be partially migrated due to SQL errors, please manually correct the DB and CSV'

        csvMigrationStatusMap[(starId, cashCFD, dmaAlgo, 'PRESENT')] = expectedResult
        csvMigrationStatusMap[(starId, cashCFD, dmaAlgo, 'TARGET')] = expectedResult

    backupFile(inputMigrationStatusFilename)

    print '===Export updated csvMigrationStatusMap to file ' + inputMigrationStatusFilename
    writeCSVMigrationStatusMapToFile(inputMigrationStatusFilename, csvMigrationStatusMap)

    print '===Reload algoMapping map from DB'
    dbAlgoMappingMap = loadAlgoMappingMapFromDB(password)

    print '===Reload migration status map from newly generated csv ' + inputMigrationStatusFilename
    csvMigrationStatusMap = loadMigrationStatusMapFromCSV(inputMigrationStatusFilename)

    print '===Start algoMapping post-actions validation process'
    for key in actionItemsMap:
        print '   validating ' + str(key)
        starId = key[0]
        cashCFD = key[1]
        dmaAlgo = key[2]
        targetMigrationStatus = actionItemsMap[key]
        product_group_key = 'AUSHARESCASH' if cashCFD == 'Cash' else 'AUSHARESCFD'
        algorithm_out_key = 'algorithm_out'
        algorithm_parameters_key = 'algorithm_parameters'

        if targetMigrationStatus:
            algorithm_out_key = 'n_algorithm_out'
            algorithm_parameters_key = 'n_algorithm_parameters'

        for csvAlgoMapping in csvAlgoMappingMap[starId]:
            if csvAlgoMapping['product_group'] != product_group_key:
                # skip
                continue
            # for each algo param, compare with the db one
            isMatchedRecordFound = False
            for dbAlgoMappping in dbAlgoMappingMap[starId]:
                if isPrimaryKeyMatched(dbAlgoMappping, csvAlgoMapping):
                    # found the same record in db
                    if csvAlgoMapping[algorithm_out_key] != dbAlgoMappping['algorithm_out'] or \
                        csvAlgoMapping[algorithm_parameters_key] != dbAlgoMappping['algorithm_parameters']:
                        if errorMap.get((starId, 'algoMapping')):
                            errorMap[(starId, 'algoMapping')] += csvAlgoMapping['market'] + ',' + csvAlgoMapping['algorithm_in'] + '|'
                        else:
                            errorMap[(starId, 'algoMapping')] = csvAlgoMapping['market'] + ',' + csvAlgoMapping['algorithm_in'] + '|'
                        print '   [Error]Client ' + starId + ' algo param mismatch for ' + csvAlgoMapping['algorithm_in'] + ' ' + dbAlgoMappping['product_group'] + ' ' + dbAlgoMappping['market']
                    else:
                        isMatchedRecordFound = True
            if not isMatchedRecordFound:
                print '   [Error]Cannot find the following record in db, might be some error when inserting ' + str(csvAlgoMapping) + ', please manually correct db and csv'

    backupFile(inputAlgoParamsFilename)

    print '===Export updated csvAlgoMappingMap to file ' + inputAlgoParamsFilename
    writeCSVAlgoMappingMapToFile(inputAlgoParamsFilename, csvAlgoMappingMap)

    if errorMap:
        print '   error occured during post-actions validation process'
        print errorMap
        print '===Terminating the script'
        return

    print '===All completed without errors'
    print '===Write migration summary to file'
    writeMigrationSummary(actionItemsMap, csvAlgoMappingMap)
    print '===End of script'

    return

if __name__ == '__main__':
    main(sys.argv)
