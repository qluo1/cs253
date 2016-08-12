#ifndef IVCOMPYDICT_H
#define IVCOMPYDICT_H

#include <Python.h>
#include <boost/python.hpp>
#include <boost/python/dict.hpp>
#include <IvComMessage.hpp>

namespace bp = boost::python;
/**
 * IvCom message to python dict, rely on boost::python::dict for seamless conversion.
 * 
 * for RoutedMessage, if messageData field is in Iv format, will extracted as pydict.
 * 
 * python dict to IvCom message. note: python dict must be string NO unicode!!
 *
 */
class IvComPyDictDecoder
{
public:
    // convert ivcom message to python dict
    static bool ivComToPyDict(const IvComMessage& message, bp::dict& out);
    // convert python dict to ivcom message with table specified
    static bool pyDictToIvCom(const IvComCatalogManager* manager, const bp::dict& in, IvComMessage& out);
};
#endif
