/*
 * Author: Luiz Ribeiro (Melbourne Technology Division)
 * December, 2015
 */
#include <boost/python.hpp>
#include "GSLog.H"
#include "IvComPyServer.h"
#include "IvComPyManager.h"
#include "IvComPyDict.h"
#include "ReleaseGil.h"
#include <sstream>


IvComPyServer::IvComPyServer(IvComPyManager& manager, const string& name) :
	manager_(manager), name_(name) {
}

// Empty destructor, allows overwriting
IvComPyServer::~IvComPyServer() { }

/* onX events section */

/* This function executed whenever the server receives a client request */
void IvComPyServer::onRequest(IvComServerRequestCallback::Data& data) {
	GSLOGFASTFINFO << "onRequestData called. Incoming message type: " << data.request().table().tableName() << endl;
	GSLOGFASTFINFO << "Creating async worker." << endl;

	// keeps a internal copy of data, since we don't have control over the parameter, since it's a reference
	IvComServerRequestCallback::Data *internalData = new IvComServerRequestCallback::Data(data);

	// creating a worker to perform the request asynchronously
	IvComError::Value status;
	IvComWork* asyncWorker =  manager_.manager()->getEventManager()->createWork();

	// saving the message state into the worker
	status = asyncWorker->setContext((void *) internalData);
	if (status != IvComError::None)
		GSLOGFSEVERE << "Failed to save the context on the worker." << endl;

	// registering callback -- will trigger onWork function
	status = asyncWorker->setCallback(this);
	if (status != IvComError::None)
		GSLOGFSEVERE << "Failed to install worker callback." << endl;

	GSLOGFASTFINFO << "Request server created IdleWork. This request will be attended as soon as the worker is scheduled." << endl;
}


void IvComPyServer::onWork(IvComWork* work, void* context) {

	GSLOGFASTFINFO << "Worker scheduled to work." << endl;
	manager_.manager()->getEventManager()->destroyWork(work);
	
	// convering message pointer from void to IvComMessage data structure
	IvComServerRequestCallback::Data *data = (IvComServerRequestCallback::Data*) context;

	// extracting data from incoming message
	const IvComMessage incoming = data->request();
	string tableName = incoming.table().tableName();

	GSLOGFASTFINFO << "Table name: " << tableName << endl;

	// converting inbound client id to c++ string
	//string messageId = static_cast<ostringstream*>(&(ostringstream() << data->requestId()))->str();
    std::ostringstream ss;
    ss << data->requestId();
    string messageId(ss.str()); 

	bool posDup = !(data->posDup() == IvComPosDup::NotPosDup);

	// if there's a proper callback registered on python client, invoke it
	if (callback_.second) {
		AquireGil lock;

		// converting incoming message to py dict
		bp::dict dictMsg, tableData;

		if (!IvComPyDictDecoder::ivComToPyDict(incoming, dictMsg))
			GSLOGFSEVERE << "Failed to convert incoming message from IvComTable to Python dict" << endl;

		// The Python callback has to return a tuple to the C++ code, however we need to check if this
		// has happened, since Python functions are weakly typed.
		
		/* storing the function result on a generic "untyped" object, we also only demand that the function
		 * returns an object for now (even None). However, we must be able to extract from this object a string
		 * containning the response table name and a dict with the table's data.
		 */
		bp::object result = bp::call_method<bp::object>(callback_.second, callback_.first.c_str(), tableName, 
				dictMsg, messageId, posDup);

		bool extractionOk;

		try {
			bp::tuple returnedTuple;
			extractionOk = convertPyInto<bp::tuple>(result, returnedTuple);
			if (!extractionOk)
				throw BadPyCast("The Python registered callback was expected to return a tuple, but it didn't");

			// confirmed a tuple, now confirming its size
			int tupleLenght = bp::len(returnedTuple);
			if (tupleLenght != 2)	//(tableName, tableData)
				throw BadPyCast("The tuple returned by the Python callback function registered on onWork event"
					"must contain exactly two elements: the table name (string) and its data (dict)");

			string tableName;
			extractionOk = convertPyInto<string>(returnedTuple[0], tableName);
			if (!extractionOk)
				throw BadPyCast("The first element of the tuple returned by the registered Python callback for " 
					"onWork event must be a string (the table name.)");

			bp::dict tableData;
            
            // extract response into tableData
			extractionOk = convertPyInto<bp::dict>(returnedTuple[1], tableData);
			if (!extractionOk)
				throw BadPyCast("The second element of the tuple returned by the registered Python callback for "
					"onWork event must be a dictionary (the table data).");

			GSLOGFDEBUG << "Python callback invoked successfully." << endl;

			// conversion and validation of the Python's callback is done. Now convert the dict into a message 
			IvComTable ivTable = manager_.manager()->getCatalogManager()->getTable(tableName.c_str());

			if (!ivTable.isValid()) {
				GSLOGFASTFSEVERE << "Failed to construct a response table based on the name returned by the " <<
					"Python callback subscribed on onWork (" << tableName << ")" << endl;
			}
			else {
				IvComMessage response(ivTable);

				if (!IvComPyDictDecoder::pyDictToIvCom(manager_.manager()->getCatalogManager(), tableData, response)) 
					GSLOGFSEVERE << "Failed to convert Python response to IvComMessage to send response back." << endl;
				else {
					// sending response back to client
                    GSLOGFASTFDEBUG << "response table: " << response << endl;

					IvComError error = data->sendResponse(response);

					if (error != IvComError::None)
						GSLOGFSEVERE << "Server failed to send acknowledgement." << endl;
					else
						GSLOGFASTFINFO << "Sent response." << endl;
				}
			}
		} 
		catch (const BadPyCast &e) {
			GSLOGFSEVERE << e.what() << endl;
		} 
	}
	else {
		GSLOGFSEVERE << "No Python callback registered to receive the following message:\n" <<
			incoming << endl;
	}

	GSLOGFASTFINFO << "Destroying work." << endl;

	// deleting the temporary data object, created when the server received the request from the client
	delete data;
}

void IvComPyServer::onRequestAvailability(IvComServerRequestCallback::RequestAvailability& data) {
	IvComError error = data.indicateAvailability(100);

	if (error != IvComError::None)
		GSLOGFASTFSEVERE << "[" << data.requestManagerName() << 
			"] error indicating availability [" << error.text() << ']' << endl;
	else
		GSLOGFASTFINFO << "[" << data.requestManagerName() << "] indicated availability" << endl;
}

void IvComPyServer::onStatus(IvComServerRequestStatusCallback::Data& data) {
	GSLOGFASTFINFO << '[' << data.requestManagerName() << 
		"] received status calback for [" << data.status() << ']' << endl;
}

const char* IvComPyServer::serverName() {
	return this->name_.c_str();
}

void IvComPyServer::setupCallback(const string& name, PyObject* callback) {
	this->callback_ = make_pair(name, callback);
}
