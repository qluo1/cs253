#include <boost/python.hpp>
#include "GSLog.H"
#include <iostream>
#include "ReleaseGil.h"
#include "IvComPyManager.h"

#include <boost/foreach.hpp>
using namespace std;

bool IvComPyManager::setuplog(const string& cfgpath, const string& name,
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
}


bool IvComPyManager::config_internal()
{
	int amountOfInstances = 0;
    // parsing request-managres
    //
    try 
    {
        // rf
        do {
            IvComConfigurationMap* map = manager_->getConfigurationManager()->getConfiguration()->asMap();
            IvComConfigurationMap::iterator itr ,found;

            found = map->find("client-request-managers");
			if (found == map->end()) break;
			
            // iter through client-request-managers
            map = found->second->asMap();

            for (itr = map->begin();itr != map->end() ;itr++)
            {
                IvComClientRequesterHandle handle = manager_->getClientRequestManager()->getClientRequesterHandle(itr->first.c_str());
                if (!handle.isValid())
                {
                    ostringstream str;
                    str << "configuration error: request name " << itr->first << " not valid" << endl;
                    throw str.str();
                }

                //save     
                request_clients_[itr->first].reset(new IvComPyClient(*this,itr->first));

                IvComError error;
                error = manager_->getClientRequestManager()->startListeningForStatus(handle,request_clients_[itr->first].get());
                if (error != IvComError::None)
                    throw error.text();

                GSLOGFINFO << "client request [" << itr->first << "] started" <<endl;

            }

			amountOfInstances += map->size();
        }while(0);

        // dss/client-datastream
        do {
            IvComConfigurationMap* map = manager_->getConfigurationManager()->getConfiguration()->asMap();
            IvComConfigurationMap::iterator itr ,found;

            found = map->find("client-datastreams");
			if (found == map->end()) break;

            map = found->second->asMap();

            for (itr = map->begin();itr !=map->end();itr++)
            {
                IvComClientDatastreamHandle handle;
                handle = manager_->getClientDatastreamManager()->getClientDatastreamHandle(itr->first.c_str());
                if(!handle.isValid())
                {
                    ostringstream str;
                    str << "configuraiton error: " << itr->first << " not valid" << endl;
                    throw str.str();
                }
				
                //save dss session
                dss_clients_[itr->first].reset(new IvComPyDssClient(*this,itr->first));

                IvComError error;
                error = manager_->getClientDatastreamManager()->start(handle,dss_clients_[itr->first].get());
                if (error != IvComError::None)
                    throw error.text();

                error = manager_->getClientDatastreamManager()->startListeningForStatus(handle,dss_clients_[itr->first].get());
                if (error != IvComError::None)
                    throw error.text();

                GSLOGFINFO << "client datastream [" << itr->first << "] started" <<endl;
			}

			amountOfInstances += map->size();
        }while(0);

        // server-datastream
        do {
            IvComConfigurationMap* map = manager_->getConfigurationManager()->getConfiguration()->asMap();
            IvComConfigurationMap::iterator itr ,found;
            found = map->find("server-datastreams");
			
            // server datastream is optional
            if (found != map->end())
            {
                map = found->second->asMap();
                for (itr = map->begin();itr !=map->end();itr++)
                {
                    //cout << itr->first <<endl;
                    IvComServerDatastreamHandle handle;
                    handle = manager_->getServerDatastreamManager()->getServerDatastreamHandle(itr->first.c_str());
                    if(!handle.isValid())
                    {
                        ostringstream str;
                        str << "configuraiton error: " << itr->first << " not valid" << endl;
                        throw str.str();
                    }

                    //save dss session
                    datastream_servers_[itr->first].reset(new IvComPySvrClient(*this,itr->first));

                    IvComError error;
                    error = manager_->getServerDatastreamManager()->start(handle,datastream_servers_[itr->first].get());
                    if (error != IvComError::None)
                        throw error.text();

                    error = manager_->getServerDatastreamManager()->startListeningForStatus(handle,datastream_servers_[itr->first].get());
                    if (error != IvComError::None)
                        throw error.text();

                    GSLOGFINFO << "server datastream [" << itr->first << "] started" <<endl;
                }

				amountOfInstances += map->size();
            }
		} while(0);

		// server-request
		do {	// just to isolate variables' scope
			IvComConfigurationMap* map = manager_->getConfigurationManager()
				->getConfiguration()->asMap();

			// transversing the configuration file seeking for the request servers list
			IvComConfigurationMap::iterator itr, found;
			found = map->find("server-request-managers");

			if (found != map->end()) {
				map = found->second->asMap();

				// iterating over all request server instances
				for (itr = map->begin(); itr != map->end(); itr++) {
					IvComServerRequesterHandle handle;

					handle = manager_->getServerRequestManager()->
						getServerRequesterHandle(itr->first.c_str());

					if (!handle.isValid()) {
						ostringstream str;
						str << "Configuration error: " << itr->first << " is not valid.\n";
						throw str.str();
					}
						
					// saving internal handler on local map to be exposed to Python layer
					request_servers_[itr->first].reset(new IvComPyServer(*this, itr->first));

					IvComError error;
					error = manager_->getServerRequestManager()->
						start(handle, request_servers_[itr->first].get());
					if (error != IvComError::None)
						throw error.text();

					error = manager_->getServerRequestManager()->
						startListeningForStatus(handle, request_servers_[itr->first].get());
					if (error != IvComError::None)
						throw error.text();

					GSLOGFINFO << "Request server [" << itr->first << "] started.\n";
				}

				amountOfInstances += map->size();
			}
		} while(0);

        //imgLive client
        do {
            IvComConfigurationMap* map = manager_->getConfigurationManager()->getConfiguration()->asMap();

            IvComConfigurationMap::iterator itr, found;
            found = map->find("image-live-clients");

            if (found != map->end()) {
                map = found->second->asMap();

                for (itr = map->begin(); itr != map->end(); itr++) {
                    IvComClientImageLiveHandle handle;

                    handle = manager_->getClientImageLiveManager()->getClientImageLiveHandle(itr->first.c_str(), false);
                    if (!handle.isValid()) {
                        ostringstream str;
                        str << "Configuration error: " << itr->first << " is not valid.\n";
                        throw str.str();
                    }

                    //registering a C++ to listen to events. This class will expose some methods to the py layer
                    IvComClientImageLiveManager *imgCliManager = manager_->getClientImageLiveManager();
                    IvComPyImgLiveClient* newCli =  new IvComPyImgLiveClient(*this, imgCliManager, itr->first);
                    imglive_clients_[itr->first].reset(newCli);

                    IvComClientImageLiveManager* clientManager = manager_->getClientImageLiveManager();
                    IvComError error;

                    error = clientManager->startListeningForStatus(handle, imglive_clients_[itr->first].get());
                    if (error != IvComError::None)
                        throw error.text();

                    error = clientManager->start(handle, imglive_clients_[itr->first].get());
                    if (error != IvComError::None)
                        throw error.text();

					GSLOGFINFO << "ImageLive client " << itr->first << "] started.\n";
                }
                amountOfInstances += map->size();
            }
        } while(0);
    } 
	catch (const char* error) {
        GSLOGFASTFSEVERE << error << endl;
        return false;
    }

	if (amountOfInstances == 0) {
		GSLOGFSEVERE << "No instance present on configuration file." << endl;
		return false;
	}

    GSLOGFINFO << "setup ivcom configuration ok!" <<endl;
    return true;
}


