#include "OmaClientMgr.hpp"

#include <OmaClientCommon.H>
#include <OmaClientViewCB.H>
#include <OmaPermClientView.H>

#include <OmaDummyProductFactory.H>
#include <OmaDummyAccountFactory.H>
#include <OmaDummyUserFactory.H>
#include <OmaNVPNames.H>
#include <OmaNVPSequence.H>

#include <boost/thread.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>

#include <GSLog.H>

bool   bRunning_ = false;

OmaClientManager::OmaClientManager(const string& seqHolder):
    holder_(seqHolder),
    pConnCB_(new ConnResetCB()),
    pClientCB_(new OmaClientCB()),
    pView_(NULL)

{

}

OmaClientManager::~OmaClientManager()
{
    if (pView_!= NULL)
    {
        GSLOGFINFO << "delete pView_ on destructor" <<endl;
        delete pView_;
    }

    if (pConnCB_ != NULL)
    {
        delete pConnCB_;
    }

    if (pClientCB_ != NULL)
    {
        delete pClientCB_;
    }
}


/// internal threading 
void run(OmaClientView* pView=NULL)
{
    assert (pView != NULL);
    GSLOGFINFO << "start thread run loop." <<endl;
    while (bRunning_)
    {
        while (pView != NULL && pView->more_work())
        {
            pView->do_work();
        }
        boost::this_thread::sleep(boost::posix_time::milliseconds(100));
    }
    GSLOGFINFO << "running thread stopped" << endl;

}

bool OmaClientManager::logon(const char* host, const char* service, const char* user, const char* pwd,const char* viewName)
{

    //connection properties
    //
    ConnectionProperties connProps = ConnectionProperties();
    connProps.server_list.append(new OmaServerHost(service,host));
    connProps.user_id = user;
    connProps.password = pwd;

    if (pView_ != NULL)
    {
        GSLOGFSEVERE << "already logged on? or view already created?" << endl;
        return false;
    }

    RWCString userDest;
    RWBoolean success;

    pView_ = new OmaPermClientView(viewName, pClientCB_, OmaTypes::OmaServer, connProps, userDest, success);

    if (!success)
    {
        GSLOGFSEVERE << "Failed to log on " << endl;

        delete pView_;
        pView_ = NULL;
        return false;
    }

    pClientCB_->setConnection(pView_->myConnection());
    pClientCB_->setSeqNumHolder(&holder_);

    pView_->myConnection()->add_server_reset_cb( pConnCB_ );

    GSLOGFTRACE <<  "Connected Now" << endl;

    //Configure view and add fields, filters, and sub-filters
    pView_->turn_on_batch_changes();
    pView_->add_field(OmaNvpAllFields);
    pView_->add_filter( OmaFilterAllClassId, OmaClientView::RegularFilter);
    pView_->turn_off_batch_changes();

    GSLOGFINFO << "Turn off batch changes" << endl;

    int retries = 30;
    //view->myConnection()->set_num_retries(OmaTypes::OmaServer, retries);
    pView_->myConnection()->set_num_retries(retries);
    GSLOGFINFO << "Set retries to " << retries << endl;


    pView_->restart_from_tags(holder_, TRUE); 
    //view->restart_from_tag(0); 

    GSLOGFINFO << "Starting work loop" << endl;

    bRunning_ = true;

    boost::thread t(run, pView_);

    return true;

}

bool OmaClientManager::stop()
{
    if (bRunning_)
    {
       // stop running thread
       bRunning_ = false;
       if (pView_)
        {
            OmaClientConnection* pConn = pView_->myConnection();
            pConn->log_off();
            // clean up internal view on stop the session.
            // python might not destruct the session on exit.
            delete pView_;
            pView_ = NULL;
            GSLOGFINFO << "stop oma client session: log_off/delete pView_." <<endl;
        }
    }

    return bRunning_;
}


bool OmaClientManager::registerCallback(const string& method_name, PyObject* pCallback)
{
    bool ret = false;

    if (pClientCB_)
    {
        pClientCB_->setupCallback(method_name,pCallback);
        GSLOGFINFO << "oma client callback registered" << endl;
        ret = true;
    }else
    {
        GSLOGFSEVERE << "OmaClientCB is null " <<endl;
    }
    return ret;

}

bool OmaClientManager::send_transaction(const string& data)
{
    OmaNVPSequence sendResults;
    OmaNVPSequence valResults;
    OmaNVPSequence nvpSeqCopy;

    nvpSeqCopy = OmaNVPSequence(data.c_str());

    GSLOGFDEBUG << nvpSeqCopy << endl;

    bool res = false;
    if(! nvpSeqCopy.checkIfValid())
    {
        GSLOGFSEVERE << "invalid NVP sequence: [ " << data << "]" << endl;
        return res;
    }

    if (pView_ &&  pView_->myConnection())
    {
        OmaTypes::TransactionResult tranResult;
        int ret = pView_->myConnection()->send_transaction(
                (OmaTypes::TransactionType) OmaTypes::AdministrativeUpdate,
                nvpSeqCopy,
                true,
                sendResults,
                valResults,
                tranResult
                );

        if (ret == OmaTypes::TransRejected)
        {
            GSLOGFSEVERE  << "\nError: Transaction #" << data << " rejected by OMA" << endl << endl
                          << nvpSeqCopy << endl
                          << "Send Results:" << sendResults << endl
                          << "Validation Results:" << valResults << endl ;
        }
        else
        {
            res = true;
            GSLOGFINFO << "\nDone: Transaction #" << data << " was successfully processed by OMA" << endl;
        }
    }else{
        GSLOGFSEVERE << "connection isn't available or not logged on yet." <<endl;
    }

    return res;
}
