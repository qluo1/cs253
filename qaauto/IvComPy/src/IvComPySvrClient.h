#ifndef IVCOMPYSVRCLIENT_H
#define IVCOMPYSVRCLIENT_H

#include <Python.h>
#include "IvComApi.hpp"
#include <boost/python.hpp>
#include <string>

using namespace std;

namespace bp = boost::python;

// forward 
class IvComPyManager;

class IvComPySvrClient: public IvComServerDatastreamCallback, public IvComServerDatastreamStatusCallback
{
public:
    // ctor - initialise client-request-managers
    IvComPySvrClient(IvComPyManager& manager,const string& name);
    // dtor
    virtual ~IvComPySvrClient() { };

    const char* datastreamName(){ return name_.c_str(); };

    const char* status() { return status_.text();};

    bool enqueue(const string& table, int  messageId, bp::dict msg, bool posDup);

    // for ack callback
    void setupCallback(const string& name,PyObject* callback)
    {
        callback_ = make_pair(name,callback);
    };
    
private:
    /**
     * Inherited from IvComServerDatastreamCallback
     */
    void onRequestData(RequestData& data);

    void onProcessed(Acknowledgement& data);

    // this function is called whenever the server receives a request for a stream of initialization messages from a client
    void onRequestInitialization(RequestInitialization& data);

    void onRequestAvailability(RequestAvailability& data);

    /**
     * inherited from IvComServerDatastreamStatusCallback
     */
    void onStatus(IvComServerDatastreamStatusCallback::Data& data);

    // internal attrs
    IvComPyManager& manager_;
    // current status
    IvComServerDatastreamStatus status_;
    //datastream name
    string name_;
    // C*ALLBACK
    pair<string,PyObject*> callback_;

};
#endif
