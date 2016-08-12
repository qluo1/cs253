## oma project configuration
## can be imported by projects
import os

from gns import *
## om2 codebase
##  svn+ssh://asiaoma.svn.services.gs.com/svnroot/asiaoma/gate/trunk
CODE_BASE   = "/local/data/home/eqtdata/sandbox/luosam/works/projects/omaasia"

GSVERSION   = os.path.join(CODE_BASE,"gscompversion")
GSLOG       = os.path.join(CODE_BASE,"gslog","src")
GSLOG_INC   = os.path.join(CODE_BASE,"gslog","include")
GSLOG_TEST  = os.path.join(CODE_BASE,"gslog","test")
GSLOG_LIB = os.path.join(CODE_BASE,"gslog","lib","linux6_64_DBG")

GSCPPUTIL   = os.path.join(CODE_BASE,"gscpputil")
GSCPPUTIL_LIB = os.path.join(GSCPPUTIL,"linux6_64_DBG")

IVCOM       = os.path.join(CODE_BASE,"ivcom","src")
IVCOM_INC   = os.path.join(CODE_BASE,"ivcom","inc")
IVCOM_EXTINC= os.path.join(CODE_BASE,"ivcom","extinc")
IVCOM_SIMU  = os.path.join(CODE_BASE,"ivcom","simulator")
## GSFIX
GSFIX_BASE  = os.path.join(CODE_BASE,"fixlibs")
GSFIX       = os.path.join(GSFIX_BASE,"gsfix")
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

## LIBSRC
LIBSRC     = os.path.join(CODE_BASE,"libsrc")
EQCPPUTIL  = os.path.join(LIBSRC,"eqcpputil")
EQDATASTORE= os.path.join(LIBSRC,"eqdatastore")
EQUTIL     = os.path.join(LIBSRC,"equtil")
EQCONFIG   = os.path.join(LIBSRC,"eqconfig")

## OMA
OMA_CONST       = os.path.join(CODE_BASE,"omaconsts")
OMA_CODE_BASE   = os.path.join(CODE_BASE,"oma")
OMA_BASE        = os.path.join(OMA_CODE_BASE,"base")
OMA_AUTH        = os.path.join(OMA_CODE_BASE,"authorization")
OMA_FILTER      = os.path.join(OMA_CODE_BASE,"filter")
OMA_CBB         = os.path.join(OMA_CODE_BASE,"cbb")
OMA_CLIENT      = os.path.join(OMA_CODE_BASE,"client")
OMA_NOTIFY      = os.path.join(OMA_CODE_BASE,"notification")
OMA_ORBIX       = os.path.join(OMA_CODE_BASE,"orbix")
OMA_FACTORY     = os.path.join(OMA_CODE_BASE,"factory")
OMA_OMAD        = os.path.join(OMA_CODE_BASE,"omad")
OMA_DBFACTORY   = os.path.join(OMA_CODE_BASE,"dbFactory")
OMA_ENTRY       = os.path.join(OMA_CODE_BASE,"entry")
#CDL_UTIL        = os.path.join(CODE_BASE,"cdl","util")
CDL_UTIL        = os.path.join(CODE_BASE,"public")
OMA_VALID       = os.path.join(OMA_CODE_BASE,"validation")

## gate -- asia oma
OMA_GATE        = os.path.join(CODE_BASE,"gate","oma")
GATE_CBB        = os.path.join(OMA_GATE,"cbb")


## kevlar
KEVLAR          = os.path.join(CODE_BASE,"kevlar")
KEVLAR_RES      = os.path.join(KEVLAR,"resources")
## generated files
KEVLAR_RECS     = os.path.join(KEVLAR,"records")

OM2_ENGINE      = os.path.join(CODE_BASE,"om2","engine")

## rds
RDS         = os.path.join(CODE_BASE,"rds-distribution")
RDS_CLIENT  = os.path.join(RDS,"client")
RDS_RECORDS = os.path.join(RDS,"client","records")



DEBUG = True

CCFLAG_GS = "-fmessage-length=0 -pthread -finline-functions"
## CCFLAG
if DEBUG:
    CCFLAG_GS += " -g"

## GS build CXXFLAGS
CXXFLAG_GS = "-pipe -DUSE_GNS -m64 -D__64BIT__ -DSYB_LP64 -D__LINUX -D__LINUX -D_64BIT_RHEL5_OR_GREATE -D__INOTIFY=1 \
              -DBOOST_FILESYSTEM_VERSION=3 -ffor-scope \
              -Wall -Wno-unused-const-variable -Wno-deprecated -Wno-reorder -Wno-tautological-compare \
              -D_RWCONFIG=12d -DRW12D -DRWDBTOOLS_4 -D_FILE_OFFSET_BITS=64 -DORBIX_VERSION=2000 "


EQCPPUTIL_LIB =os.path.join(EQCPPUTIL,"lib","linux6_64b")

OMACLIENT_LIB = os.path.join(OMA_CLIENT,"lib","linux6_64b")

LIBPATHS    = [ UUID_LIB,
                GSAUTH_LIB,
                PYTHON_LIB,
                BOOST_LIB,
                GSKRB_LIB,
                LIBEV_LIB,
                PCRE_LIB,
                RW_LIB,
                ORBIX_LIB,
                ORBIX_SHLIB,
                ORBIX_SHLIB_DEFAULT,
                OMACLIENT_LIB,
                EQCPPUTIL_LIB,
                GSLOG_LIB,
                GSCPPUTIL_LIB,
               ]

## rt for time.h, dl for dlopen/dlclose
LIBS_IVCOM = [
                "pcre",
                "pthread",
                "uuid",
                "rt",
                "dl",
                "python2.7",
               ]


#usr/bin/g++ -D_REENTRANT -g      -Wl,-export-dynamic  -lrt -luuid -o nvp linux6_64b/nvp.o ../../..//oma/cbb/lib/linux6_64b/libcbb.a ../../..//oma/base/lib/linux6_64b/libomabase.a ../../..//omaconsts/lib/linux6_64b/libomaconsts.a ../../..//libsrc/eqcpputil/lib/linux6_64b/libeqcpputil.a ../../..//libsrc/eqconfig/lib/linux6_64b/libeqconfig-mt.a ../../..//lib/linux6_64b/libequtil-mt.a ../../..//gslog/lib/linux6_64_DBG/libgslog-mt.a ../../..//gscpputil/linux6_64_DBG/libgscpputil.a ../../..//gscpputil/sybase/linux6_64_DBG/libgscppsybase.a    -lthread3212d -lthrexcept2612d -lsync4112d -litc2612d -lpointer2812d -lfunctor2612d -lfunctor_list2612d  -L/gns/mw/lang/c/roguewave-sourcepro-11.1-1/64bit/lib -ltls9112d -lpthread -lutil -lrt -ldl -lz -luuid
LIBS_RW         = [
    "thread3212d",
    "threxcept2612d",
    "sync4112d",
    "itc2612d",
    "pointer2812d",
    "functor2612d",
    "functor_list2612d",
    "tls9112d",
    "dbt7215d",
    "ctl7215d",
]

LIBS_ORBIX = [
    "it_dynany",
    "it_poa",
    "it_location",
    "it_art",
    "it_ifc",
    "it_naming",
    "it_atli2_ip",
    "it_atli2",
    "it_giop",
    "it_key_replacer_stubs",
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

LIBS_OMA = [
            'omaclient',
            'eqcpputil',
            ]

# vim: syntax=python nu softtabstop=4 tabstop=4 shiftwidth=4 expandtab:
