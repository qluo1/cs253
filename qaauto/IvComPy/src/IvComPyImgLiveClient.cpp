/*
 * Author: Luiz Ribeiro (Melbourne Technology Division)
 * January, 2016
 */
#include <boost/python.hpp>
#include "IvComPyImgLiveClient.h"

IvComPyImgLiveClient::IvComPyImgLiveClient(IvComPyManager& manager, IvComClientImageLiveManager* clientManager, 
                                            string& name) : manager_(manager), name_(name) { 
    clientManager_ = clientManager;
    pythonObjectAddr = NULL;
}

// initializing private static fields
string IvComPyImgLiveClient::FIELD_NAME = "field";
string IvComPyImgLiveClient::TRIGGER_VALUES = "validValues";
string IvComPyImgLiveClient::OPERATOR = "operator";

IvComPyImgLiveClient::~IvComPyImgLiveClient() { }

const char* IvComPyImgLiveClient::clientName() {
    return name_.c_str(); 
}

  
bool IvComPyImgLiveClient::requestViewCreation(const string& viewName, bp::list pyList) {
    bool returnValue = false;
    IvComFilterDefinitionList filterList;

    try {
        GSLOGFASTFINFO << "Creating filter" << endl;
        filterList = extractViewFromList(pyList);
        GSLOGFASTFINFO << "Filter created successfully" << endl;
    } catch (BadPyCast& exception) {
        GSLOGFASTFSEVERE << "Could not create filter based on Python dictionary. Additional information: " <<
                            exception.what() << endl;

        return false;
    }

    ReleaseGil unlock;
    void *context = 0;
    IvComClientImageLiveHandle handle = clientManager_->getClientImageLiveHandle(name_.c_str());
    IvComError error = clientManager_->createView(handle, context, viewName, filterList);

    if (error != IvComError::None) {
        GSLOGFASTFSEVERE << "Could not send a request to create view [" << viewName << "]\n"
                                "Aditional information: " << error.text() << endl;
    }
    else
        returnValue = true;

    return returnValue;
}


bool IvComPyImgLiveClient::requestViewCancel(const string& viewName) {
    ReleaseGil unlock;
    void* context = 0;

    IvComClientImageLiveHandle handle = clientManager_->getClientImageLiveHandle(name_.c_str());
    IvComError error = clientManager_->cancelView(handle, context, viewName);

    return (error == IvComError::None);
}


bool IvComPyImgLiveClient::requestViewUpdate(const string& viewName, bp::list modifications) {
    bool returnValue = false;
    IvComFilterDefinitionList filterList;
    
    try {
        GSLOGFASTFINFO << "Creating filter" << endl;
        filterList = extractViewFromList(modifications);
        GSLOGFASTFINFO << "Filter created successfully" << endl;
    } catch (BadPyCast& exception) {
        GSLOGFASTFSEVERE << "Could not create filter based on Python dictionary. Additional information: " <<
                            exception.what() << endl;
        return false;
    }

    void *context = 0;
    GSLOGFASTFINFO << "Trying to contact server " << name_ << " to update view " << viewName << endl;
    ReleaseGil unlock;

    IvComClientImageLiveHandle handle = clientManager_->getClientImageLiveHandle(name_.c_str());
    IvComError error = clientManager_->updateView(handle, context, viewName, filterList);

    if (error != IvComError::None) {
        GSLOGFASTFSEVERE << "Could not send a request to update view [" << viewName << "]\n"
                                "Aditional information: " << error.text() << endl;
    }
    else {
        returnValue = true;
        GSLOGFASTFINFO << "Request sent successfully." << endl;
    }

     
    return returnValue;
}


IvComFilterDefinitionList IvComPyImgLiveClient::extractViewFromList(bp::list pyList) {
    IvComFilterDefinitionList view;
    int listSize = bp::len(pyList);

    // each element of the list is a filter
    for (int i=0; i < listSize; i++) {
        bp::dict filter;
        if (!convertPyInto<bp::dict>(pyList[i], filter))
            throw BadPyCast("When creating ImgLive view, expected a Python dictionary describind the filter, but "
                                "something else was found.");

        // verify if the dict contains all the expected fields
        if (!filter.has_key(FIELD_NAME))
            throw BadPyCast("The Python dictionary describing the filter lacks the field '" + FIELD_NAME + "'.");

        if (!filter.has_key(TRIGGER_VALUES))
            throw BadPyCast("The Python dictionary describing the filter lacks the field '" + TRIGGER_VALUES + "'.");

        // creating the ImgLive view
        IvComFilterDefinition& newFilter = view.add();
       
        // usually OPERATOR is the name of the filter, however there are some special cases, for example,
        // when the filterName is 'objectType' or 'fieldInclusion' that OPERATOR isn't used. In these cases,
        // FIELD_NAME becomes the filter name.
       
        string filterName;
        if (filter.has_key(OPERATOR)) {
            if (!convertPyInto<string>(filter[OPERATOR], filterName))
                throw BadPyCast("While creating the ImageLive view from Python dictionary. The " + OPERATOR +
                                    " field must be a string.");
    
            // the name of the inspected field must be the first element on the filter parameters
            string fieldName;
            convertPyInto<string>(filter[FIELD_NAME], fieldName);
            newFilter.addParameter(fieldName);  // checked when verifying dict keys
        }
        else
            convertPyInto<string>(filter[FIELD_NAME], filterName);  //no need to check done when verifying keys

        newFilter.filterName(filterName);

        // Gets a C++ representation of the Python list of allowed values for this field
        list<string> triggerValues;
        bp::list pyValuesList;

        // convert this python dynamic pointer into a C++ static pointer for C++ manipulation
        if (!convertPyInto<bp::list>(filter[TRIGGER_VALUES], pyValuesList))
            throw BadPyCast("Expected a list of string values with the values that trigger the filter while "
                                "creating IvComPy ImgLive view, but something else was found.");

        if (!getListFromPyList<string>(pyValuesList, triggerValues))
            throw BadPyCast("Expected a list of string values with the values that trigger the filter while "
                                "creating IvComPy ImgLive view, but something else was found.");

        // Adds these values to the ImgLive filter
        for (list<string>::iterator value = triggerValues.begin(); value != triggerValues.end(); value++)
            newFilter.addParameter(*value); 
    }

    return view;
}


