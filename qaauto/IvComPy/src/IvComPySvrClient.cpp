#include <boost/python.hpp>
#include "GSLog.H"
#include "IvComPySvrClient.h"
#include "IvComPyManager.h"
#include "IvComPyDict.h"
#include "ReleaseGil.h"

// ctor - initialise client-request-managers
IvComPySvrClient::IvComPySvrClient(IvComPyManager& manager,const string& name):
    manager_(manager),name_(name)
{
}

/**
 * inherited from IvComServerDatastreamStatusCallback
 */
void IvComPySvrClient::onRequestData(RequestData& data)
{
    GSLOGFASTFINFO << "onRequestData callled" << endl;
}

/** This routine is called when clients connect. The availability number provided is used by the client to determine
 * which among several possible servers will be used, where the first server with the lowest load is
 * chosen.
 *
 * 100 is used as the 'base' load value.
 *
 * This function will not be called if 'auto-indicate-availability-load' is set in the datastream server's configuration
 */

void IvComPySvrClient::onRequestAvailability(RequestAvailability& data)
{
    GSLOGFASTFINFO << "onRequestAvailability callled [" << data.datastreamName() << "] messageId: " << data.messageId() << endl;
    IvComError res;
    res = data.indicateAvailability(100);
    if (res != IvComError::None)
    {
        GSLOGFASTFSEVERE << "onRequestAvailability indicate available failed! [ " << res.text() <<endl;
    }
}


void IvComPySvrClient::onRequestInitialization(RequestInitialization& data)
{
    GSLOGFASTFINFO << "onRequestInitialization callled [" << data.datastreamName() << "] previousMessageId: " << data.previousMessageId() << endl;
    IvComError error;

    if((error=data.initializationComplete())!= IvComError::None)
    {
        GSLOGFASTFSEVERE << "[" << data.datastreamName() << "]" << "error sending initialization complete [ " << error.text() << "]" <<endl;
    }else
    {
        GSLOGFASTFINFO << "[" << data.datastreamName() << "] send initialization complete " <<endl;
    }
    
}


void IvComPySvrClient::onProcessed(Acknowledgement& data)
{
    GSLOGFINFO << "onProcessed callled for [" << data.datastreamName() << "] messageId [" << data.messageId() << "]" << data.deliveryStatus()  << endl;

    if (callback_.second)
    {
        GSLOGFINFO << "Ensure GIL state" <<endl;
        AquireGil lock;
        bp::dict ret;
        ret["messageId"] = data.messageId();
        ret["datastream"] = data.datastreamName();
        ret["deliveryStatus"] = data.deliveryStatus();
        ret["group"] = data.group();

        GSLOGFDEBUG << "callback to python for acked message" <<endl;
        // Python callback
        bp::call_method<void>(callback_.second,callback_.first.c_str(),ret);

        GSLOGFDEBUG << " finished callback" <<endl;

   }else{

       GSLOGFSEVERE << "NO pyton callback registered" <<endl;
   }

    
}


void IvComPySvrClient::onStatus(IvComServerDatastreamStatusCallback::Data& data)
{
    GSLOGFASTFINFO << "[" << data.datastreamName() << "] received status callback for [" << data.status() << "]"<< endl;

    status_ = data.status();
}

// publish 
bool IvComPySvrClient::enqueue(const string& table,int messageId, bp::dict msg,bool posDup)
{
    GSLOGFDEBUG << "enqueue message for table [ " << table << "]  messageId [ " << messageId <<endl;
    
    // convert income message to 
    IvComCatalogManager* pCatMgr = manager_.manager()->getCatalogManager();
    IvComTable ivTable = pCatMgr->getTable(table.c_str());
    if (!ivTable.isValid())
    {
        GSLOGFASTFSEVERE << "specified table name [" << table << "] isn't valid" <<endl;
        return false;
    }
    //
    IvComMessage ivmsg(ivTable);

    if(!IvComPyDictDecoder::pyDictToIvCom(pCatMgr,msg,ivmsg))
    {
        GSLOGFASTFSEVERE << "pydict convert to ivcom failed " <<endl;
        return false;
    }
    GSLOGFDEBUG << "converted to ivcom: " << ivmsg <<endl;


    IvComError res;
    stringstream ss;
    ss << messageId;

    // release gil here before acquire ivcom handle
    ReleaseGil gil;
    // workout handle, acquire handle will raise lock, apply after python call
    IvComServerDatastreamManager* pDSManager = manager_.manager()->getServerDatastreamManager();

    IvComServerDatastreamHandle handle = pDSManager->getServerDatastreamHandle(datastreamName());

    if (!handle.isValid())
    {
        GSLOGFASTFSEVERE <<  "server datastream handle isn't valid for [" << datastreamName() << "]" <<endl;
        return false;
    }

    // enqueue message
    if (posDup == true)
    {
        res = pDSManager->enqueue(handle,ss.str().c_str(),ivmsg,IvComPosDup::PosDup);
    }else
    {
        res = pDSManager->enqueue(handle,ss.str().c_str(),ivmsg,IvComPosDup::NotPosDup);
    }

    if (res != IvComError::None)
    {
        GSLOGFASTFSEVERE << "enqueue message failed [" << res.text() << "]" <<endl;
        return false;
    }

    return true;
}
