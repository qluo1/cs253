""" nvp definition in python.

parse OMA original def and generate python def.

- nvp_types
- nvp_names
- nvp_id_names

"""
import sys
import os
from datetime import datetime, date
import ctypes

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

## source of NVPs 
OMA_SOURCE = "/local/data/home/eqtdata/sandbox/luosam/works/projects/omaasia"
NVP_NAME = os.path.join(OMA_SOURCE, "omaconsts/OmaDefineNVPs.txt")
NVP_TYPE = os.path.join(OMA_SOURCE, "omaconsts/OmaTypes.txt")

if not os.path.isfile(NVP_NAME):
    NVP_NAME = os.path.join(CUR_DIR,"OmaDefineNVPs.txt")
if not os.path.isfile(NVP_TYPE):
    NVP_TYPE =  os.path.join(CUR_DIR,"OmaTypes.txt")

class NVP_C_TYPE:
    """ oma/base/include/OmaNVP.H
    enum OmaNVPType
    {
    Int, UInt, Long, ULong, Short, UShort,
    Char, UChar, Float, Double, String,
    Boolean, Date, DateTime, Enum, Unknown,
    MilliTime, Binary
    };
    """
    Int, UInt, Long, ULong, Short, UShort,\
    Char, UChar, Float, Double, String,\
    Boolean, Date, DateTime, Enum, Unknown,\
    MilliTime, Binary = range(18)


def enrich_type(input, typerefs):

    assert input
    if input =="Int":
        return int
    elif input == "Long":
        return ctypes.c_long
    elif input == "Double":
        return ctypes.c_double
    elif input == "Float":
        return float
    elif input == "String":
        return str
    elif input == "Date":
        return date
    elif input == "DateTime":
        return datetime
    elif input.startswith("OmaTypes"):
        assert "::" in input
        t = input.split("::")[1]
        if t in typerefs:
            return t
        else:
            return input

def parse_nvp_type(fn):
    """ return nvp type definition.

    input: OmaTypes
    """

    res = {}

    current = None
    current_count = None
    func = 0
    with open(fn,"r") as f:
        for ln in f:
            ## parsing line by line
            line = ln.strip()
            ## remove comment line
            if line.startswith("//") or line == "":
                continue
            ## split out line and comment
            if "//" in line:
                line,_ = line.split("//",1)

            #print line
            if line.startswith("T_Begin"):
                assert current == None
                assert current_count == None
            elif line.startswith("T_Fun"):
                func +=1 
                continue
            elif line.startswith("T_Enum"):
                assert current == None
                ## set current
                current = line.split()[1].strip()
                res[current] = {}
            elif line.startswith("T_End"):
                ## reset
                current = None
                current_count = None
            #elif line.startswith("No") or "=" in line:
            #    ## set current count
            #    current_count = -1
            else:
                try:
                    comment = None
                    assert "," in line
                    line,comment = line.split(",",1)
                    comment = comment.strip()
                    ## strip double quote
                    if comment.startswith('"') and comment.endswith('"'):
                            comment = comment[1:-1]
                    ######################
                    ## TODO: handle multiple items
                    ## multiple items
                    #if func > 1:
                    #    comment = comment.split()
                    #    # clean up quote
                    #    for comm in comment:
                    #        if comm.startswith('"'):
                    #            comm = comm[1:]
                    #        if comm.endswith('"'):
                    #            comm = comm[:-1]

                    if "=" in line:
                        current_key,current_count = line.split("=")
                        current_count = int(current_count)
                    else:
                        if current_count  == None:
                            current_count = 0
                        else:
                            current_count += 1
                        current_key = line
                    assert current_key
                    assert current_count != None
                    res[current][current_count] = (current_key,comment)
                except Exception,e:
                    print line,e
                    exit(1)
    return res

def parse_nvp_name(fn,typedefs):
    """ return a scema of NVP name definition.

    convert OmaTypes.txt into python nvp type.

    input: 1) OmaDefineNVPS.txt
           2) typedefs i.e. nvp type definition parsed from OmaTypes.txt

    out: python nvp definition.
    """

    res = {}

    with open(fn,"r") as f:
        for ln in f:
            ## parsing line by line
            line = ln.strip()
            ## remove comment line
            if line.startswith("//") or line == "":
                continue
            ## remove comment section of the line
            if "//" in line:
                line = line.split("//")[0]
            #################
            ## nvp line
            #################
            #print line
            assert line.startswith("defineNVP") , line
            name,value = line.split("=",1)
            try:
                ## simplify with basic type
                vals = name[name.find("(")+1 : name.find(")")].split(",")
                name = vals[0].strip()
                #if name == "OmaNvpVersionNumber": import pdb;pdb.set_trace()
                #if name == "OmaNvpOrderFlags": import pdb;pdb.set_trace()
                #if name == "OmaNvpTimeInForce": import pdb;pdb.set_trace()

                if len(vals) == 2:
                    type = vals[1].strip()
                elif len(vals) == 3:
                    ## prefer more specific type
                    #defineNVP( OmaNvpCreationTime, String, DateTime )
                    type = vals[2].strip()
                elif len(vals) == 4:
                    ## 'defineNVP( OmaNvpOrderFlags, String, Int, OmaTypes::OrderFlags )        = 1028 '
                    type = vals[1].strip()
                else:
                    assert False, "unexpected: %s" % line
                res[name] = [int(value),enrich_type(type,typedefs)]

            except Exception:
                name = name[name.find("(")+1 : name.find(")")].strip()
                res[name] = [int(value),None]
            ## enrich type field

    return res



## i.e. OmaTypes::UserType enum
## example
# 'ValResultType': {0: ('ValPassed', None),
#                   1: ('ValFailed', None),
#                   2: ('ValRequired', None),
#                   3: ('ValWarning', None)},
#
nvp_types = parse_nvp_type(NVP_TYPE)

## dict of OmaNVPNames
# 'OmaNvpACTModifier': (1883, <type 'str'>),
# 'OmaNvpACTNoClearing': (1885, <type 'str'>),
nvp_names = parse_nvp_name(NVP_NAME,nvp_types)

## enrich nvp_name to nvp_types as dict
for k,v in nvp_names.iteritems():
    if v[1] in nvp_types:
        v[1] = {v[1]: nvp_types[v[1]]}

nvp_id_names = {v[0]:(k,v[1]) for k,v in nvp_names.iteritems()}


__all__ = [

        'nvp_types',
        'nvp_names',
        'nvp_id_names',
]

if __name__ == "__main__":

    from pprint import pprint
    print "---------- nvp type. -----------"

    pprint(nvp_types)

    print "----------nvp name. ------------"
    pprint(nvp_names)

    print "----------nvp id/name. ------------"
    pprint(nvp_id_names)


