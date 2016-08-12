#include "MyMDTListener.h"
#include <iostream>
#include <boost/python/dict.hpp>
#include <boost/python.hpp>
#include "ReleaseGil.h"
#include <mdt/IMDSymbolList.h>
#include <mdt/MDSymbolListSpec.h>
#include <mdt/IMDSymbolListEvent.h>
#include <mdt/IMDSymbolListEventsIterator.h>

namespace bp = boost::python;

// init MyMDTListeneer
MyMDTListener::MyMDTListener(const string& env, const string& user, const vector<string>& services)
{
    try{

        MDToolkit::init();

        sessionSpec_.setEnvironment(MDString(env.c_str()));
        sessionSpec_.setUsername(MDString(user.c_str()));

        // Connect a session, subscriber and listener to the infrastructure
        session_   = MDToolkit::getSession( &sessionSpec_ );

        for (vector<string>::const_iterator i = services.begin(); i != services.end();++i)
        {
            subscribers_.push_back(make_pair(*i,session_->createSubscriber(i->c_str(), this )));
        }


    }catch( const MDToolkitException& mdte )
    {
			GSLOGFSEVERE << "MDToolkitException: " << mdte.what() << std::endl;
            exit(-1);
    }
}

MyMDTListener::~MyMDTListener()
{
    // Gracefully shutdown the API
    for (SubIterator i = subscribers_.begin(); i != subscribers_.end();++i)
    {
       session_->destroySubscriber(i->second );
    }
    MDToolkit::releaseSession(session_);

    MDToolkit::shutdown();
}

// subscribing symbols 
bool MyMDTListener::subscribe(const string& service,const vector<string> & symbols)
{
    //assert(subscriber_);
    GSLOGFINFO << "received call on subscribe for: "<< service << endl;

    bool result = false;

    for (SubIterator i = subscribers_.begin(); i != subscribers_.end(); ++i)
    {
        if (i->first == service)
        {
            try{
                MDSubSpec subSpec;
                MDSymbolListSpec symbolListSpec;
                
                vector<string>::const_iterator itr = symbols.begin();
                for (;itr != symbols.end(); ++itr)
                {
                    MDString symbol(itr->c_str());
                    subSpec.addSymbol(symbol);
                    symbolListSpec.addSymbol(symbol);

                }

                i->second->subscribe( &subSpec );
                //subscriber_->subscribe( &symbolListSpec);
                result = true;

            }catch(const MDToolkitException& mdte)
            {
                GSLOGFSEVERE << "MDToolkitException: " << mdte.what() << "code:" <<  mdte.getErrorCode()<< endl;
                return false;

            }
        } // if service name match
    } // for each services check

    return result;

}
// subscribing symbols 
bool MyMDTListener::unsubscribe(const string& service, const vector<string> & symbols)
{

    bool result = false;

    for(SubIterator it = subscribers_.begin(); it != subscribers_.end(); ++ it)
    {

        if (service == it->first)
        {

            try{
                MDSubSpec subSpec;
                
                vector<string>::const_iterator itr = symbols.begin();
                for (;itr != symbols.end(); ++itr)
                {
                    subSpec.addSymbol(MDString(itr->c_str()));
                }

                it->second->unsubscribe( &subSpec );

                result = true;
            }catch(const MDToolkitException& mdte)
            {
                GSLOGFSEVERE << "MDToolkitException: " << mdte.what() << endl;
                return false;

            }
        } // if service name match
    } // for each services
    return result;

}

