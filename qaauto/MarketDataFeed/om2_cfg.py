## om2 project configuration
## can be imported by projectj
import os,sys
from gns import *

## om2 codebase
CODE_BASE   = "/home/luosam/ws/gitworks/om2"
GSVERSION   = os.path.join(CODE_BASE,"gscompversion")
GSLOG       = os.path.join(CODE_BASE,"gslog","src")
GSLOG_INC   = os.path.join(CODE_BASE,"gslog","include")
GSLOG_TEST  = os.path.join(CODE_BASE,"gslog","test")
GSCPPUTIL   = os.path.join(CODE_BASE,"gscpputil")
IVCOM       = os.path.join(CODE_BASE,"ivcom","src")
IVCOM_INC   = os.path.join(CODE_BASE,"ivcom","inc")
IVCOM_EXTINC= os.path.join(CODE_BASE,"ivcom","extinc")
IVCOM_SIMU  = os.path.join(CODE_BASE,"ivcom","simulator")
## GSFIX
GSFIX_BASE  = os.path.join(CODE_BASE,"fixlibs")
GSFIX       = os.path.join(GSFIX_BASE,"gsfix")

## GSCUSHMDB
GSCUSHMDB   = os.path.join(CODE_BASE,"gscushmdb")

## CURE
CURE        = os.path.join(CODE_BASE,"cure","application")
EQMON       = os.path.join(CODE_BASE,"eqmon","src")
EQMON_INC   = os.path.join(CODE_BASE,"eqmon","include")
EQCYCLOPSMON= os.path.join(CODE_BASE,"eqcyclopsmon","src")
EQCYCLOPSMON_INC = os.path.join(CODE_BASE,"eqcyclopsmon","include")

CYCLOPSMON  = os.path.join(CODE_BASE,"cyclops","monitor","src")
CYCLOPSMON_INC = os.path.join(CODE_BASE,"cyclops","monitor","inc")
CYCLOPSPUB = os.path.join(CODE_BASE,"cyclops","publisher","src")
CYCLOPSPUB_INC = os.path.join(CODE_BASE,"cyclops","publisher","inc")
CYCLOPSMSG  = os.path.join(CODE_BASE,"cyclops","messageDefinitions","src")
CYCLOPSMSG_INC = os.path.join(CODE_BASE,"cyclops","messageDefinitions","inc")

GSMD        = os.path.join(CODE_BASE,"gsmd")
GSMD_GSMD   = os.path.join(GSMD,"gsmd")
GSMD_IMPL   = os.path.join(GSMD,"impl")

GSMD_MDT    = os.path.join(GSMD,"mdt")
GSMD_RFA    = os.path.join(GSMD,"rfa")
DEBUG = False


CCFLAG_GS = "-fmessage-length=0 -pthread -finline-functions"
## CCFLAG
if DEBUG:
    CCFLAG_GS += " -g"
else:
    CCFLAG_GS += " -O3"

## GS build CXXFLAGS
CXXFLAG_GS = "-pipe -DUSE_GNS -m64 -D__64BIT__ -DSYB_LP64 -D__LINUX -D__LINUX -D_64BIT_RHEL5_OR_GREATE -D__INOTIFY=1 \
              -DBOOST_FILESYSTEM_VERSION=3 -ffor-scope -Wall"

## all build output
BUILD_DIR = "/home/luosam/ws/works/projects/lib"

LIBPATHS    = [BUILD_DIR,CPPUNIT_LIB,UUID_LIB,GSAUTH_LIB,JSON_LIB,PYTHON_LIB,BOOST_LIB,MONGO_LIB,GSKRB_LIB,LIBEV_LIB]

## rt for time.h, dl for dlopen/dlclose
LIBS_IVCOM        = ["pcre",
               "pthread",
               "cppunit",
               "uuid",
               "rt",
               "dl",
               "gsauthn",
               "json_linux-gcc-4.4.7_libmt",
               "python2.7",
               ]

## simulator
LIBS_SIMU  = LIBS_IVCOM + [
               "expat", # XML
               "event",
               "boost_filesystem",
               "boost_thread-mt",
               "boost_system",
               "mongoclient",
               "krb5",
               "gssapi_krb5",
               ]

# vim: syntax=python nu softtabstop=4 tabstop=4 shiftwidth=4 expandtab:
