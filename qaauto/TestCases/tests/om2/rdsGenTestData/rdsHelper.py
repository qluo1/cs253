from rdsRepositoryCatalog import rdsRepositoryCatalog as CATALOG, rdsRepositoryCatalogEnums as ENUMS


def enum_lookup(label,idx):
    """
        from index to enum label
        -- used by parse ivcom message
    """
    enums = ENUMS['enums']

    values = enums[label]['values']
    for k in values:
        if values[k] == idx:
            return k

def lookup_enum(label,name):
    """
        from name to enum index
            - ignore case lookup
    """
    enums = ENUMS['enums']

    ## try default
    if label in enums:
        values = enums[label]['values']
        for k in values:
            if k.lower() == name.lower():
                return values[k]
    ## try add Om2 prefix
    if "Rds" + label in enums:
        values = enums["Om"+label]['values']
        for k in values:
            if k.lower() == name.lower():
                return values[k]

    raise ValueError("failed enum lookup:%s,%s" % (label,name))

def enrich_enum(tableName,msg):
    """ for each table item each rich enum field.  """

    #log.debug("enrich enum tableName: %s, msg: %s" % (tableName,msg))
    if tableName in CATALOG['tables']:
        table = CATALOG['tables'][tableName]
        for k,v in table['columns'].items():
            meta = v.get('meta-fields') or [{'value': None}] ##or fake meta for rds catalog
            if k in msg:
                if v['type'] == 'table':
                    #assert type(msg[k]) == list
                    ## trea table as dict
                    if  meta[-1]['value'] == 'struct':
                        #msg[k] = msg[k][0]
                        #log.info("key: %s, meta: %s, msg: %s" % (k,meta, msg))
                        ## recursive here
                        if type(msg[k]) == dict:
                            enrich_enum(v['tablename'],msg[k])
                        elif type(msg[k]) == list:
                            ## om2 bug in catalog
                            for m in msg[k]:
                                enrich_enum(v['tablename'],m)
                        else:
                            assert False,"unexpect type: key: %s, meta: %, msg: %s" % (k,meta,msg[k])
                    else:
                        assert type(msg[k]) == list
                        ## treat table as list
                        for m in msg[k]:
                            enrich_enum(v['tablename'],m)
                ## handle enum enrichment
                if v['type'] == 'ubyte' and 'enum' in v:
                    msg[k] = enum_lookup(v['enum'],msg[k])



class IvComDictHelper():
    """
        create IvComJson message based on
        - catalog
        - enums
        - table specified
    """
    def __init__(self,tblName,catalog=CATALOG,enums=ENUMS):
        """
        """
        self.tbl = tblName
        self.tblscheme = catalog['tables'][tblName]
        self.enums = enums['enums']
        self.msg = {}


    def set(self,colName,value):
        """
        """
        assert colName in self.tblscheme['columns'].keys(), "colName unknown: %s,%s for tbl: %s" % (colName,value,self.tbl)
        colscheme = self.tblscheme['columns'][colName]

        if colscheme['type'] == 'table':
            ## set single table value
            if type(value) == dict:
                if colscheme['meta-fields'][-1]['value'] == 'collection':
                    self.msg[colName] = [value]
                else:
                    self.msg[colName] = value
            ## set list of values
            elif type(value) == list and colscheme['meta-fields'][-1]['value'] == 'collection':
                self.msg[colName] = value
            ## error
            else:
                raise ValueError("unknown input:%s for col %s" % (value,colName))

        elif colscheme['type'] == 'ubyte' and colscheme['enum']:
            if type(value) == int:
                self.msg[colName] = value
            else:
                ## convert string to int
                value_enum = lookup_enum(colscheme['enum'],value)
                self.msg[colName] = value_enum
        else:
            self.msg[colName] = value

    def __str__(self):
        """
        """
        return json.dumps(self.msg)


import collections
## convert all unicode to string, ivcom don't like unicode
def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data
