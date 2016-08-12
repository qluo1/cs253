/*
 * Author: Luiz Ribeiro (Melbourne Technology Division)
 * December, 2015
 */

#ifndef IVCOMPYSERVER_H
#define IVCOMPYSERVER_H

#include <Python.h>
#include "IvComApi.hpp"
#include "python_parser.cpp"
#include <boost/python.hpp>
#include <string>

using namespace std;
namespace bp = boost::python;

// forwarded declaration -- see IvComPyManager.h
class IvComPyManager;

class IvComPyServer: public IvComServerRequestCallback, public IvComServerRequestStatusCallback,
						public IvComWorkCallback
{
public:
	IvComPyServer(IvComPyManager& manager, const string& name);
	virtual ~IvComPyServer();

	const char* serverName();

	/*
	 * Attetion: regardless of the call back name, the registered callback is going to be
	 * invoked everytime that a new message is received. Maybe in the future multiple callbacks
	 * registration is implemented.
	 */
	void setupCallback(const string& name, PyObject* callback);

private:
	void onRequest(IvComServerRequestCallback::Data& data);

	void onRequestAvailability(IvComServerRequestCallback::RequestAvailability& data);

	void onStatus(IvComServerRequestStatusCallback::Data& data);

	/*
	 * Inherited from IvComWorkCallback. Always when the server receives a request, it creates a new
	 * worker object that holds a copy of the inbound message on its context. Eventually, IvCom schedules
	 * this worker to run, thus causing this callback to be executed, sending a response back to the client.
	 */
	void onWork(IvComWork* work, void* context);

	IvComPyManager& manager_;
	string name_;
	pair<string, PyObject*> callback_;
};

#endif
