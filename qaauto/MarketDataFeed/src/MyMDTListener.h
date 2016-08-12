#ifndef MYMDTLISTENER_H
#define MYMDTLISTENER_H

#include <Python.h>
#include <mdt/MDToolkit.h>
#include <iostream>
#include <vector>
#include <string>
#include <boost/shared_ptr.hpp>
#include <GSLog.H>

using namespace std;
using namespace MDT;

class MyMDTListener : public IMDListenerClient
{

public:

    MyMDTListener(const string& env,const string& user,const vector<string>& service);

    virtual ~MyMDTListener();
	/**
	 * Called by the MD Toolkit listener interface when a data message is received on the market
	 * data infrastructure. The example implementation here just prints out all available field
	 * names and values to the console.
	 *
	 * @param message 	a data message
	 * @param userdata	the user provided data object for the subscribed symbol, null if not provided
	 * @see 		IMDListenerClient#onMessage(IMDMessage&, void*)
	 */
	void onMessage(const IMDMessage& message, void* userdata);

	/**
	 * Called by the MD Toolkit listener interface when a status message is received on the
	 * market data infrastructure. The example implementation here just prints the status
	 * symbol, type and description to the console.
	 *
	 * @param status	a status message
	 * @see 		IMDListenerClient#onStatus(IMDStatus&)
	 */
	void onStatus(const MDStatus& status, void* userdata);
	/**
	 * Called by the MD Toolkit listener interface when a model data and/or status message 
	 * needs to be delivered from market data infrastructure. The example implementation 
	 * here doesnt implement this yet.
	 *
	 * @param mdModel	a model object
	 * @see 		IMDListenerClient#onModel(const IMDModel& mdModel, void* userdata)
	 */
	void onModel (const IMDModel& mdModel, void* userdata);

    bool subscribe(const string& service, const vector<string>& symbols);
    bool unsubscribe(const string& service, const vector<string>& symbols);


    void setupCallback(const string& name,PyObject* callback)
    {
        GSLOGFINFO <<"setupCallback in c++ " << name <<endl;
        cb_onmsg_ = make_pair(name,callback);
    };

    void setupStatusCB(const string& name, PyObject* callback)
    {
        GSLOGFINFO <<"setup onStatus callback in c++ " <<name << endl;
        cb_onstatus_ = make_pair(name,callback);

    };

private:
    // private copy ctor
    //MyMDTListener(const MyMDTListener &) {};

    IMDSession*     session_;

    vector<pair<string,IMDSubscriber*> >  subscribers_;
    typedef vector<pair<string,IMDSubscriber*> >::const_iterator SubIterator;

    MDSessionSpec   sessionSpec_;

    // C*ALLBACK
    pair<string,PyObject*> cb_onmsg_;
    pair<string,PyObject*> cb_onstatus_;

};


#endif

