""" SConstruct GNS reference.

include external libs under: gns, sw

"""
import os
import sys
import glob

GNS         = "/gns/software/eqtech/third-party"
## GSAUTH
GSAUTH_BASE = "/gns/mw/security/authn/gsauthn-gcc-4.4-64bit-4.2.0"
GSAUTH_INC  = os.path.join(GSAUTH_BASE,"include")
GSAUTH_LIB  = os.path.join(GSAUTH_BASE,"lib")

##uuid
UUID_BASE   = "/sw/external/libuuid-2.17.2-12.el6"
UUID_INC    = os.path.join(UUID_BASE,"include")
UUID_LIB    = os.path.join(UUID_BASE,"lib64")
## pcre
PCRE_BASE   = os.path.join(GNS,"pcre.opt-7.7_1")
PCRE_INC    = os.path.join(PCRE_BASE,"include")
PCRE_LIB    = os.path.join(PCRE_BASE,"lib")
## zlib
ZLIB_BASE   = "/gns/mw/lang/c/zlib-1.2.3-3.el5.gns"
ZLIB_INC    = os.path.join(ZLIB_BASE,"include")
ZLIB_LIB    = os.path.join(ZLIB_BASE,"lib64")
##cppunit
CPPUNIT_BASE= os.path.join(GNS,"cppunit.opt-1.12.1_1")
CPPUNIT_INC = os.path.join(CPPUNIT_BASE,"include")
CPPUNIT_LIB = os.path.join(CPPUNIT_BASE,"lib")
##python
PYTHON_BASE = "/gns/mw/lang/python/modules/2.7.2/python-devel-runtime-2.7"
PYTHON_INC  = os.path.join(PYTHON_BASE,"include")
PYTHON_LIB  = os.path.join(PYTHON_BASE,"lib64")
## curl
CURL_BASE   = "/gns/software/infra/bai/util/curl-7.26.0"
CURL_INC    = os.path.join(CURL_BASE,"include")
CURL_LIB    = os.path.join(CURL_BASE,"lib64")
## sybase
SYBASE_BASE = "/gns/mw/dbclient/sybase/oc/openclient-12.5.1.ESD21.v01/OCS-12_5"
SYBASE_INC  = os.path.join(SYBASE_BASE,"include")
SYBASE_LIB  = os.path.join(SYBASE_BASE,"lib")
## jsoncpp
JSON_BASE   = os.path.join(GNS,"jsoncpp-0.6.0_rc2")
JSON_INC    = os.path.join(JSON_BASE,"include")
JSON_LIB    = os.path.join(JSON_BASE,"lib")
## MONGO
MONGO_BASE  = "/gns/mw/dbclient/mongodb/cxx/mongodb-cxx-driver-2.4.6.v02"
MONGO_INC   = os.path.join(MONGO_BASE,"include")
MONGO_LIB   = os.path.join(MONGO_BASE,"lib")
## libevent
LIBEV       = os.path.join(GNS,"libevent.opt-2.0.19_1")
LIBEV_INC   = os.path.join(LIBEV,"include")
LIBEV_LIB   = os.path.join(LIBEV,"lib")
## GS KRB
GSKRB_BASE  = "/gns/software/infra/bai/krb5-1.10"
GSKRB_INC   = os.path.join(GSKRB_BASE,"include")
GSKRB_LIB   = os.path.join(GSKRB_BASE,"lib")
##
ABNERT      = "/gns/software/eqtech/products/Core/CentralExecutionPath/ateam-3.74"
ABNERT_SIMU = os.path.join(ABNERT,"AbnerSimulator")
ABNERT_SIMU_INC  = os.path.join(ABNERT_SIMU,"include")
## MDT
#MDT         = "/gns/mw/mds/mdtcpp/mdtcpp-gcc-4.4.5-64-1.2.30.E1-1"
### latest PROD version
#MDT         = "/sw/ficc/mdt_cpp-1.0.115"
MDT         = "/sw/ficc/mdt_cpp-1.0.129"
MDT_INC     = os.path.join(MDT,"linux64_g44.hdr")
MDT_LIB     = os.path.join(MDT,"linux64_g44.dll")
#XERCES_LIB  = os.path.join(MDT_LIB,"xerces2.8")

