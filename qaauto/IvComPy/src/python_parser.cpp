/*
 * Author: Luiz Ribeiro (Melbourne Technology Division)
 * January, 2016
 */

#ifndef SYMBOL___
#define SYMBOL___

#include <boost/python.hpp>
#include <list>

using namespace std;
namespace bp = boost::python;

/* Exception class to signalize failure upon conversion */
class BadPyCast: public exception {
private:
	string msg;
public:
	BadPyCast(string msg) : msg(msg) {}
	~BadPyCast() throw() {}
	const char *what() const throw() { return this->msg.c_str(); }
};


/*
 * Casts a Python pointer (to a unknown-type object) into a C++ typed object 
 * @template T: the boost handler that contains a C++ representation of the Python object to which @pyObj is 
 * 	going to be converted into
 * @param pyObj: the Python object to be converted
 * @param boostHandler: the interface which will allow manipulation of the Python object (This is the output parameter)
 * @returns bool: true if the conversion was successful, false otherwise.
 */
template<typename T>
bool convertPyInto(bp::object pyObj, T& boostHandler) {
	bp::extract<T> extractor (pyObj);
	if (!extractor.check())
		return false;

	boostHandler = extractor();
	return true;
}


/* Converts a Python list pointer into a C++ list
 * @template T: the C++ type of the elements that the destination list will contain
 * @param pyList: the Python list
 * @param destinationObj: the C++ list obtained after conversion
 * @returns bool: true if the conversion was successful.
 */
template<typename T> 
bool getListFromPyList(bp::list pyList, list<T>& destinationObject) {
    list<T> output;
    T extracted;
    int size = bp::len(pyList);

    for (int i=0; i<size; i++) {
        if (!(convertPyInto<T>(pyList[i], extracted)))
            return false;

        output.push_back(extracted);
    }

    destinationObject = output;
    return true;
}

#endif
