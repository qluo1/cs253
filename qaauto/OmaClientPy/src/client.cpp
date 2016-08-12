#include "OmaTypes.H"
#include "OmaClientConnection.H"
#include "GSLog.H"

#include <iostream>

using namespace std;

void serverResetCB(const OmaClientConnection& conn,RWBoolean reconnected)
{
    GSLOGFINFO << "serverRest " << reconnected <<endl;

    if(reconnected)
    {
        GSLOGFINFO << "reconnected" <<endl;
    }else{
        GSLOGFSEVERE << "disconnected" <<endl;
    }

}


int main(int argc, char** argv)
{

    GSLOGFINFO << argc << " : "  << argv[1] << " " << argv[2] << "" << endl;
    const RWCString host(argv[1]);
    const RWCString port(argv[2]);
    const RWCString user(argv[3]);

    OmaClientConnection* pConn;
    pConn = new OmaClientConnection();
    pConn->add_server_reset_cb(serverResetCB);

    ConnectionProperties connProps;
    connProps.server_list.append(new OmaServerHost(host,port));
    connProps.user_id = user;
    connProps.password = "qa_omaclient";

    RWCString userDesc;
    if (!pConn->log_on(OmaTypes::OmaServer,connProps,userDesc))
    {
        GSLOGFSEVERE << "failed to login" <<endl;
    }else{
        GSLOGFINFO << "user desc as : " << userDesc <<endl;
    }


    pConn->log_off();
    rwSleep(10);
    delete pConn;

    return 0;

}