## RW OMA
RW         = "/gns/mw/lang/c/roguewave-sourcepro-11.1-1/64bit"
RW_LIB     = os.path.join(RW,"lib")

ORBIX_BASE = "/gns/mw/lang/c/iona-orbix_dev-run-6.3-01-GS1/6.3-01-GS1"
ORBIX       = os.path.join(ORBIX_BASE,"asp","6.3")
ORBIX_LIB   = os.path.join(ORBIX,"lib","lib64")
ORBIX_SHLIB   = os.path.join(ORBIX_BASE,"shlib","lib64")
ORBIX_SHLIB_DEFAULT   = os.path.join(ORBIX_BASE,"shlib","default","lib64")

##boost
BOOST_GNS="/gns/mw/cpe/tww/gs-tww-libboost-1.55.0-1rhel6"
BOOST_INC = os.path.join(BOOST_GNS,"include")
BOOST_LIB = os.path.join(BOOST_GNS,"lib64")


################################################################################
## common collect src, compile obj,shobj utils
################################################################################
def compile_comp(libname,srcdir,outdir,env,surfix,excludes=[]):
    """
    compile source into library/sharedlibrary
    input: libname
           source folder
           build output folder

           env
           surfix i.e. source file surfix.
           excludes i.e. source files to be excluded.

    """
    assert libname and srcdir and outdir and env and surfix


    obj    = []
    shobj   = []
    ## workout common source codes i.e. .c, .C, .cpp
    src = glob.glob(srcdir + "/*" + surfix)
    ## collect/filter
    src= [s for s in src if s.split("/")[-1] not in excludes]

    if len(src) ==0:
        import pdb;pdb.set_trace()
    assert len(src) > 0, libname

    for o in src:
        t = o.replace(o[o.rfind("."):] ,".o")
        obj.append(os.path.join(outdir,t.split("/")[-1]))
        ts =o.replace(o[o.rfind("."):] ,".o_fpic")
        shobj.append(os.path.join(outdir,ts.split("/")[-1]))

    # compile
    for s,o,so in zip(src,obj,shobj):
        env.Object(target=o,source=s)
        env.SharedObject(target=so,source=s)

    ## library
    env.Library(target=os.path.join(outdir,libname),source=obj)
    ## shared library
    env.SharedLibrary(target=os.path.join(outdir,libname),source=shobj)


def compile_comp_oma(libname,**kw):
    """
    compile source into library/sharedlibrary
    input: libname
           source folder
           build output folder

           env
           surfix i.e. source file surfix.
           excludes i.e. source files to be excluded.

    """
    indir  = kw['indir']
    outdir  = kw['outdir']
    env     = kw['env']
    surfix  = kw.get('surfix',".C")
    idl     = kw.get('idl',False)
    excludes = kw.get('excludes',[])
    includes = kw.get('includes',[])


    assert libname and indir and outdir and env and surfix


    obj    = []
    shobj   = []
    ## workout common source codes i.e. .c, .C, .cpp
    src = glob.glob(os.path.join(indir,"src") + "/*" + surfix)
    ## collect/filter
    src= [s for s in src if s.split("/")[-1] not in excludes]

    ## corba idl
    if idl:
        src += glob.glob(os.path.join(indir,"idl",OMA_BUILD) + "/*.cc")

    assert len(src) > 0

    ## filter out symbolic link for omaclient
    #import pdb;pdb.set_trace()
    src = [o for o in src if not os.path.islink(o)]

    if len(includes) > 0:
        src += includes

    for o in src:
        t = o.replace(o[o.rfind("."):] ,".o")
        obj.append(os.path.join(outdir,t.split("/")[-1]))
        ts =o.replace(o[o.rfind("."):] ,".o_fpic")
        shobj.append(os.path.join(outdir,ts.split("/")[-1]))

    # compile
    for s,o,so in zip(src,obj,shobj):
        env.Object(target=o,source=s)
        env.SharedObject(target=so,source=s)

    ## library
    env.Library(target=os.path.join(outdir,libname),source=obj)
    ## shared library
    env.SharedLibrary(target=os.path.join(outdir,libname),source=shobj)


