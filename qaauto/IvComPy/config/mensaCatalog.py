mensaCatalog = {
	'tables': {
		'FIXmessage': {
			'id': 519, 
			'version': 1, 
			'publishable': 'true', 
			'columns': {
				'fixLineId':        { 'index': 0, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '32'},
				                      ],
				                    },
				'timestamp':        { 'index': 1, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'rdbRemapDataType' , 'value' : 'datetime:yyyy-MM-dd HH:mm:ss.SSS'},
					                  {'field': 'maxStringLength' , 'value' : '23'},
				                      ],
				                    },
				'avgPx':            { 'index': 2, 'type': 'double', 
				                      'meta-fields': [
					                  {'field': 'dictionaryType' , 'value' : 'real'},
				                      ],
				                    },
				'clOrdID':          { 'index': 3, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'cumQty':           { 'index': 4, 'type': 'int', }, 
				'execID':           { 'index': 5, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'execRefID':        { 'index': 6, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'execTransType':    { 'index': 7, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '2'},
				                      ],
				                    },
				'securityIDSource': { 'index': 8, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '3'},
				                      ],
				                    },
				'lastMkt':          { 'index': 9, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '5'},
				                      ],
				                    },
				'lastPx':           { 'index': 10, 'type': 'double', 
				                      'meta-fields': [
					                  {'field': 'dictionaryType' , 'value' : 'real'},
				                      ],
				                    },
				'lastQty':          { 'index': 11, 'type': 'double', 
				                      'meta-fields': [
					                  {'field': 'dictionaryType' , 'value' : 'real'},
				                      ],
				                    },
				'msgSeqNum':        { 'index': 12, 'type': 'int', }, 
				'msgType':          { 'index': 13, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '3'},
				                      ],
				                    },
				'orderID':          { 'index': 14, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'orderQty':         { 'index': 15, 'type': 'double', 
				                      'meta-fields': [
					                  {'field': 'dictionaryType' , 'value' : 'real'},
				                      ],
				                    },
				'ordStatus':        { 'index': 16, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '3'},
				                      ],
				                    },
				'ordType':          { 'index': 17, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '3'},
				                      ],
				                    },
				'origClOrdID':      { 'index': 18, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'possDupFlag':      { 'index': 19, 'type': 'bool', }, 
				'price':            { 'index': 20, 'type': 'double', 
				                      'meta-fields': [
					                  {'field': 'dictionaryType' , 'value' : 'real'},
				                      ],
				                    },
				'securityID':       { 'index': 21, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'senderCompID':     { 'index': 22, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'side':             { 'index': 23, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '3'},
				                      ],
				                    },
				'symbol':           { 'index': 24, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'targetCompID':     { 'index': 25, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'timeInForceFIX':   { 'index': 26, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'rdbAlias' , 'value' : 'timeInForce'},
					                  {'field': 'maxStringLength' , 'value' : '3'},
				                      ],
				                    },
				'listID':           { 'index': 27, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'possResend':       { 'index': 28, 'type': 'bool', }, 
				'onBehalfOfCompID': { 'index': 29, 'type': 'string', 
				                      'meta-fields': [
					                  {'field': 'maxStringLength' , 'value' : '128'},
				                      ],
				                    },
				'raw':              { 'index': 30, 'type': 'string', }, 
			}, 
		}, 
	},

	'rcsids' : [
		'$Header: /home/cvs/eqtech/cep/src/kevlar/sampleApplication/config/sampleDictionary.xml,v 1.3 2010/12/15 23:03:07 gerket Exp $',
		'$Header: /home/cvs/eqtech/cep/src/ivshmdb/config/ivShmDbMetaDictionary.xml,v 1.1 2010/04/08 07:29:02 hironk Exp $',
		'$Header: /home/cvs/eqtech/cep/src/om2/config/omDictionary.xml,v 1.1158 2014/11/18 18:18:18 dasand Exp $',
		'$Header: /home/cvs/eqtech/cep/src/rds-distribution/client/config/rdsDictionary.xml,v 1.198 2014/11/22 02:40:05 yongs Exp $',
	]
}

mensaCatalogEnums = {
	'enums': {
	}
}

