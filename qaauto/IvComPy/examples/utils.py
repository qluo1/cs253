import collections

def convert(data):
    '''
	    Recursivelly converts all strings in a dictionary from Unicode prior
	    to sending them to IvCom.

	    @param data (dict): the dictionary to be converted.
    '''

    if isinstance(data, basestring):
	return str(data)
    elif isinstance(data, collections.Mapping):
	return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
	return type(data)(map(convert, data))
    else:
	return data

