	
hermesCatalog = {
	'tables': {
		'HermesCommand': {
			'id': 730,
			'columns': {
				'requestManager': { 'index': 0, 'type': 'string' },
				'cmd': { 'index': 1, 'type': 'string' },
				'args': { 'index': 2, 'type': 'string' },
				'handle': { 'index': 3, 'type': 'string' },	
				'guiId': { 'index': 4, 'type': 'int' },	
				#'argumentVector': { 'index': 5, 'type': 'table', 'tablename': 'HermesCommandArgument', },
				'argumentVector': { 'index': 5, 'type': 'table', 'tablename': 'HermesCommandArgument', 
                                'meta-fields': [{'field': 'dictionaryType' , 'value' : 'collection'}]
                    },
				'cmdId': { 'index': 6, 'type': 'int' },
				'userId': { 'index': 7, 'type': 'string' },
			},
		},
		'HermesCommandResult': {
			'id': 731,
			'columns': {
				'requestManager': { 'index': 0, 'type': 'string' },
				'guiId': { 'index': 1, 'type': 'int' },	
				'handle': { 'index': 2, 'type': 'string' },
				'cmd': { 'index': 3, 'type': 'string' },
				'args': { 'index': 4, 'type': 'string' },
				'status': { 'index': 5, 'type': 'string' },
				'message': { 'index': 6, 'type': 'string' },
				'cmdId': { 'index': 7, 'type': 'int' },
			},
		},
		'HermesCommandArgument': {
			'id': 732,
			'columns': {
				'arg': { 'index': 0, 'type': 'string' },
			},
		},

	},
}
