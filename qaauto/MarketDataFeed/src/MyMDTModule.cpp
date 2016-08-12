#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <vector>

#include "MyMDTListener.h"
#include "GSLog.H"

using namespace std;

namespace bp = boost::python;


bp::dict test_func()
{
    bp::dict data;

    data["name"] = "test";
    data["value"] = 123;
    return data;
};

bool setuplog(const string& cfgpath, const string& name,
                              const string& workdir)
{

    if(!gslog.setup(cfgpath.c_str(),name.c_str(),workdir.c_str()))
    {
        cerr << "Unable to setup gslog" <<endl;
        return false;
    }

    gslog.show_thread_id(true);

    GSLOGFINFO << "setup gslog ok!" <<endl;

    return true;
};

BOOST_PYTHON_MODULE(MyMDTModule)
{

    namespace bp=boost::python;
    // Necessary because of usage of the ReleaseGil/AquireGL class
    PyEval_InitThreads();

    // manager
    bp::class_<MyMDTListener,boost::noncopyable>( "MyMDTListener" ,bp::init<string,string,vector<string> >())
        .def("subscribe",   &MyMDTListener::subscribe)
        .def("unsubscribe", &MyMDTListener::unsubscribe)
        .def("setupOnDataCB",&MyMDTListener::setupCallback)
        .def("setupOnStatusCB",&MyMDTListener::setupStatusCB)
    ;

    // stringVector
    bp::class_< vector<string>,
      boost::shared_ptr< vector< string > > >( "StringVector" )
        .def( bp::vector_indexing_suite< vector< string > >() )
    ;

    bp::def("test_dict",test_func);
    bp::def("setuplog",setuplog);

};

