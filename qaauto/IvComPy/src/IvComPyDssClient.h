#ifndef IVCOMPYDSSCLIENT_H
#define IVCOMPYDSSCLIENT_H
#include <Python.h>
#include "IvComApi.hpp"
#include <boost/python.hpp>
#include <string>

// forward 
class IvComPyManager;

using namespace std;
namespace bp = boost::python;

class IvComPyDssClient: public IvComClientDatastreamCallback, public IvComClientDatastreamStatusCallback
{
public:
    // ctor - initialise client-request-managers
    IvComPyDssClient(IvComPyManager& manager,const string& name);
    // dtor
    virtual ~IvComPyDssClient() { };

    void setupCallback(const string& name ,PyObject* callback)
    {
        callback_ = make_pair(name,callback);
    }

    const char* dssName(){ return name_.c_str(); };
    const char* status() { return status_.text();};

private:
    // inherited from IvComClientDatastreamCallback
    const char* onRequestLastProcessedMessageId(const char* messageId);
    // inherited from IvComClientDatastreamCallback
    void onMessage(IvComClientDatastreamCallback::Data& data);

    /**
     * Inherited from IvComClientDatastreamCallback
     *
     * This is called once the final initialization message has been received. At this
     * point the client should be completely up to date, and further messages will
     * be sent in real time.
     */
    void onInitializationComplete(InitializationCompleteData& data);

    /**
     * inherited from IvComClientDatastreamStatusCallback
     */
    void onStatus(IvComClientDatastreamStatusCallback::Data& data);

    IvComPyManager& manager_;

    // current status
    IvComClientDatastreamStatus status_;
    //dss name
    string name_;
    // C*ALLBACK
    pair<string,PyObject*> callback_;
    
    string lastMessageId_ ;
};

#endif
