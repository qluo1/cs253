#include "OmaClientCB.hpp"
#include "GSLog.H"
#include "ReleaseGil.h"

#include <OmaNVPNames.H>
#include <OmaClientCommon.H>	    	// for the failure defines 
#include <OmaClientConnection.H>	    // for the connection 
#include <OmaClientConnectionReceiver.H>	// for the connection callbacks
#include <OmaClientViewCB.H>		    // for the view callbacks
#include <OmaSubNVPSeq.H>			    // internalize for OmaOrderData needs this
#include <OmaOrderDataFactory.H>	    // for create_order_data 
#include <OmaOrderData.H>			    // we are internalizing into an orderdata
#include <OmaNVPSequence.H>
#include <sstream>
#include <rw/typedefs.h>
#include <iostream>

using namespace std;
namespace bp = boost::python;


// helper method to print out operation type
const char* op_type_to_string(const OmaOperationType& opType)
{
    switch (opType) {
        case OmaInsert  :       return "OmaInsert";
        case OmaInvalid :       return "OmaInvalid";
        case OmaUpdate  :       return "OmaUpdate"; 
        case OmaRemove  :       return "OmaRemove"; 
        case OmaQuery   :       return "OmaQuery"; 
        case OmaNoTranType:     return "NoTranType"; 
        case OmaFeedStatusUpdate: return "OmaFeedStatusUpdate";
        default:
            return "Unknown";
    }
}


bool 
OmaClientCB::process_oma_status_message(const OmaClientViewID& viewId,
                                          const RWCString& serverName,
                                          OmaTypes::ClientStatus status)
{
    GSLOGFINFO << "ClientViewCB::status_message from " << serverName
               << " for " << viewId << ": " 
               << OmaTypes::client_status_to_string(status) << endl;
    GSLOGFINFO << "om status message ok" << endl;
    return true;
}

bool 
OmaClientCB::process_oma_query_message(const OmaClientViewID& viewId,
                                            const RWCString& serverName,
                    const OmaNVPSequence& nvp)
{
    OmaOrderData *order = OmaOrderDataFactory::new_oma_order_data();
    order->internalize_from_nvp(OmaSubNVPSeq(nvp));

    GSLOGFINFO << "ClientViewCB::query_message from " << serverName
              << " for " << viewId
              << " : " << order->uniqueTag() << endl;

    delete order;
    return true;
}


bool 
OmaClientCB::process_message(const OmaClientViewID& viewId,
                         const RWCString& serverName,
                         const OmaOperationType& opType,
                         const OmaNVPSequence& nvp,
                         const char* name)
{
    GSLOGFINFO << "process_oma_message: [" << name << "]" << endl;
    GSLOGFINFO  << "process_oma_status_message: [" << viewId << "] name: [" << serverName << " ]"   <<endl;
    assert(conn_ != NULL);

    OmaOrderData *order = OmaOrderDataFactory::new_oma_order_data();
    order->internalize_from_nvp(OmaSubNVPSeq(nvp));

    GSLOGFINFO << "Received seq num for " << serverName  << " is " << conn_->lastMessageSeqNum( serverName ) << endl;
    if(holder_)
    {
        GSLOGFINFO << "Incrementing seq num for "<< serverName <<endl;
        holder_->incrementSeqNum(serverName);
    }

    GSLOGFINFO << "ClientViewCB::view_message from " << serverName
         << " for " << viewId
         << " : " << op_type_to_string(opType)
         << " " << order->uniqueTag() << endl;

    GSLOGFTRACE << "NVP is " << nvp << endl;

    if (callback_.second)
    {
        GSLOGFDEBUG << "Ensure GIL. " <<endl;
        AquireGil lock;
        boost::python::dict data;
        // Python callback
        std::string buffer(nvp.dump());
        std::string server_name(serverName);
        std::string view_id(viewId);
        std::string tag(order->uniqueTag());

        data["nvp"] = buffer.c_str();
        data["serverName"] =  server_name.c_str();
        data["viewId"] = view_id.c_str();
        data["opType"] = op_type_to_string(opType);
        data["tag"] = tag.c_str();
        data["method"] = name;

        bp::call_method<void>(callback_.second,callback_.first.c_str(),data);
        GSLOGFDEBUG << " finished callback" <<endl;

    } else {

        GSLOGFSEVERE << " no callback registered" <<endl;
    }

    delete order;
    return true;
}


// --------------- connection reset callback
//
void ConnResetCB::connected_to_ex( const char* serverName, const OmaTypes::ServerType serverType )
{
    // re-connected
     GSLOGFINFO << "ConnectionResetCB::connected_to: " 
                << serverName << "; ServerType= "
                << OmaTypes::server_type_to_string(serverType)<<endl;
}

void ConnResetCB::disconnected_from_ex( const char* serverName, const OmaTypes::ServerType serverType, 
                                OmaClientConnectionClassResetCB::OmaDisconnectReason reason )
{
    // disconnected	
    GSLOGFINFO << "ConnectionResetCB::disconnected_from: " << serverName << "; ServerType= "
         <<OmaTypes::server_type_to_string(serverType)<< " ";
    switch (reason)
    {
        case TerminalDisconnect:  GSLOGFINFO << "Terminal Disconnect" << endl; break;
        case MaxRetriesExhausted: GSLOGFINFO << "Maximum retries" << endl; break;
        case ServerDisconnected:  GSLOGFINFO << "Server Disconnected" << endl; break;
        case EmptyReconnectionList: GSLOGFINFO << "EmptyReconnectionList" <<endl; break;
    }
}

void ConnResetCB::on_attempt_server_login_ex( const char* serverName, const OmaTypes::ServerType serverType, int iAttempt )
{
    // a callback for every attempt
    GSLOGFINFO << "ConnectionResetCB::on_attempt_server_login: " << iAttempt 
               << " ;ServerName="<< serverName
               << "; ServerType= "<<OmaTypes::server_type_to_string(serverType)<<endl;
}
void ConnResetCB::server_down_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq )
{
    GSLOGFINFO << "ConnectionResetCB::server_down " << strServer << "; ServerType= "
               <<OmaTypes::server_type_to_string(serverType)<<endl;
    GSLOGFINFO << " NVP is " << nvpSeq << endl;
}
void ConnResetCB::server_up_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq )
{
    GSLOGFINFO << "ConnectionResetCB::server_up " << strServer << "; ServerType= "
               <<OmaTypes::server_type_to_string(serverType)<<endl;
    GSLOGFINFO << " NVP is " << nvpSeq << endl;    
}

void ConnResetCB::server_unavail_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq )
{
    GSLOGFINFO << "ConnectionResetCB::server_unavail " << strServer << "; ServerType= "
               <<OmaTypes::server_type_to_string(serverType)<<endl;
    GSLOGFINFO << " NVP is " << nvpSeq << endl;    
}        

void ConnResetCB::server_avail_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq )
{
    GSLOGFINFO << "ConnectionResetCB::server_avail " << strServer << "; ServerType= "
               <<OmaTypes::server_type_to_string(serverType)<<endl;
    GSLOGFINFO << " NVP is " << nvpSeq << endl;    
}            