void MyMDTListener::onModel(const IMDModel& mdModel, void* userdata)
{
    GSLOGFINFO << "onModel called" <<endl;
    switch (mdModel.getModelType())
    {
    case MTYPE_MDSYMBOLLIST:
        {
            const IMDSymbolList& symbolList = dynamic_cast<const IMDSymbolList&>(mdModel);
            IMDSymbolListEventsIterator& events = symbolList.getEventsIterator();

            GSLOGFINFO << "Message Type: " << ((symbolList.getMessageType() == IMAGE)?"IMAGE":"UPDATE") << std::endl;

            if (symbolList.getMessageType() == IMAGE)
                GSLOGFINFO << "IMAGE flag set: Clear the client cache - fresh image has arrived.\n";

            for(events.begin(); !events.end(); events++)
            {
                IMDSymbolListEvent* entry = events.value();
                switch (entry->getEvent())
                {
                case EVENT_ADD:
                    GSLOGFINFO <<  entry->getSymbol() << ":Added \t";
                    break;
                case EVENT_DELETE:
                    GSLOGFINFO <<  entry->getSymbol() << ":Deleted \t";
                    break;
                case EVENT_COMPLETE:
                    GSLOGFINFO << "Symbol List comlete!\n";
                        break;
                default:
                    GSLOGFINFO << "unhandled event" ;
                    break;
                }
            }
            GSLOGFINFO << "\n";
        }
        break;
    default:
        break;
    };

}

void MyMDTListener::onStatus(const MDStatus& status, void* userdata)
{
    GSLOGFINFO << "on status called" <<endl;
	GSLOGFINFO << " entity = " << status.getName() << endl;
    GSLOGFINFO << " class = " << status.getClassificationString() << endl;;
    GSLOGFINFO << " state = " << status.getStateString() <<endl;
    GSLOGFINFO << " code = " << status.getCodeString() << endl;;
    GSLOGFINFO << " desc = " << status.getDescription() << endl;
    //notify QuoteManager to clean up inactive symbols
    if (cb_onstatus_.second)
    {
        AquireGil lock;
        boost::python::dict data;
        data["entity"] = status.getName().c_str();
        data["class"] = status.getClassificationString().c_str();
        data["code"] = status.getCodeString().c_str();
        data["desc"] = status.getDescription().c_str();
        GSLOGFDEBUG << "callback with dict:" << cb_onstatus_.first <<endl;
        bp::call_method<void>(cb_onstatus_.second,cb_onstatus_.first.c_str(),data);
    }else{
        GSLOGFINFO << "No callback registgerd for onMessage" <<endl;
    }

  
}

