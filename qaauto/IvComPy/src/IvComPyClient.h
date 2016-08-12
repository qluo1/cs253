#ifndef IVCOMPYCLIENT_H
#define IVCOMPYCLIENT_H
#include <Python.h>
#include "IvComApi.hpp"
#include "IvComClientRequestManager.hpp"
#include <boost/python.hpp>
#include <string>

// forward 
class IvComPyManager;

using namespace std;
namespace bp = boost::python;

class IvComPyClient: public IvComClientRequestCallback, public IvComClientRequestStatusCallback
{
public:
    // ctor - initialise client-request-managers
    IvComPyClient(IvComPyManager& manager,string& name);
    // copy ctor

    virtual ~IvComPyClient() { };

    /*
     * send request 
     * */
    bool sendClientRequest(const string& table,const string& json);
    
    bool sendClientRequestDict(const string& table, bp::dict in);


    void setupCallback(const string& name,PyObject* callback)
    {
        callback_ = make_pair(name,callback);
    };
    const char* status() { return status_.text(); };

    const char* requestName(){ return name_.c_str(); };

private:
    // inherited from IvComClientRequestCallback
    void onResponse(IvComClientRequestCallback::Data& data);
    void onTimeout(IvComClientRequestCallback::TimeoutData& data);
    // inherited 
    void onStatus(IvComClientRequestStatusCallback::Data& data);

    IvComPyManager& manager_;

    // current status
    IvComClientRequestStatus status_;
    //reqeust-manager name
    string name_;
    // C*ALLBACK
    pair<string,PyObject*> callback_;
    
};

#endif
