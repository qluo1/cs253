#ifndef OMACLIENT_H 
#define OMACLIENT_H

#include <Python.h>
#include <boost/python.hpp>

// This is a regular view client, that uses the reconnection logic of the clientAPI
#include <OmaClientCommon.H>		// for the failure defines 
#include <OmaClientConnection.H>	// for the connection 
#include <OmaClientConnectionReceiver.H>	// for the connection callbacks
#include <OmaClientViewCB.H>		// for the view callbacks
#include <OmaSubNVPSeq.H>			// internalize for OmaOrderData needs this
#include <OmaOrderDataFactory.H>	// for create_order_data 
#include <OmaOrderData.H>			// we are internalizing into an orderdata
#include <OmaNVPSequence.H>


// connection callback class, this notifies your client when you
// have been disconnected, reconnected and attempting relogin to a server
class ConnResetCB : public OmaClientConnectionClassResetCB
{
    void connected_to_ex( const char* serverName, const OmaTypes::ServerType serverType);
    void disconnected_from_ex( const char* serverName, const OmaTypes::ServerType serverType, 
            OmaClientConnectionClassResetCB::OmaDisconnectReason reason );
    void on_attempt_server_login_ex( const char* serverName, const OmaTypes::ServerType serverType, int iAttempt );
    void server_down_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq );
    void server_up_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq );
    void server_unavail_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq );
    void server_avail_ex( const char* strServer, const OmaTypes::ServerType serverType, const OmaNVPSequence& nvpSeq );

};

// this is your view callback class.  Your application gets notified when
// items are updated in your view, you should iterate thru the NVPSequence
// as soon as possible and put it in an object
class OmaClientCB : public OmaClientViewCB
{
    public:

        OmaClientCB(OmaSequenceNumberHolder* h=NULL) : conn_(NULL), 
        holder_(h),
        callback_() {}

        virtual ~OmaClientCB() {}

        void setConnection( OmaClientConnection* c ) { conn_ = c; }
        void setSeqNumHolder( OmaSequenceNumberHolder* h ) { holder_ = h; }


        virtual RWBoolean process_oma_status_message(const OmaClientViewID& viewId,
                const RWCString& serverName,
                OmaTypes::ClientStatus status);


        virtual RWBoolean process_oma_query_message(const OmaClientViewID& viewId,
                const RWCString& serverName,
                const OmaNVPSequence& nvp);

        virtual RWBoolean process_oma_view_message(const OmaClientViewID& viewId,
                const RWCString& serverName,
                const OmaOperationType& opType,
                const OmaNVPSequence& nvp)
        {
            return process_message(viewId,serverName,opType,nvp,"oma_view_message");    
        }

        virtual RWBoolean process_oma_view_execution(const OmaClientViewID& viewId,
                const RWCString& serverName,
                const OmaOperationType& opType,
                const OmaNVPSequence& nvp)
        {
            return process_message(viewId,serverName,opType,nvp,"oma_view_execution");    
        };

        // more methods can be implemented here see OmaClientViewCB
        //
        //
        void setupCallback(const std::string& name,PyObject* callback)
        {
            callback_ = make_pair(name,callback);
        };

        OmaClientConnection* conn_;

        OmaSequenceNumberHolder* holder_;

    protected:
        // internal shared 
        bool process_message(const OmaClientViewID& viewId,
                const RWCString& serverName,
                const OmaOperationType& opType,
                const OmaNVPSequence& nvp,
                const char* name);

        // CALLBACK
        std::pair<std::string,PyObject*> callback_;

};


#endif
