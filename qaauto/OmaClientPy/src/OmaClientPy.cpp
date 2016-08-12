#include <Python.h>
#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <iostream>
#include <vector>
#include <string>
#include <boost/scoped_ptr.hpp>

#include "OmaClientMgr.hpp"

#include <OmaOrderDataFactory.H>
#include <OmaDummyProductFactory.H>
#include <OmaDummyAccountFactory.H>
#include <OmaDummyUserFactory.H>
#include <OmaNVPNames.H>
#include <GSLog.H>

using namespace std;
bool setuplog(const string& cfgpath, const string& name, const string& workdir)
{

    if(!gslog.setup(cfgpath.c_str(),name.c_str(),workdir.c_str()))
    {
        cerr << "Unable to setup gslog" <<endl;
        return false;
    }

    gslog.show_thread_id(true);

    GSLOGFINFO << "setup gslog ok!" <<endl;

    return true;
}

// singleton -- required
boost::scoped_ptr<OmaOrderDataFactory> pDataFactory(new OmaOrderDataFactory());
OmaDummyProductFactory* pProductFactory = OmaDummyProductFactory::create_factory();
OmaDummyUserFactory* pUserFactory =  OmaDummyUserFactory::create_factory();
boost::scoped_ptr<OmaDummyAccountFactory> pAccountFactory( new OmaDummyAccountFactory());


BOOST_PYTHON_MODULE(OmaClientPy)
{
    namespace bp = boost::python;

    PyEval_InitThreads();

    bp::def("setuplog",setuplog);

    bp::class_<OmaClientManager,boost::noncopyable>("OmaClientManager",bp::init<std::string>())
        .def("logon",&OmaClientManager::logon)
        .def("registerCallback",&OmaClientManager::registerCallback)
        .def("stop",&OmaClientManager::stop)
        .def("send",&OmaClientManager::send_transaction)
  ;

}