void IvComPyImgLiveClient::registerCallbacks(PyObject* object, const string& onNotify, const string& onEvent) {
    pythonObjectAddr = object;
    onNotifyCallbackName = onNotify;
    onEventCallbackName = onEvent;
}


bool IvComPyImgLiveClient::callOnEvent(const char* viewName, const char* reason, const char* event) {
    GSLOGFASTFINFO << "ImgLive callback [" << event << "] triggered. Preparing to call Python callback." << endl;
    AquireGil lock;

    if (pythonObjectAddr && onEventCallbackName.size() != 0) {
        bp::dict paramsAsDict;

        string interm(viewName);

        paramsAsDict["viewName"] = interm;
        paramsAsDict["reason"] = reason;
        paramsAsDict["event"] = event;

        bp::call_method<void>(pythonObjectAddr, onEventCallbackName.c_str(), paramsAsDict);
    }

    return true;
}


bool IvComPyImgLiveClient::callOnNotify(IvComImageLiveViewRecord& record, const string& event) {
    if (!pythonObjectAddr || onNotifyCallbackName.size() == 0) return true;

    do {
        AquireGil lock; // scoped GIL
        bp::dict params;
        bp::dict dictMsg;

        params["event"] = event.c_str();
        params["viewName"] = record.viewName();
        params["recordId"] = record.recordId();
        params["version"] = record.version();
        params["isInitialization"] = record.isInitialization();
        params["type"] = decodeTypeEnum(record.type());

        if (!IvComPyDictDecoder::ivComToPyDict(*(record.message()), dictMsg))
            GSLOGFASTFSEVERE << "Failed to convert Image Live IvComMessage into Python dictionary (It shouldn't happen)\n"; 
        else {
            params["message"] = dictMsg;
            bp::call_method<void>(pythonObjectAddr, onNotifyCallbackName.c_str(), params);
        }
    } while(0);

    // Regardless of being able to convert the IvComMessage into Py, send ACK to the server to avoid queue overfill
    IvComClientImageLiveHandle handle = clientManager_->getClientImageLiveHandle(name_.c_str());
    IvComError error = clientManager_->acknowledgeProcessed(handle, record.viewName().c_str(), 
                            record.recordId().c_str(), record.version(), "");

    if (error != IvComError::None)
        GSLOGFASTFSEVERE << "Could not send ACK [" << error.text() << "]." << endl;
    else
        GSLOGFASTFINFO << "ACKed server successfully for message [" << record.viewName() << ":" << record.recordId()
            << ":" << record.version() << "]" << endl;

    return true;
}


int IvComPyImgLiveClient::decodeTypeEnum(IvComImageLiveNotificationType type) {
    return type;
}


/* Event callbacks -- These will trigger onEvent Python callback */
bool IvComPyImgLiveClient::onClearAllRecords (const char* viewName, void* context) {
    return callOnEvent(viewName, NULL, "onClearAllRecords");
}

bool IvComPyImgLiveClient::onInitializationCommence (const char* viewName, void* context) {
    return callOnEvent(viewName, NULL, "onInitializeCommence");
}

bool IvComPyImgLiveClient::onInitializationComplete (const char* viewName, void* context) {
    return callOnEvent(viewName, NULL, "onInitilizationComplete");
}

bool IvComPyImgLiveClient::onViewCreateSuccess(const char* viewName, void* context) {
    return callOnEvent(viewName, NULL, "onViewCreateSuccess");
}

bool IvComPyImgLiveClient::onViewCreateFailure(const char* viewName, const char* reason, void* context) {
    return callOnEvent(viewName, reason, "onViewCreateFailure");
}

bool IvComPyImgLiveClient::onViewUpdateSuccess(const char* viewName, void* context) {
    return callOnEvent(viewName, NULL, "onViewUpdateSuccess");
}

bool IvComPyImgLiveClient::onViewUpdateFailure(const char* viewName, const char* reason, void* context) {
    return callOnEvent(viewName, reason, "onViewUpdateFailure");
}

/* Event callbacks -- These will trigger onNotify Python callback */
bool IvComPyImgLiveClient::onRecordUpdate(IvComImageLiveViewRecord& viewRecord, void* context) {
    return callOnNotify(viewRecord, "update");
}

bool IvComPyImgLiveClient::onRemoveRecord(IvComImageLiveViewRecord& viewRecord, void* context) {
    return callOnNotify(viewRecord, "remove");
}

/* Event callbacks -- These ones are ignored, however they produce log evidence */
bool IvComPyImgLiveClient::onBatchStart(const char* viewName) { 
    GSLOGFASTFINFO << "ImageLive view [" << viewName << "] triggered onBatchStart event. "
                        "This event won't be propagated to Python" << endl;
    return true;
}
bool IvComPyImgLiveClient::onBatchEnd(const char* viewName) {
    GSLOGFASTFINFO << "ImageLive view [" << viewName << "] triggered onBatchEnd event. "
                        "This event won't be propagated to Python" << endl;
    return true;
}


void IvComPyImgLiveClient::onStatus(Data& data) {
    // capture current status
    this->status_ = data.status();
}