void MyMDTListener::onMessage(const IMDMessage& msg, void *userdata)
{

    GSLOGFINFO << " on message recieved" <<endl;
    // process message data
    //
    IMDFieldIterator &iter = msg.getIterator();
    string name, value;
    MDT::FIELD_TYPE type; 
    //Must lock early as any boost python object access need GIL
    AquireGil lock;
    boost::python::dict data;
    data["SYMBOL"] = msg.getSymbol().c_str();
    data["IMAGE"] = msg.getMessageType() == IMAGE? "IMAGE": "UPDATE";
    data["SCHEMAID"] = msg.getSchemaId();
    data["STATUS"] = msg.getStatus()->getStateString().c_str();

    GSLOGFINFO << " --------------------------------------------------------------" << endl;
    GSLOGFINFO << "SYMBOL: " << msg.getSymbol() << " - " << msg.getSchemaId() << " - " \
            << ((msg.getMessageType() == IMAGE)?"IMAGE":"UPDATE") << " - " \
            << msg.getStatus()->getStateString() << endl;


    for (iter.begin(); !iter.end(); iter++)
    {
        try
        {
            IMDField *field = iter.value();
            name = field->getName().c_str();
            type = field->getType();

            switch (field->getType())
            {
            case FTYPE_NOT_SUPPORTED:
                GSLOGFDEBUG  << name << " :NOTSUPPORTED: " << field->getStringValue() << std::endl;
                data[name] = field->getStringValue();
            break;
            case FTYPE_BYTE:
                GSLOGFDEBUG << name << " :BYTE: " << field->getByteValue() << std::endl;
                data[name] = field->getByteValue();
            break;
            case FTYPE_SHORT:
                GSLOGFDEBUG << name << " :SHORT: " << field->getShortValue() << std::endl;
                data[name] = field->getShortValue();
            break;
            case FTYPE_INT32:
                GSLOGFDEBUG << name << " :INT32: " << field->getInt32Value() << std::endl;
                data[name] = field->getInt32Value();
            break;
            case FTYPE_INT64:
                GSLOGFDEBUG << name << " :INT64: " << field->getInt64Value() << std::endl;
                data[name] = field->getInt64Value();
            break;
            case FTYPE_FLOAT:
                GSLOGFDEBUG << name << " :FLOAT: " << field->getFloatValue() << std::endl;
                data[name] = field->getFloatValue();
            break;
            case FTYPE_DOUBLE:
                GSLOGFDEBUG << name << " :DOUBLE: " << field->getDoubleValue() << std::endl;
                data[name] = field->getDoubleValue();
            break;
            case FTYPE_STRING:
                GSLOGFDEBUG << name << " :STRING: " << field->getStringValue() << std::endl;
                data[name] = field->getStringValue();
            break;
            case FTYPE_OPAQUE:
                {
                    int nSize = 0;
                    const char *binaryBuffer = field->getOpaqueValue (&nSize);
                    std::cout << name << " :BINARY: Size=" << nSize << " : ";
                    for (int i=0; i<nSize; i++)
                    {
                        GSLOGFDEBUG  << std::hex << std::uppercase << (unsigned short)binaryBuffer[i] << " ";
                    }
                    std::cout << std::endl;
                break;
                }
            case FTYPE_ENUMERATED:
                GSLOGFDEBUG << name << " :ENUM: " << field->getStringValue() << std::endl;
                data[name] = field->getStringValue();
            break;
            case FTYPE_DATETIME:
            {
                MDDateTime dateTime;
                field->getDateTimeValue(dateTime);
                if (dateTime.isParsed())
                    GSLOGFDEBUG << name << " :PARSED DATETIME: " << dateTime.getMonth() << " / " \
                                << dateTime.getDay() << " / " << dateTime.getYear() << dateTime.getHour() << " : " \
                                << dateTime.getMinute() << " : " << dateTime.getSecond() << " : " << dateTime.getMicrosecond() << std::endl;
                else
                    GSLOGFDEBUG << name << " :DATETIME: " << dateTime.toString() << std::endl;

                data[name] = dateTime.toString();
                break;
            }
            case FTYPE_TIME:
            {
                MDDateTime dateTime;
                field->getTimeValue(dateTime);
                if (dateTime.isParsed())
                    GSLOGFDEBUG << name << " :PARSED TIME: " << dateTime.getHour() << " : " \
                                << dateTime.getMinute() << " : " << dateTime.getSecond() << " : " << dateTime.getMicrosecond() << std::endl;
                else
                    GSLOGFDEBUG << name << " :TIME: " << dateTime.toString() << std::endl;
                data[name] = dateTime.toString();
                break;
            }
            case FTYPE_DATE:
            {
                MDDateTime dateTime;
                field->getDateValue(dateTime);
                if (dateTime.isParsed())
                    GSLOGFDEBUG << name << " :PARSED DATE: " << dateTime.getMonth() << " / "\
                                << dateTime.getDay() << " / " << dateTime.getYear() << std::endl;
                else
                    GSLOGFDEBUG  << name << " :DATE: " << dateTime.toString() << std::endl;
                data[name] = dateTime.toString();
                break;
            }
            case FTYPE_REAL32:
                GSLOGFDEBUG  << name << " :REAL32: " << field->getFloatValue() << std::endl;
                data[name] = field->getFloatValue();
            break;
            case FTYPE_REAL64:
                GSLOGFDEBUG << name << " :REAL64: " << field->getDoubleValue() << std::endl;
                data[name] = field->getDoubleValue();
            break;
            }

        }
        catch( const MDToolkitException& mdte )
        {
            
            GSLOGFDEBUG << "MDToolkitException: " << mdte.what()  << " for " << name \
                        <<" error code:" <<  mdte.getErrorCode() << " type" << type << std::endl; 
            if(mdte.getErrorCode() == 1009)
            {
                // empty field still need for missing value
                data[name] = NULL;
            }
        } 
    } // for each field

    if (cb_onmsg_.second)
    {
        GSLOGFDEBUG << "callback with dict:" << cb_onmsg_.first <<endl;
        bp::call_method<void>(cb_onmsg_.second,cb_onmsg_.first.c_str(),data);
    }else{
        GSLOGFINFO << "No callback registgerd for onMessage" <<endl;
    }

}