bool IvComPyManager::initJson(const string& jsoncfg)
{

    string pythonWrappedData = "def configure():\n return ";
    pythonWrappedData += jsoncfg;
    IvComError error = manager_->configurePythonString(pythonWrappedData.c_str());
    if (error != IvComError::None)
    {
        GSLOGFSEVERE << "could not configure manager :" << error.text() <<endl;
        return false;
    }
    return  config_internal();

}

bool IvComPyManager::init(const string& pycfgpath)
{
    IvComError error = manager_->configure(pycfgpath.c_str());
    if (error != IvComError::None)
    {
        GSLOGFSEVERE << "could not configure manager :" << error.text() <<endl;
        return false;
    }
    return  config_internal();

}

IvComPyClient* IvComPyManager::getClientRequest(const string& name)
{
    map_rf::iterator itr = request_clients_.find(name);
    if(itr != request_clients_.end())
    {
        return itr->second.get();
    }
    GSLOGFSEVERE << "not found for request-manager name:" << name <<endl;
    return 0;
}

vector<string> IvComPyManager::getClientRequestNames()
{
    vector<string> ret;

    map_rf::iterator itr = request_clients_.begin(), 
                    end = request_clients_.end();
    for(;itr != end;++itr)
    {
        ret.push_back(itr->first);
    }
    return ret;
}

