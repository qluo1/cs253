"""  using pyparsing parsing rds line records.

"""
from pyparsing import *
from datetime import datetime
########### rule for parsing rds line ##############
Item = nestedExpr("[","]")
Items = OneOrMore(Item)
rdsLine = oneOf("Insert Update Delete") + Word("df") + Word(alphas + nums) + Items

def _convert_set_to_dict(items):
    """ internal helper parse collection."""
    assert isinstance(items,list)
    #print item
    ret = []

    for item in items:
        int(item[0])
        ret.append(_convert_list_to_dict(item[2:]))

    if len(ret) == 1: ret = ret[0]
    return ret

def _convert_list_to_dict(item):
    """ internal helper parse rds list to dict."""
    assert isinstance(item,list)
    #print item
    ret = {}
    for i in item:
        #print i
        if i[1] == "String":
            if len(i) == 3:
                ret[i[0]] = i[2]
            else:
                ret[i[0]] = None
        elif i[1] == "Double":
            ret[i[0]] = float(i[2])
        elif i[1] in ("Long","Int"):
            ret[i[0]] = int(i[2])
        elif i[1] == "collection":
            #import pdb;pdb.set_trace()
            ret[i[0]] = _convert_set_to_dict(i[2:])
        elif i[1] == 'Bool':
            ret[i[0]] = bool(i[2])
        elif i[1] == "DateTime":
            ret[i[0]] = (i[2], i[3])
        elif i[1] == "Date":
            ret[i[0]] = i[2]
        else:
            raise ValueError("unexpected type: %s " %i)

    return ret

def parse_rds_line(line):
    """ parsing rds line into list."""

    ## strip double quota
    line = line.replace('"','')
    s = datetime.now()
    result = rdsLine.parseString(line,parseAll=True).asList()
    e = datetime.now()
    #print e - s
    action = result[0]
    name = result[2]
    assert result[1] == "df"
    return dict(action=action,
                name=name,
                data=_convert_list_to_dict(result[3:]))




