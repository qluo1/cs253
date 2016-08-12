#ifndef OMACLIENTMGR_H
#define OMACLIENTMGR_H
#include <Python.h>
#include "OmaTypes.H"
#include "OmaClientConnection.H"
#include "OmaClientCB.hpp"
#include "OmaPermClientView.H"
#include "OmaFilePersistSeqNumHolder.H"


using namespace std;

class OmaClientManager
{

public:

    OmaClientManager(const string& seqHolder);
    ~OmaClientManager();

    bool logon(const char* host, const char* service, const char* user, const char* pwd, const char* viewName);

    bool registerCallback(const string& method_name, PyObject* pCallback);

    bool stop();
    // send nvp in raw string format.
    bool send_transaction(const string& data);

private:

    OmaFilePersistSeqNumHolder holder_;

    ConnResetCB* pConnCB_;
    OmaClientCB* pClientCB_; 
    OmaPermClientView* pView_;

};




#endif 


