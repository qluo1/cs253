#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <iostream>
#include <vector>
#include "IvComPyManager.h"
#include "IvComPyClient.h"
#include "IvComPyDssClient.h"
#include "IvComPyServer.h"
#include "IvComServerDatastream.hpp"

using namespace std;

BOOST_PYTHON_MODULE(IvComPy)
{

    namespace bp=boost::python;
    // Necessary because of usage of the ReleaseGil class
    PyEval_InitThreads();

    // manager
    bp::class_<IvComPyManager,boost::noncopyable>("IvComPyManager")
        .def("init",&IvComPyManager::init)
        .def("initJson",&IvComPyManager::initJson)
        .def("setuplog",&IvComPyManager::setuplog)
        .def("run",&IvComPyManager::run)
        .def("stop",&IvComPyManager::stop)
        .def("getClientRequest",&IvComPyManager::getClientRequest,
                bp::return_internal_reference<>())
        .def("getDss",&IvComPyManager::getDss,
                bp::return_internal_reference<>())
        .add_property("clientRequestNames",&IvComPyManager::getClientRequestNames)
        .add_property("dssNames",&IvComPyManager::getDssNames)
        // serverDatastreamClient
        .def("getServerDatastreamClient",&IvComPyManager::getServerDatastreamClient,
                bp::return_internal_reference<>())
        .add_property("serverDatastreamNames",&IvComPyManager::getServerDatastreamClientNames)

		//request servers
		.def("getRequestServer", &IvComPyManager::getRequestServer,
				bp::return_internal_reference<>())
		.add_property("requestServerNames", &IvComPyManager::getRequestServerNames)

        //imagelive client
        .def("getImageLiveClient", &IvComPyManager::getImageLiveClient,
                bp::return_internal_reference<>())
        .add_property("ImageLiveClientNames", &IvComPyManager::getImageLiveClientNames)
    ;

    // stringVector
    bp::class_< vector<string>,
      boost::shared_ptr< vector< string > > >( "StringVector" )
        .def( bp::vector_indexing_suite< vector< string > >() )
    ;

    // clientRequest
    bp::class_<IvComPyClient,boost::noncopyable>("IvComPyClient",bp::no_init)
        .def("sendClientRequest",&IvComPyClient::sendClientRequest)
        .def("setupCallback",&IvComPyClient::setupCallback)
        .def("sendClientRequestDict",&IvComPyClient::sendClientRequestDict)
        .add_property("requestName",&IvComPyClient::requestName)
        .add_property("status",&IvComPyClient::status)
        
    ;
    // dss
    bp::class_<IvComPyDssClient,boost::noncopyable>("IvComPyDssClient",bp::no_init)
        .def("setupCallback",&IvComPyDssClient::setupCallback)
        .add_property("status",&IvComPyDssClient::status)
        .add_property("dssName", &IvComPyDssClient::dssName)
    ;

    // serverDatastreamClient
    bp::class_<IvComPySvrClient,boost::noncopyable>("IvComPySvrDSClient",bp::no_init)
        .def("setupCallback",&IvComPySvrClient::setupCallback)
        .def("enqueue",&IvComPySvrClient::enqueue)
        .add_property("status",&IvComPySvrClient::status)
        .add_property("datastreamName",&IvComPySvrClient::datastreamName)
        
    ;

	//serverRequest
	bp::class_<IvComPyServer, boost::noncopyable>("IvComPyServer", bp::no_init)
		// there's just one callback slot, which is invoked at every request.
		.def("setupCallback", &IvComPyServer::setupCallback)
		.def("serverName", &IvComPyServer::serverName)
	;

    bp::class_<IvComPyImgLiveClient, boost::noncopyable>("IvComPyImgLiveClient", bp::no_init)
        .def("clientName", &IvComPyImgLiveClient::clientName)
        .def("requestViewCreation", &IvComPyImgLiveClient::requestViewCreation)
        .def("requestViewCancel", &IvComPyImgLiveClient::requestViewCancel)
        .def("requestViewUpdate", &IvComPyImgLiveClient::requestViewUpdate)
        .def("registerCallbacks", &IvComPyImgLiveClient::registerCallbacks)
        .add_property("status",&IvComPyImgLiveClient::status)
    ;

    // deliverySstatus
    // IvComServerDatastreamCallback::DeliveryStatus
    bp::enum_<IvComServerDatastreamCallback::DeliveryStatus>("DeliveryStatus")
        .value("Invalid",IvComServerDatastreamCallback::Invalid)
        .value("InFlight",IvComServerDatastreamCallback::InFlight)
        .value("Processed",IvComServerDatastreamCallback::Processed)
        .value("MaybeDelivered",IvComServerDatastreamCallback::MaybeDelivered)
        .value("NeverDelivered",IvComServerDatastreamCallback::NeverDelivered)
        ;
}


