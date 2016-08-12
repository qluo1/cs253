/*
 * Author: Luiz Ribeiro (Melbourne Technology Division)
 * January, 2016
 */

#ifndef IVCOMPYIMGCLIENT_H_
#define IVCOMPYIMGCLIENT_H_

#include <boost/python.hpp>
#include "IvComApi.hpp"
#include "python_parser.cpp"
#include "IvComPyDict.h"
#include "ReleaseGil.h"

#include <string>
#include <map>
#include <list>

using namespace std;
namespace bp = boost::python;


class IvComPyManager;

class IvComPyImgLiveClient : public IvComClientImageLiveStatusCallback, public IvComClientImageLiveCallback {
private:
    IvComPyManager& manager_;
    string& name_;
    
    // used to send requests to create view
    IvComClientImageLiveManager* clientManager_;

    /* Used to trigger Python callbacks from C++ code */
    PyObject* pythonObjectAddr;
    string onNotifyCallbackName, onEventCallbackName;

    /* expected keys when converting a Python dict into a ImgLive filter */
    static string FIELD_NAME;
    static string TRIGGER_VALUES;
    static string OPERATOR;


    /* This dummy function converts the enumerator into its correponding int, as boost.python
     * doesn't do this transparently.
     */
    int decodeTypeEnum(IvComImageLiveNotificationType type);

    bool callOnEvent(const char* viewName, const char* reason, const char* event);
    bool callOnNotify(IvComImageLiveViewRecord& record, const string& event);

    virtual bool onRecordUpdate(IvComImageLiveViewRecord& viewRecord, void* context);
    virtual bool onRemoveRecord(IvComImageLiveViewRecord& viewRecord, void* context);

    virtual bool onClearAllRecords (const char* viewName, void* context);
    virtual bool onInitializationCommence (const char* viewName, void* context);
    virtual bool onInitializationComplete (const char* viewName, void* context);
    virtual bool onViewCreateSuccess(const char* viewName, void* context);
    virtual bool onViewCreateFailure(const char* viewName, const char* reason, void* context);
    virtual bool onViewUpdateSuccess(const char* viewName, void* context);
    virtual bool onViewUpdateFailure(const char* viewName, const char* reason, void* context);

    virtual bool onBatchStart(const char* viewName);
    virtual bool onBatchEnd(const char* viewName);

    virtual void onStatus(Data& data);
    
    IvComClientImageLiveStatus status_;
    /* Utility function that converts a python representation of a View into a IvCom object. If this
     * is not possible due to malformed or invalid representation, a BadPyCast exception with details is
     * thrown.
     */
    IvComFilterDefinitionList extractViewFromList(bp::list);

public:
    IvComPyImgLiveClient(IvComPyManager& manager, IvComClientImageLiveManager* clientManager, string& name);
    ~IvComPyImgLiveClient();

    /* Returns the client name on the configuration file */
    const char* clientName();

    /* Sends a request to the corrseponding server to create a view
     * @param viewName (py or c++ string): the name of the view to be created
     * @param pyList (py.dict): list of dictionaries representing a ImageLive view.
     * @returns bool: True [C++/Python]: if the request was sent successfully. False otherwise
     */
    bool requestViewCreation(const string& viewName,  bp::list pyList);

    /* Sends a request to the server to cancel a view named @viewName.
     * returns bool: True if the request was sent successfully
     */
    bool requestViewCancel(const string& viewName);

    /* Updates view rules on the server. It's up to the server how to interpret the update request.
     * It may either replace the previous view with this one or amend the current view. Notice
     * however that this function will *NOT* retrieve the view @viewName stored on the server to
     * perform the modifications, instead a new view is sent to the server. Hence removing filters 
     * and allowed values for filters from the view may not supported.
     */
     bool requestViewUpdate(const string& viewName, bp::list modifications);
     
    /* Registers the name of the Python functions to be invoked. 
     * onNotify is triggered if the underlying onRecordUpdate or onRemoveRecord callbacks are invoked,
     * which happens if a server message matches a subscribed view. In this case, this function receives as
     * parameter a dict in the following format: 
     * {    
     *    event -> string (if the event was an "update" or "remove" on the server-side,
     *    viewName -> string (the name of the view triggered by this message
     *    recordId -> string
     *    version -> uint
     *    isInitialization -> bool (true if this is a initialization message or message triggered by view update)
     *    type -> either 0 (invalid), 1 (update), 2 (insert), 3 (remove)
     * }
     *
     * onEvent is triggered if either on{ClearAllRecords, InitializationCommence, InitializationComplete,
     * ViewCreateSuccess, ViewCreateFailture, ViewUpdateSuccess, ViewUpdateFailure} is triggered.
     * (add details here about onNofify)
     * when onEvent is triggered, it receives as parameter a Python dictionary in the form {'viewName' -> string,
     * 'reason' -> string (not null only for onView[Create|Update]Failure) }.
     */
    void registerCallbacks(PyObject* object, const string& onNotify, const string& onEvent);

    const char* status() { return status_.text(); };

};

#endif
