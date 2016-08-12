#include <boost/python.hpp>
#include "GSLog.H"
#include "IvComJsonDecoder.hpp"
#include "IvComJsonEncoder.hpp"
#include <sstream>
#include <map>
#include "IvComPyDssClient.h"
#include "ReleaseGil.h"
#include <boost/assert.hpp>

//#include <json/json.h>
//#include <GsCuBase64Encoder.hpp>
#include "IvComPyManager.h"

#include "IvComPyDict.h"

using namespace std;
namespace bp = boost::python;



IvComPyDssClient::IvComPyDssClient(IvComPyManager& manager, const string& name):
    manager_(manager),name_(name),callback_(),lastMessageId_("0")
{

}

// inherited from IvComClientDatastreamCallback
const char* IvComPyDssClient::onRequestLastProcessedMessageId(const char* messageId)
{
    return lastMessageId_.c_str();
}

// inherited from IvComClientDatastreamCallback
void IvComPyDssClient::onMessage(IvComClientDatastreamCallback::Data& data)
{
    GSLOGFINFO << "received onMessage: "  << data.datastreamName() << "msgId: " <<  data.messageId() \
        << "posDup: " << data.posDup() << endl;
    const IvComMessage& ivmsg = data.message();
    string table(ivmsg.table().tableName()), json;
    string msgId(data.messageId());
    bool posDup;
    posDup = !(data.posDup() == IvComPosDup::NotPosDup);
    GSLOGFINFO << " msgType: " << table <<endl;

// TO BE removed, not using json anymore
//
//    IvComJsonEncoder encoder = IvComJsonEncoder();
//    // handle routed message
//    if (ivmsg.table().tableId() == 54)
//    {
//        IvComTable tbl = ivmsg.table();
//        IvComColumn col_tabId = tbl.getColumn("tableId");
//        int tableId;
//        ivmsg.get(col_tabId,tableId);
//
//        GSLOGFDEBUG <<"tableId: " << tableId <<endl;
//
//        IvComColumn col_data = tbl.getColumn("messageData");
//        const unsigned char* data = NULL;
//        unsigned int size;
//
//        if (ivmsg.get(col_data,data,size))
//        {
//                IvComCatalogManager* pCat = const_cast<IvComCatalogManager*>(this->manager_.catalogManager());
//                IvComMessage msg(tableId,pCat,data,size);
//                GSLOGFDEBUG << "misformatted:" << msg.isMisformatted() << endl;
//                GSLOGFDEBUG << "messageData, as table" << msg <<endl;
//
//                // ivcom to json
//                if(!encoder.serializeAsJson(msg,json))
//                {
//                    GSLOGFSEVERE << "IvCom to Json encode failed for routed msg: " << msg <<endl;
//                    return;
//                }
//                // set table name for the message
//                table = msg.table().tableName();
//                
//        }else
//        {
//            GSLOGFSEVERE << "parse RoutedMessage for messageData failed" << ivmsg <<endl;
//            return;
//        }
//
//    }else
//    {
//        // all other message i.e. DSS OrderExecutionUpdate
//        if(!encoder.serializeAsJson(ivmsg,json))
//        {
//            GSLOGFSEVERE << "IvCom to Json encode failed for msg: " << ivmsg <<endl;
//            return;
//        }
//
//    }
//    GSLOGFDEBUG << "successful encoded json: " << json <<"table: " << table << " from ivcom: " << ivmsg <<endl;
//
//        //null root
//        Json::Value root;
//        Json::Reader reader = Json::Reader();
//
//        if (reader.parse(json,root))
//        {
//            GSLOGFINFO << "reader parse ok" <<endl;
//            try {
//
//                if (root.isMember("currentOrder"))
//                {
//                    Json::Value currOrder = root["currentOrder"];
//                    GSLOGFINFO << " got current order " <<endl;
//                }
//
//                // process routed message here
//                if (root.isMember("messageData") && root.isMember("tableId"))
//                {
//                    // 
//                    Json::Value commandHeader = root["commandHeader"];
//                    GSLOGFINFO << root["messageData"].asString() <<endl;
//                    GSLOGFINFO << root["tableId"].asInt() <<endl;
//                    GSLOGFINFO << GsCuBase64Encoder::decode(root["messageData"].asString()) <<endl;
//                    // convert
//                    std::string msgData = GsCuBase64Encoder::decode(root["messageData"].asString());
//                    GSLOGFINFO << "msgData length: " << msgData.length() <<endl;
//
//                    IvComCatalogManager* pCat = const_cast<IvComCatalogManager*>(this->manager_.catalogManager());
//                    IvComMessage msg(root["tableId"].asInt(),pCat,(unsigned char*)msgData.c_str(),msgData.length());
//
//                    GSLOGFINFO << "misformatted:" << msg.isMisformatted() << endl;
//                    GSLOGFINFO << "messageData, as table" << msg <<endl;
//                }
//
//
//
//            }catch(const std::exception& ex)
//            {
//                GSLOGFSEVERE << "error" << ex.what() << endl;
//
//            }catch (...)
//            {
//                GSLOGFSEVERE << "root.get failed";
//            }
//         }
//

    if (callback_.second)
    {
        AquireGil lock;
        // convert ivcom to pydict.
        //
        bp::dict out;

        if (! IvComPyDictDecoder::ivComToPyDict(ivmsg,out))
        {
            GSLOGFSEVERE << "convert to pydict failed " << endl;
        }

        //GSLOGFDEBUG << "callback to python onMessage:" << json  <<endl;
        // Python callback
        bp::call_method<void>(callback_.second,callback_.first.c_str(),table,out,msgId,posDup);

        GSLOGFDEBUG << " finished callback" <<endl;

    }else{

       GSLOGFSEVERE << "NO pyton callback registered" <<endl;
       GSLOGFINFO << ivmsg <<endl;
    }

    // have to ack on all processed message 
    IvComError error = data.acknowledgeProcessed();
    if (error != IvComError::None)
    {
        GSLOGFSEVERE << "dss acknowledgeProcessed failed: " << error.text() <<endl;
    }

    // remember last messageId
    lastMessageId_ = msgId;

}

/**
 * Inherited from IvComClientDatastreamCallback
 *
 * This is called once the final initialization message has been received. At this
 * point the client should be completely up to date, and further messages will
 * be sent in real time.
 */
void IvComPyDssClient::onInitializationComplete(InitializationCompleteData& data)
{
    GSLOGFINFO << "dssClient received onInitializationComplete: " << data.datastreamName() << endl;


}

/**
 * inherited from IvComClientDatastreamStatusCallback
 */
void IvComPyDssClient::onStatus(IvComClientDatastreamStatusCallback::Data& data)
{
    GSLOGFINFO << data.datastreamName() << " received onStatus: " << data.status() <<endl;

    status_ = data.status();

}

