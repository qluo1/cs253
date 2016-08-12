#include <boost/python.hpp>
#include "GSLog.H"
//ivcom to json
#include "IvComJsonDecoder.hpp"
#include "IvComJsonEncoder.hpp"
// ivcom to pydict
#include "IvComPyDict.h"
#include <sstream>
#include <map>
#include "IvComPyClient.h"
#include "IvComPyManager.h"
#include "ReleaseGil.h"
#include <boost/assert.hpp>


using namespace std;
namespace bp = boost::python;

// ctor - initialise client-request-managers
IvComPyClient::IvComPyClient(IvComPyManager& manager,string&name):
    manager_(manager),name_(name),callback_()
{  
    status_ = IvComClientRequestStatus::Invalid;    
    BOOST_ASSERT(name_.size() > 0);
};

/*
 * send request 
 * */
bool IvComPyClient::sendClientRequest(const string& table,const string& json)
{
    GSLOGFDEBUG << "ReleaseGil" <<endl;
    ReleaseGil unlock;
    // 
    GSLOGFINFO << "sendClientRequest: " << table << ", msg: " << json <<endl;

    if (status_ != IvComClientRequestStatus::Available)
    {
        GSLOGFASTFSEVERE << name_ << " not in available status " << status_ << endl;
        return false;
    }
    IvComTable t = manager_.catalogManager()->getTable(table.c_str());
    if(!t.isValid())
    {
        GSLOGFASTFSEVERE << "Invalid table name: " << table <<endl;
        return false;
    }
    IvComMessage ivmsg = IvComMessage(t);

    IvComJsonDecoder decoder = IvComJsonDecoder();
    if(!decoder.deserializeFromJson(json,manager_.catalogManager(),ivmsg))
    {
        GSLOGFASTFSEVERE << "convert from json to IvComManager failed" <<endl;
        return false;
    }
   
    ivmsg.takeOwnership();
    GSLOGFINFO << " IVMSG: " << ivmsg <<endl;


    // aquire lock
    IvComClientRequesterHandle handle = manager_.clientReqManager()->getClientRequesterHandle(name_.c_str());
    if (!handle.isValid())
    {
        ostringstream str;
        str << "configuration error: request name " << name_ << " not valid" << endl;
        GSLOGFSEVERE << str;
        return false;
    }

    IvComError error;
    error = manager_.clientReqManager()->sendRequest(handle,ivmsg,
                                                    IvComClientRequestManager::Queueable,
                                                    IvComPosDup::PosDup,this);
    if (error != IvComError::None)
    {
         GSLOGFASTFSEVERE << "[" << name_ << "] could not send request [" << error.text() << ']' << endl;
         return false;
    }

    return true;
};

/*
 * send request as python dict object, called from python thread, GILL should already exist
 * */
bool IvComPyClient::sendClientRequestDict(const string& table,bp::dict in)
{
    // 
    GSLOGFINFO << "sendClientRequest dict: " << table <<endl;

    if (status_ != IvComClientRequestStatus::Available)
    {
        GSLOGFASTFSEVERE << name_ << " not in available status " << status_ << endl;
        return false;
    }
    IvComTable t = manager_.catalogManager()->getTable(table.c_str());
    if(!t.isValid())
    {
        GSLOGFASTFSEVERE << "Invalid table name: " << table <<endl;
        return false;
    }
    IvComMessage ivmsg = IvComMessage(t);

    if(!IvComPyDictDecoder::pyDictToIvCom(manager_.catalogManager(),in, ivmsg))
    {
        GSLOGFASTFSEVERE << "convert from pydict to IvComMessage failed" <<endl;
        return false;
    }
    GSLOGFDEBUG << "request IVMSG: " << ivmsg <<endl;

    // release GIL block after all python API access.
    GSLOGFDEBUG << "ReleaseGil" <<endl;
    ReleaseGil unlock;
    // mutex lock here, fix deadlock, after release GIL
    GSLOGFDEBUG << " getClientRequesterHandle" <<endl;
    IvComClientRequesterHandle handle = manager_.clientReqManager()->getClientRequesterHandle(name_.c_str());
    if (!handle.isValid())
    {
        ostringstream str;
        str << "configuration error: request name " << name_ << " not valid" << endl;
        GSLOGFSEVERE << str;
        return false;
    }

    IvComError error;
    error = manager_.clientReqManager()->sendRequest(handle,ivmsg,
                                                    IvComClientRequestManager::Queueable,
                                                    IvComPosDup::PosDup,this);
    if (error != IvComError::None)
    {
         GSLOGFASTFSEVERE << "[" << name_ << "] could not send request [" << error.text() << ']' << endl;
         return false;
    }

    return true;
}


void IvComPyClient::onStatus(IvComClientRequestStatusCallback::Data& status)
{
    GSLOGFINFO << "onStatus called:" << status.status() << "name: "<< status.requestManagerName()  <<endl;

    BOOST_ASSERT (name_.compare(status.requestManagerName()) ==0);
    // update client_requests
    status_ = status.status();

}

void IvComPyClient::onTimeout(IvComClientRequestCallback::TimeoutData& data)
{
    GSLOGFINFO << "onTimeout called:" << data.status() << endl;
}

void IvComPyClient::onResponse(IvComClientRequestCallback::Data& data)
{
    GSLOGFINFO << "onResponse called from: " << data.requestManagerName() <<endl;

    const IvComMessage& ivmsg = data.response();
    GSLOGFDEBUG << ivmsg << endl;

    string table = ivmsg.table().tableName();
///  to be removed
//    string json;
//    IvComJsonEncoder encoder = IvComJsonEncoder();
//
//    if(!encoder.serializeAsJson(ivmsg,json))
//    {
//        GSLOGFSEVERE << "ivmsg encode json failed: "  << ivmsg << endl;
//        return;
//
    if (callback_.second)
    {
        GSLOGFDEBUG << "Ensure GIL. " <<endl;
        AquireGil lock;
        bp::dict out;
        if(!IvComPyDictDecoder::ivComToPyDict(ivmsg,out))
        {
            GSLOGFSEVERE << "ivmsg encode dict failed: "  << ivmsg << endl;
            return;
        }

        GSLOGFDEBUG << "callback to python onMessage" <<endl;
        // Python callback
        bp::call_method<void>(callback_.second,callback_.first.c_str(),table,out);

        GSLOGFDEBUG << " finished callback" <<endl;

   }else{

       GSLOGFSEVERE << "NO pyton callback registered" <<endl;
       GSLOGFINFO << ivmsg <<endl;
   }

}

