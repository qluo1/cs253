#include <boost/python.hpp>
#include "IvComPyDict.h"
#include <GSLog.H>
#include <GsCuBase64Encoder.hpp>
#include <IvComMessageIterator.hpp>
#include <IvComMessageFormatter.hpp>

typedef GsCuHashMap<std::string, std::string> MetaDataMap;

// convert ivcom to python dict
bool IvComPyDictDecoder::ivComToPyDict(const IvComMessage& message, bp::dict&  out)
{
    if( message.isMisformatted())
    {
        GSLOGFSEVERE << "ivcom message is misformatted" <<endl;
        return false;
    }

    int tableId = message.tableId();

    IvComMessageIterator it(message);

    while(it.next())
    {

        const char* columnName = it.column().columnName();
        switch(it.column().column()->columnType_)
        {
            case VAR_BINARY2:
                {
                    const unsigned char* data = NULL;
                    unsigned int size;
                    it.getValueData(data,size);
                    out[columnName] = GsCuBase64Encoder::encode(data,size);
                }
                break;
            case VAR_STR:
                {
                    const char* value = NULL;
                    if(it.get(value))
                    {
                        out[columnName] = value;
                    }
                }
                break;
            case VAR_BYTE:
            case VAR_SBYTE:
            case VAR_SHORT:
            case VAR_USHORT:
            case VAR_INT:
            case VAR_UINT:
            case VAR_BOOL:
                {
                    int value;
                    if(it.get(value))
                    {
                        out[columnName] = value;
                    }
                }
                break;
            case VAR_LONGLONG:
            case VAR_ULONGLONG:
                {
                    int64_t value;
                    if(it.get(value))
                    {
                        out[columnName] = value;
                    }
                }
                break;
            case VAR_DBL:
            case VAR_FLOAT:
                {
                    double value;
                    if(it.get(value))
                    {
                        out[columnName] = value;
                    }
                }
                break;
            case VAR_SUBTABLE:
                {
                    IvComMessageListIterator messageList;
                    if(it.get(messageList))
                    {
                        bp::list col;

                        while (messageList.next())
                        {
                            IvComMessageIterator nestedMessageIterator;

                            if(!messageList.get(nestedMessageIterator))
                            {
                                GSLOGFSEVERE << "Couldn't get nested message data for [" << columnName << ']' << endl;
                                return false;
                            }
                            int nestedTableId = nestedMessageIterator.tableId();
                            IvComTable nestedTable = nestedMessageIterator.table().manager()->getTable(nestedTableId);

                            if(!nestedTable.isValid())
                            {
                                GSLOGFSEVERE << "Invalid nested table [" << nestedTableId << "]" <<endl;
                                return false;
                            }

                            IvComMessage nestedMessage(nestedTable);
                            nestedMessage.setData(nestedMessageIterator.data(),nestedMessageIterator.size());

                            bp::dict outitem;

                            if (!ivComToPyDict(nestedMessage,outitem))
                            {
                                GSLOGFSEVERE << "Convert nested message for sub table [" << nestedTableId << "]" <<endl;
                                return false;
                            }

                            
                            // append to list
                            col.append(outitem);

                        }
                        
                        MetaDataMap map = it.column().column()->getMetaData();
                        MetaDataMap::iterator itr = map.find("dictionaryType");
                        if (itr != map.end() && itr->second == "struct" && bp::len(col) == 1)
                        {
                            // this is structure not a list
                            out[columnName] = col[0];

                        }else{
                            // assign list to out pydict
                            out[columnName] = col;
                        }
                    }

                }
                break;
            default:
                {
                    GSLOGFSEVERE << "unknown data type [" << it.column().column()->columnType_ << "[ encountered" <<endl;
                    return false;
                }
        }// switch

    } // while

    // handle RoutedMessage or MessageWrapperData , decode messageData as structure
    if (tableId == 54 || tableId == 71)
    {
        IvComTable tbl = message.table();
        int tableId,msgFormat;
        message.get(tbl.getColumn("tableId"),tableId);
        message.get(tbl.getColumn("messageFormat"),msgFormat);
        // manager from original message
        IvComCatalogManager* pCat = message.manager();

        GSLOGFDEBUG <<"Routed/WrapperData tableId: " << tableId << " msgFormat:" << msgFormat << endl;

        // only handle Iv format
        if (msgFormat == 2)
        {
            IvComColumn col_data = tbl.getColumn("messageData");
            const unsigned char* data = NULL;
            unsigned int size;
            if (!message.get(col_data,data,size))
            {
                GSLOGFSEVERE << "parse RoutedMessage for messageData failed" << message <<endl;
                return false;

            }
            IvComMessage msg(tableId,pCat,data,size);
            if (msg.isMisformatted())
            {
                GSLOGFSEVERE << "extracted messageData is misformatted!" << msg <<endl;
                return false;
            }
            // convert back to  pydict
            
            boost::python::dict routedOut;

            if (!ivComToPyDict(msg,routedOut))
            {
                GSLOGFSEVERE << "convert routed message to pydict failed " <<endl;
                return false;
            }
            // set as dict
            out["messageData"] = routedOut;
            // enrich table name here
            out["tableName"] = pCat->getTableName(tableId);

        }// msgFormat == 2
    }

    // handle TransactionElement 
    if (tableId ==382 )
    {
        IvComTable tbl = message.table();
        int tableId;
        message.get(tbl.getColumn("tableId"),tableId);

        // manager from original message
        IvComCatalogManager* pCat = message.manager();

        GSLOGFDEBUG <<"TransactionElement record tableId: " << tableId << endl;
        //
        const unsigned char* data = NULL;
        unsigned int size;
        IvComColumn col_data = tbl.getColumn("recordData");
        if (!message.get(col_data,data,size))
        {
            GSLOGFSEVERE << "parse TransactionElement for recordData failed" << message <<endl;
            return false;
        }
        IvComMessage msg(tableId,pCat,data,size);
        if (msg.isMisformatted())
        {
            GSLOGFSEVERE << "extracted messageData is misformatted!" << msg <<endl;
            return false;
        }
        // convert back to  pydict
        boost::python::dict recordData;

        if (!ivComToPyDict(msg,recordData))
        {
            GSLOGFSEVERE << "convert TransactionElement record to pydict failed " <<endl;
            return false;
        }
        // set as dict
        out["recordData"] = recordData;
    }

    return true;
}

