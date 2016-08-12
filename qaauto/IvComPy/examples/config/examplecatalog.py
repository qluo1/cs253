
# rcsid "$Header: /home/cvs/eqtech/cep/src/ivcom/config/examplecatalog.py,v 1.5 2014/02/26 18:53:46 krielq Exp $"

# For example purposes, we're going to make some modifications to the server-side catalog, which
# will be used by server.py and serverReverse.py
servercatalog = {
        'subject' : 'catalog',
        'tables' : {
            # The datastream protocol supports catalog downloading on the fly to support server upgrading.
            # Here, we've created a new version of the existing TextMessage table and added a new field.
            #
            # You can see the catalog downloading in action by connecting exampleivcomdatastreamserver
            # to an exampleivcomdatastreamclient and watching the table download happen during connection
            # initialization.
            'TextMessage' : {
                'id': 9,
                'version' : 3,
                'publishable': 'true',
                'columns': {
                    'text': { 'index': 0, 'type': 'string' },
                    'blob': { 'index': 1, 'type': 'binary' },
                    'text1': { 'index': 2, 'type': 'string' },
                    'text2': { 'index': 3, 'type': 'string' },
                    'text3': { 'index': 4, 'type': 'string' },
                    'text4': { 'index': 5, 'type': 'string' },
                    'text5': { 'index': 6, 'type': 'string' },
                    'text6': { 'index': 7, 'type': 'string' },
                    'text7': { 'index': 8, 'type': 'string' },
                    'text8': { 'index': 9, 'type': 'string' },
                    'text9': { 'index': 10, 'type': 'string' },
                    'text10': { 'index': 11, 'type': 'string' },
                    'text11': { 'index': 12, 'type': 'string' },
                    'text12': { 'index': 13, 'type': 'string' },
                    'text13': { 'index': 14, 'type': 'string' },
                    'text14': { 'index': 15, 'type': 'string' },
                    'text15': { 'index': 16, 'type': 'string' },
                    'int1': { 'index': 17, 'type': 'int' },
                    'int2': { 'index': 18, 'type': 'int' },
                    'int3': { 'index': 19, 'type': 'int' },
                    'int4': { 'index': 20, 'type': 'int' },
                    'int5': { 'index': 21, 'type': 'int' },
                    'int6': { 'index': 22, 'type': 'int' },
                    'int7': { 'index': 23, 'type': 'int' },
                    'int8': { 'index': 24, 'type': 'int' },
                    'int9': { 'index': 25, 'type': 'int' },
                    'int10': { 'index': 26, 'type': 'int' },
                    'int11': { 'index': 27, 'type': 'int' },
                    'int12': { 'index': 28, 'type': 'int' },
                    'int13': { 'index': 29, 'type': 'int' },
                    'int14': { 'index': 30, 'type': 'int' },
                    'int15': { 'index': 31, 'type': 'int' },
                    'nestedInTextMessage': { 'index': 32, 'type': 'table', 'tablename': 'NestedInTextMessage', },
                    'uint': { 'index': 33, 'type': 'uint' },
                    # The following fields are new in version 3
                    'newfield' : { 'index' : 34, 'type' : 'string' },
                    'newenum' : { 'index' : 35, 'type' : 'int', 'enum' : 'ExampleEnum' },
                    }
            },
            'NestedInTextMessage' : {
                    'id': 1012,
                    'columns': {
                            'text': { 'index': 0, 'type': 'string' },
                            'blob': { 'index': 1, 'type': 'binary' },
                            'text1': { 'index': 2, 'type': 'string' },
                            'int': { 'index': 3, 'type': 'int' },
                    }
            }
            # It's also possible to add entirely new tables to the catalog download. While the client may not have
            # code to do anything with these tables, they'll be recognized and logged descriptively.
            # Try uncommenting this table, and the corresponding commented lines in server.py to try it out.
            #'NewTable' : {
            #    'id': 1014,
            #    'publishable': 'true',
            #    'columns': {
            #        'blob': { 'index': 0, 'type': 'binary' },
            #    },
            #}
        }
}

clientcatalog = {
        'tables' : {
            # The request manager protocol supports catalog uploading on the fly as well.
            # Here, we've created a new version of the existing NestedInTextMessage table and added a new field.
            'NestedInTextMessage' : {
                    'id': 1012,
                    'version' : 2,
                    'columns': {
                            'text': { 'index': 0, 'type': 'string' },
                            'blob': { 'index': 1, 'type': 'binary' },
                            'text1': { 'index': 2, 'type': 'string' },
                            'int': { 'index': 3, 'type': 'int' },
                            'somethingnew' : { 'index' : 4, 'type' : 'string' },
                    }
            }
        }
}

servercatalogEnums = {
        'enums' : {
                'ExampleEnum' : {
                    'version' : 1,
                    'values' : {
                        'INVALID' : 0,
                        'SomeValue' : 1,
                        'SomeOtherValue' : 2,
                    }
                }
        }
}
