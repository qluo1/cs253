FIELD = 'field'
OPERATOR = 'operator'
VALUES = 'validValues'

class ViewCreator:
    '''
        Utility class to create Python representations of Image Live Views.
        @author: Luiz Ribeiro
        @date: 27-01-2016
    '''

    def __init__(self, viewName):
        '''
            Creates a new ImgLive view representation.
            @param viewName (string): The name by which this view will be identified on the server.
            @param objectType (string): The type of object that this view can track. Either order, execution or basket.
            @param fieldInclusion (list(string) or string). The fields that are going to be inspected by this
                view. If a single field is going to be inspected, a string parameter is accepted.
        '''

        self.__viewName = viewName
        self.__filters = []


    def addTypeAndFields(self, objectType, fieldInclusion):
        assert type(objectType) == str

        if type(fieldInclusion) == str:
            fieldInclusion = [fieldInclusion]
        else:
            assert type(fieldInclusion) == list

        self._addSpecialFilter('objectType', [objectType])
        self._addSpecialFilter('fieldInclusion', fieldInclusion)


    def addFilter(self, operator, field, values):
        '''
            Adds a filter to the view.
            @param operator(string): The operator that is going to be used to inspect a field. Valid operators are:
                equals, notEquals, moreThan, lessThan, between, in, notIn, contains, inRange, outOfRange'. This 
                function doesn't validate the operator, this is done by the server receiving the view creation request.
            @param field(string): The complete path, starting from the root of the field to be inspected.
            @param values(list(string)): A list of string of expected values.
        '''
        assert type(values) == list

        newFilter = {
            FIELD: field,
            OPERATOR: operator,
            VALUES: values
        }

        self.__filters.append(newFilter)


    def _addSpecialFilter(self, fieldName, values):
        '''
            Adds a special filter with no operator. For example, objectType and fieldInclusion. You
            should refrain using this method, unless another filter of this kind needs to be used.
            @param fieldName (string): the name of the field to be inspected (eg: objectType)
            @param values (list(string)): the list of values the triggers this filter
        '''
        assert type(values) == list

        newFilter = {
            FIELD: fieldName,
            VALUES: values
        }

        self.__filters.append(newFilter)


    def __str__(self):
        ''' Debugging method the friendly prints the created view '''
        out = 'View [' + self.__viewName + ']\n'
        for filterRule in self.__filters:
            out += str(filterRule) + '\n'

        return out

    def getViewName(self):
        ''' Returns the view name. This method is usually invoked to send a view creation request.'''
        return self.__viewName

    def getViewFilters(self):
        ''' 
            Returns a copy of the filters created so far. This method is usually invoked to send a view 
            creation request. Since a copy is returned, the user can't compromise the internal view representation.
        '''
        return self.__filters[:]

    def __call__(self):
        return (self.getViewName(), self.getViewFilters())

if __name__ == '__main__':
    v = ViewCreator('newView')
    v.addTypeAndFields('order', 'noFields')
    v.addFilter('between', 'orderValue', ['100', '200'])
    print v


    v2 = ViewCreator("atpView")
    v2.addTypeAndFields("order",["previousOrder","transactionalProduct","currentOrder"])
    v2.addFilter("equals","/currentOrde/orderStatusData/isRootOrder",[True])
    v2.addFilter("in","/transactionalProduct/productSummaryInfo/primaryExchangeId",["SYDE"])
    v2.addFilter("in","/currentOrder/orderInstructionData/tradingAlgorithm",["AggressiveMV","ICEBeta",])
    v2.addFilter("moreThan","currentOrder/orderStatusData/createDateTime",["1453899600"])
    print v2

    print v2()