// internal helper recusively called
bool dictToIvCom(const IvComCatalogManager* manager,const bp::dict& in, IvComMessageFormatter & formatter)
{
    IvComTable table = formatter.table();
    bp::list keys = in.keys();
    int tableId = table.tableId();

    for (int i=0; i < bp::len(keys);i++)
    {
        
        bp::extract<string> x (keys[i]);
        if (!x.check())
        {
            GSLOGFASTFSEVERE << "Could not extract key string" << endl;
            return false;
        }
        const string& columnName = x();
        GSLOGFDEBUG << "dict KEY: " << columnName <<endl;
        IvComColumn column = table.getColumn(columnName.c_str());
        if (!column.isValid())
        {
            GSLOGFINFO << "skip not valid column [" << columnName << "]" <<endl;
            continue;
        }

        switch(column.column()->columnType_)
        {

            case VAR_BINARY2:
                {
                    if (tableId == 54 && columnName == "messageData")
                    {
                        GSLOGFDEBUG << "handle Routed Message for message data [" << columnName << "]" <<endl;
                        // routed message actually is an embeded subtable
                        bp::extract<bp::dict> x(in[columnName]);
                        if (!x.check())
                        {
                            GSLOGFASTFSEVERE << "Failed to extract routed message as pydict: ["  << columnName << "]" <<endl;
                            return false;
                        }
                        //
                        bp::extract<int> y(in["tableId"]);
                        if (!y.check())
                        {
                            GSLOGFASTFSEVERE <<"Failed to extract routed message tableId field  for [" <<columnName << "]" <<endl;
                            return false;
                        }

                        //// work out subtable
                        bp::dict data = x();
                        int subTableId = y();

                        IvComTable table = manager->getTable(subTableId);
                        IvComMessageFormatter subTableFormatter = IvComMessageFormatter(table);
                        GSLOGFDEBUG << "message data as table [" << table.tableName() << "]" <<endl;

                        if(!dictToIvCom(manager,data,subTableFormatter))
                        {
                            GSLOGFASTFSEVERE << "Fail to convert message data into ivcom for ,[" << columnName << "]" <<endl;
                            return false;
                        }

                        const unsigned char* pdata = NULL;
                        unsigned int size;
                        subTableFormatter.getData(pdata,size);

                        if(!formatter.set(column,pdata,size))
                        {
                            GSLOGFASTFSEVERE << "Could not set [" << columnName << " ] as binary value for routed message" <<endl;
                            return false;
                        }

                        
                    }else{ 
                        bp::extract<string> x(in[columnName]);
                        if (!x.check())
                        {
                            // skip binary data if can't extracted.
                            GSLOGFASTFSEVERE << "Fail to extract binary data for column [" << columnName << "]" <<endl;
                            continue;
                        }
                        string val = x(); //bp::extract<string>(in[columnName]);
                        string value = GsCuBase64Encoder::decode(val);

                        if(!formatter.set(column,value.data(),value.size()))
                        {
                            GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as binary value from [" << val << "]" << endl;
                            return false;
                        }


                    }

                }
                break;
            case VAR_STR:
                {
                    bp::extract<string> x(in[columnName]);
                    if (!x.check())
                    {
                        GSLOGFASTFSEVERE << "Fail to extract string from column[" <<columnName << "]" <<endl;
                        return false;
                    }
                    
                    string value = x(); 
                    if(!formatter.set(column,value))
                    {
                        GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as string value from [" << value << "]" << endl;
                        return false;
                    }

                }
                break;
            case VAR_BYTE:
            case VAR_SBYTE:
            case VAR_SHORT:
            case VAR_USHORT:
            case VAR_INT:
            case VAR_UINT:
                {
                    bp::extract<int> x (in[columnName]);
                    if (!x.check())
                    {
                        GSLOGFASTFSEVERE << "Fail to extract int for column [" <<columnName << "]" <<endl;
                        return false;
                    }
                    int value = x();
                    if(!formatter.set(column,value))
                    {
                        GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as int value from [" << value << "]" << endl;
                        return false;
                    }

                }
                break;
            case VAR_LONGLONG:
            case VAR_ULONGLONG:
                {
                    int64_t value = bp::extract<int64_t>(in[columnName]);
                    if(!formatter.set(column,value))
                    {
                        GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as LONG value from [" << value << "]" << endl;
                        return false;
                    }

                }
                break;
            case VAR_BOOL:
                {
                    bool value = bp::extract<bool>(in[columnName]);
                    if(!formatter.set(column,value))
                    {
                        GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as bool value from [" << value << "]" << endl;
                        return false;
                    }
                }
                break;
            case VAR_DBL:
                {
                    double value = bp::extract<double>(in[columnName]);
                    if(!formatter.set(column,value))
                    {
                        GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as double value from [" << value << "]" << endl;
                        return false;
                    }

                }
                break;
            case VAR_FLOAT:
                {
                    float value = bp::extract<float>(in[columnName]);
                    if(!formatter.set(column,value))
                    {
                        GSLOGFASTFSEVERE << "Could not set [" << columnName << "] as float value from [" << value << "]" << endl;
                        return false;
                    }

                }
                break;
            case VAR_SUBTABLE:
                {
                    const char* subTableName = column.column()->subTable_.c_str();
                    IvComTable subTable = manager->getTable(subTableName);
                    GSLOGFDEBUG << "subtable [" << subTableName << "]" << endl;
                    MetaDataMap map = column.column()->getMetaData();
                    MetaDataMap::iterator itr = map.find("dictionaryType");
                    if (itr != map.end() && itr->second == "struct")
                    {
                        // this is structure not a list
                        // 
                        bp::extract<bp::dict> x (in[columnName]);
                        if (!x.check())
                        {
                            GSLOGFASTFSEVERE << "Could not extract dict for column [" << columnName << "]" <<endl;
                            return false;
                        }
                        bp::dict value = x();

                        if(!formatter.startMessageList(column))
                        {
                            GSLOGFASTFSEVERE << "Could not start message list for column [" << columnName << "]"  << endl;
                            return false;
                        }
                        if(!formatter.startMessage())
                        {
                            GSLOGFASTFSEVERE << "Could not start message for column [" << columnName << "]"  << endl;
                            return false;
                        }

                        IvComMessageFormatter subTableFormatter = IvComMessageFormatter(subTable);
                        if (!dictToIvCom(manager,value,subTableFormatter))
                        {
                            GSLOGFASTFSEVERE << "convert subtable [" << subTableName << "] from column " << columnName << " failed " <<endl;
                            return false;
                        }

                        if(!formatter.append(subTableFormatter))
                        {
                            GSLOGFASTFSEVERE << "Could not append [" << columnName << "] as subtable from [" << columnName << "]" << endl;
                            return false;
                        }
                        if (!formatter.endMessage())
                        {
                            GSLOGFASTFSEVERE << "Could not end message for  [" << columnName << "]" << endl;
                            return false;
                        }

                        if(!formatter.endMessageList())
                        {
                            GSLOGFASTFSEVERE << "Could not end  message list for column [" << columnName << "]"  << endl;
                            return false;
                        }


                    }else{
                        //  extract list
                        //
                        bp::extract<bp::list> x(in[columnName]);
                        if (!x.check())
                        {
                            GSLOGFASTFSEVERE << "Could not extract list for column [ " << columnName << "]" <<endl;
                            return false;
                        }

                        bp::list values = x();

                        if(!formatter.startMessageList(column))
                        {
                            GSLOGFASTFSEVERE << "Could not start message list for column [" << columnName << "]"  << endl;
                            return false;
                        }

                        for (int i=0;i< bp::len(values);i++)
                        {
                            bp::extract<bp::dict> x (values[i]);
                            if (!x.check())
                            {
                                GSLOGFASTFSEVERE << "Could not extract dict from list of column [ "<< columnName << "]" <<endl;
                                return false;
                            }
                            bp::dict value = x();

                            if(!formatter.startMessage())
                            {
                                GSLOGFASTFSEVERE << "Could not start message for column [" << columnName << "]"  << endl;
                                return false;
                            }

                            IvComMessageFormatter subTableFormatter = IvComMessageFormatter(subTable);
                            if (!dictToIvCom(manager, value,subTableFormatter))
                            {
                                GSLOGFASTFSEVERE << "convert subtable [" << subTableName << "] from column " << columnName << " failed " <<endl;
                                return false;
                            }

                            if(!formatter.append(subTableFormatter))
                            {
                                GSLOGFASTFSEVERE << "Could not append [" << columnName << "] as subtable from [" << columnName << "]" << endl;
                                return false;
                            }
                            if (!formatter.endMessage())
                            {
                                GSLOGFASTFSEVERE << "Could not end message for  [" << columnName << "]" << endl;
                                return false;
                            }

                        }

                        if(!formatter.endMessageList())
                        {
                            GSLOGFASTFSEVERE << "Could not end  message list for column [" << columnName << "]"  << endl;
                            return false;
                        }

                    }
                }
                break;
            default:
                {
                    GSLOGFASTFSEVERE << "Unknown data type [" << column.column()->columnType_ <<"] encountered" <<endl;
                    return false;
                }

        }// switch

    }//for loop

    return true;
}


// convert python dict into IvMessage with table already specified.
bool IvComPyDictDecoder::pyDictToIvCom(const IvComCatalogManager* manager, const bp::dict& in, IvComMessage& message)
{
    if(message.isMisformatted())
    {
        GSLOGFSEVERE << "IvMessage is misformatted" <<endl;
        return false;
    }

    IvComCatalog* catalog = const_cast<IvComCatalogManager*>(manager)->catalog();
    int tableId = message.tableId();
    IvComTable table =  catalog->getTable(tableId);
    // check table is valid
    if (!table.isValid())
    {
        GSLOGFASTFSEVERE << "Table [" << tableId << "] is not valid" << endl;
        return false;
    }

    // 
    IvComMessageFormatter formatter(table);

    if (!dictToIvCom(manager,in,formatter))
    {
        GSLOGFASTFSEVERE << "Convert dict to ivcom failed " <<endl;
        return false;
    }

    message.setData(formatter.data(),formatter.size());
    // check message 
    if(message.isMisformatted())
    {
        GSLOGFASTFSEVERE << "Convert dict to ivmessage is misformatted" <<endl;
    }

    return true;
}

