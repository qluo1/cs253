#ifndef MYIVCOMPYMANAGER_H
#define MYIVCOMPYMANAGER_H

#include "IvComApi.hpp"
#include <string>
#include <boost/python.hpp>
#include "IvComPyClient.h"
#include "IvComPyDssClient.h"
#include "IvComPySvrClient.h"
#include "IvComPyServer.h"
#include "IvComPyImgLiveClient.h"

#include <map>

using namespace std;

class IvComPyManager
{

    public:
        IvComPyManager():manager_(new IvComManager()){};
        ~IvComPyManager() {
            delete manager_;
        }

        bool setuplog(const string& cfgpath, const string& name,
                        const string& workdir); 

        // configure with python file
        bool init(const string& pycfgpath);
        // configure with json string
        bool initJson(const string& jsoncfg);

        bool run();

        bool stop();

        // helpers
        IvComManager* manager() { return manager_; };

        const IvComCatalogManager* catalogManager();
        const IvComConfigurationManager* configManager();
        // rf request
        IvComClientRequestManager* clientReqManager();
        // datastream request
        IvComServerDatastreamManager* serverDataStreamManager();
        //
        // rf clients
        IvComPyClient* getClientRequest(const string& name);
        vector<string> getClientRequestNames();
        // dss clients
        IvComPyDssClient* getDss(const string& name);
        vector<string> getDssNames();
        // serverDatastreamClient
        IvComPySvrClient* getServerDatastreamClient(const string& name);
        vector<string> getServerDatastreamClientNames();

		// request servers
		IvComPyServer* getRequestServer(const string& name);
		vector<string> getRequestServerNames();

        // imglive clients
        IvComPyImgLiveClient* getImageLiveClient(const string& name);
        vector<string> getImageLiveClientNames();

    private:
        bool config_internal();
        //typedef boost::scoped_ptr<IvComManager> IvComManagerPtr;
        IvComManager* manager_;

        //IvComClientRequest maps
        typedef map<string,boost::shared_ptr<IvComPyClient> > map_rf;
        map_rf request_clients_;
        
        //IvComDssRequest maps
        typedef map<string,boost::shared_ptr<IvComPyDssClient> > map_dss;
        map_dss dss_clients_;

        //IvComServerDatastream maps
        typedef map<string,boost::shared_ptr<IvComPySvrClient> > map_datastreamServer;
        map_datastreamServer datastream_servers_;
 
 		//IvComServerRequest maps
		typedef map<string, boost::shared_ptr<IvComPyServer> > map_requestServer;
		map_requestServer request_servers_;

        //ImgLive client
		typedef map<string, boost::shared_ptr<IvComPyImgLiveClient> > map_imglive_client;
        map_imglive_client imglive_clients_;
        
        IvComClientImageLiveManager* getClientImageLiveManager();


    // This grants that only this class has access to getClientImageLiveHandle, which this class needs to dispatch
    // a view creation request.
        friend class IvComPyImgLiveClient;
};

#endif