IvComPyDssClient* IvComPyManager::getDss(const string& name)
{
    map_dss::iterator itr = dss_clients_.find(name);
    if(itr != dss_clients_.end())
    {
        return itr->second.get();
    }
    GSLOGFSEVERE << "not found for dss name:" << name <<endl;
    return 0;
}

vector<string> IvComPyManager::getDssNames()
{
    vector<string> ret;

    map_dss::iterator itr = dss_clients_.begin(), 
                    end = dss_clients_.end();
    for(;itr != end;++itr)
    {
        ret.push_back(itr->first);
    }
    return ret;
}

// serverDatastream clients
vector<string> IvComPyManager::getServerDatastreamClientNames()
{
    vector<string> ret;

    map_datastreamServer::iterator itr = datastream_servers_.begin(), 
                    end = datastream_servers_.end();
    for(;itr != end;++itr)
    {
        ret.push_back(itr->first);
    }
    return ret;
}



IvComPySvrClient* IvComPyManager::getServerDatastreamClient(const string& name)
{
    map_datastreamServer::iterator itr = datastream_servers_.find(name);
    if(itr != datastream_servers_.end())
    {
        return itr->second.get();
    }
    GSLOGFSEVERE << "not found for serverDatastream name:" << name <<endl;
    return 0;
}

// Request servers
vector<string> IvComPyManager::getRequestServerNames() {
	vector<string> ret;
	map_requestServer::iterator itr = request_servers_.begin();
	map_requestServer::iterator end = request_servers_.end();

	for (; itr != end; itr++)
		ret.push_back(itr->first);

	return ret;
}

// ImageLive clients
vector<string> IvComPyManager::getImageLiveClientNames() {
	vector<string> ret;
	map_imglive_client::iterator itr = imglive_clients_.begin();
	map_imglive_client::iterator end = imglive_clients_.end();

	for (; itr != end; itr++)
		ret.push_back(itr->first);

	return ret;
}

IvComPyServer* IvComPyManager::getRequestServer(const string& name) {
	map_requestServer::iterator itr =  request_servers_.find(name);
	if (itr != request_servers_.end())
		return itr->second.get();
	
	// if not found
	GSLOGFSEVERE << "Request client " << name << " not found.\n";
	return 0;
}

IvComPyImgLiveClient* IvComPyManager::getImageLiveClient(const string& name) {
    map_imglive_client::iterator itr =  imglive_clients_.find(name);
    if (itr != imglive_clients_.end())
        return itr->second.get();

	GSLOGFSEVERE << "Request client " << name << " not found.\n";
    return 0;
}

// kick off IvCom event loop
//
bool IvComPyManager::run()
{
    ReleaseGil unlock;

    IvComError error = manager_->run();

    if (error != IvComError::None)
    {
        GSLOGFSEVERE << "manager exited with error: " << error.text() << endl;
        return false;
    }
    GSLOGFINFO << "manager exited normally" << endl;
    return true;
}

bool IvComPyManager::stop()
{
    //ReleaseGil unlock;

    IvComError error = manager_->stopRunning();
    if (error !=IvComError::None)
    {
        GSLOGFSEVERE <<"manager stopping failed with error: " << error.text() <<endl;
        return false;
    }
    GSLOGFINFO << "manager stopping ok" <<endl;
    return true;

}
// helper
//
 const IvComCatalogManager* IvComPyManager::catalogManager()
{
    return manager_->getCatalogManager();
}

const IvComConfigurationManager* IvComPyManager::configManager()
{
    return manager_->getConfigurationManager();
}
IvComClientRequestManager* IvComPyManager::clientReqManager()
{
    return manager_->getClientRequestManager();
}

IvComServerDatastreamManager* IvComPyManager::serverDataStreamManager()
{
    return manager_->getServerDatastreamManager();
}

IvComClientImageLiveManager* IvComPyManager::getClientImageLiveManager(){
    return manager_->getClientImageLiveManager();
}

