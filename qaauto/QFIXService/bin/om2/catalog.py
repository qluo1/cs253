
# rcsid "$Header: /home/cvs/eqtech/cep/src/ivcom/config/catalog.py,v 1.28 2014/11/19 12:34:25 ananas Exp $"

# This file contains table definitions for IvCom infrastructure protocol messages.
import copy

# This function should be used to combine two table definition dictionaries
# It expects a base dictionary of definitions and an extra dictionary of definitions
# and combines the extra definitions directly into the base
def combineCatalogs(base, extra):
    base['tables'].update(extra['tables'])
    rcsids = extra.get('rcsids')
    if rcsids:
        base['rcsids'].extend(rcsids)

basecatalog = {
	'subject': 'catalog',
	'tables': {
		# This table is used to transmit the definitions of other tables
		# When 'column-meta-fields' and 'table-meta-fields' was added we did not increment the version
		# number, this was intentional, changing this would require that client have the new version
		'catalog': {
			'id': 0,
			'publishable': 'false',
			'columns': {
				'table':             { 'index': 0, 'type': 'string' },
				'tableid':           { 'index': 1, 'type': 'int' },
				'index':             { 'index': 2, 'type': 'int' },
				'type':              { 'index': 3, 'type': 'int' },
				'name':              { 'index': 4, 'type': 'string' },
				'subtable':          { 'index': 5, 'type': 'string' },
				'width':             { 'index': 6, 'type': 'int' },
				'always-present':    { 'index': 7, 'type': 'int' },
				'aliases':           { 'index': 8, 'type': 'table', 'tablename': 'column-alias' },
				'column-meta-fields':{ 'index': 9, 'type': 'table', 'tablename': 'meta-field' },
				'table-meta-fields': { 'index': 10, 'type': 'table', 'tablename': 'meta-field' },
			},
		},
		# This table is used for service discovery for the datastream service
		'datastream': {
			'id': 1,
			'publishable': 'true',
			'columns': {
				'datastreamname':          { 'index': 0, 'type': 'string' },
				'applicationid':           { 'index': 1, 'type': 'string' },
				'instance':                { 'index': 2, 'type': 'string' },
				'group':                   { 'index': 3, 'type': 'string' },
				'messageid':               { 'index': 4, 'type': 'string' },
				'callbackid':              { 'index': 5, 'type': 'binary', 'width': 17 },
				'load':                    { 'index': 6, 'type': 'int', },
				'require-processing-acks': { 'index': 7, 'type': 'int', },
				'require-receipt-acks':    { 'index': 8, 'type': 'int', },
				'tables':                  { 'index': 9, 'type': 'table', 'tablename': 'table-version' },
				'enums':                   { 'index': 10, 'type': 'table', 'tablename': 'table-version' },
			},
		},
		# This table is used for service discovery for the request response service
		'requestmanager': {
			'id': 2,
			'publishable': 'false',
			'columns': {
				'requestmanagername':   { 'index': 0, 'type': 'string' },
				'applicationid':        { 'index': 1, 'type': 'string' },
				'instance':             { 'index': 2, 'type': 'string' },
				'group':                { 'index': 3, 'type': 'string' },
				'callbackid':           { 'index': 4, 'type': 'binary', 'width': 17 },
				'load':                 { 'index': 5, 'type': 'int', },
				'require-receipt-acks': { 'index': 6, 'type': 'int', },
				'tables':               { 'index': 7, 'type': 'table', 'tablename': 'table-version' },
				'enums':                { 'index': 8, 'type': 'table', 'tablename': 'table-version' },
			},
		},
		# This table is used for transmitting messages from datastream servers to datastream clients
		'envelope': {
			'id': 3,
			'publishable': 'false',
			'columns': {
				'messageid': { 'index': 0, 'type': 'string' },
				'posdup':    { 'index': 1, 'type': 'int' },
				'table':     { 'index': 2, 'type': 'ushort' },
				'message':   { 'index': 3, 'type': 'binary' },
			},
		},
		# This table is used for transmitting acknowledgements from datastream clients to datastream servers
		'return-receipt': {
			'id': 4,
			'publishable': 'false',
			'columns': {
				'messageid':  { 'index': 0, 'type': 'string' },
				'callbackid': { 'index': 1, 'type': 'binary', 'width': 17 },
			},
		},
		# Request/Response clients use the message to send requests to Request/Response servers
		'request': {
			'id': 5,
			'publishable': 'false',
			'columns': {
				'requestid':           { 'index': 0, 'type': 'uint', 'always-present': 'true'  },
				'posdup':              { 'index': 1, 'type': 'ubyte', 'always-present': 'true'  },
				'table':               { 'index': 2, 'type': 'ushort', 'always-present': 'true'  },
				'require-receipt-ack': { 'index': 3, 'type': 'bool', 'always-present': 'true'  },
				'callbackid':          { 'index': 4, 'type': 'binary', 'width': 17, 'always-present': 'true' },
				'messagelength':       { 'index': 5, 'type': 'ushort', 'always-present': 'true' },
				'messagelengthWide':   { 'index': 6, 'type': 'uint', 'always-present': 'true' },
			},
		},
		# Request/Response servers use the message to send responses to Request/Response clients
		'response': {
			'id': 6,
			'publishable': 'false',
			'columns': {
				'requestid':         { 'index': 0, 'type': 'uint' , 'always-present': 'true' },
				'table':             { 'index': 1, 'type': 'ushort', 'always-present': 'true'  },
				'callbackid':        { 'index': 2, 'type': 'binary', 'width': 17, 'always-present': 'true'},
				'messagelength':     { 'index': 3, 'type': 'ushort', 'always-present': 'true' },
				'messagelengthWide': { 'index': 4, 'type': 'uint', 'always-present': 'true' },
			},
		},
		# This table describes the version of a table that an application has been configured with
		'table-version': {
			'id': 7,
			'publishable': 'true',
			'columns': {
				'name':    { 'index': 0, 'type': 'string' },
				'version': { 'index': 1, 'type': 'int', },
			},
		},
		# This table is used for service discovery
		'discovery': {
			'id': 8,
			'publishable': 'false',
			'columns': {
				'callbackid': { 'index': 0, 'type': 'binary', 'width': 17 },
				'available':  { 'index': 1, 'type': 'int', },
			},
		},
		# This table describes an alias for a column
		'column-alias': {
			'id': 12,
			'publishable': 'false',
			'columns': {
				'alias': { 'index': 0, 'type': 'string' },
			},
		},
		# This table is used for enum synchronization between server and client
		'enum': {
			'id': 15,
			'publishable': 'false',
			'columns': {
				'name':              { 'index': 0, 'type': 'string' },
				'values':            { 'index': 1, 'type': 'table', 'tablename': 'enum-value' },
				'meta-fields':       { 'index': 2, 'type': 'table', 'tablename': 'meta-field' },
			},
		},
		'enum-value': {
			'id': 16,
			'publishable': 'false',
			'columns': {
				'name':              { 'index': 0, 'type': 'string' },
				'value':             { 'index': 1, 'type': 'int'   },
			},
		},
		# Image Live Server Table definitions
		'image-live': {
			'id': 1000,
			'publishable': 'false',
			'columns': {
				'imageLiveName':           { 'index': 0, 'type': 'string' },
				'applicationid':           { 'index': 1, 'type': 'string' },
				'instance':                { 'index': 2, 'type': 'string' },
				'group':                   { 'index': 3, 'type': 'string' },
				'recordId':                { 'index': 4, 'type': 'string' },
				'recordVersion':           { 'index': 5, 'type': 'int', },
				'eventId':                 { 'index': 6, 'type': 'string' },
				'callbackid':              { 'index': 7, 'type': 'binary', 'width': 17 },
				'load':                    { 'index': 8, 'type': 'int', },
				'require-processing-acks': { 'index': 9, 'type': 'int', },
				'require-receipt-acks':    { 'index': 10, 'type': 'int', },
				'tables':                  { 'index': 11, 'type': 'table', 'tablename': 'table-version' },
				'enums':                   { 'index': 12, 'type': 'table', 'tablename': 'table-version' },
			},
		},
		'image-live-return-receipt': {
			'id': 1001,
			'publishable': 'false',
			'columns': {
				'viewName':      { 'index': 0, 'type': 'string' },
				'recordId':      { 'index': 1, 'type': 'string' },
				'recordVersion': { 'index': 2, 'type': 'int', },
				'eventId':       { 'index': 3, 'type': 'string' },
				'callbackid':    { 'index': 4, 'type': 'binary', 'width': 17 },
			},
		},
		'create-view': {
			'id': 1002,
			'publishable': 'true',
			'columns': {
				'callbackid' : { 'index': 0, 'type': 'binary', 'width': 17 },
				'viewName'   : { 'index': 1, 'type': 'string' },
				'viewFilters': { 'index': 2, 'type': 'table', 'tablename': 'view-filter' },
			},
		},
		'view-filter': {
			'id': 1003,
			'publishable': 'true',
			'columns': {
				'filterName'      : { 'index': 0, 'type': 'string' },
				'filterParameters': { 'index': 1, 'type': 'table', 'tablename': 'filter-parameter' },
			},
		},
		'filter-parameter': {
			'id': 1004,
			'publishable': 'true',
			'columns': {
				'filterParameter' : { 'index': 0, 'type': 'string' },
			},
		},
		'view-cancel': {
			'id': 1005,
			'publishable': 'true',
			'columns': {
				'callbackid': { 'index': 0, 'type': 'binary', 'width': 17 },
				'viewName'  : { 'index': 1, 'type': 'string' },
			},
		},
		'view-creation-failed': {
			'id': 1006,
			'publishable': 'true',
			'columns': {
				'type'     : { 'index': 0, 'type': 'int' },
				'viewName' : { 'index': 1, 'type': 'string' },
				'failureReason' : { 'index': 2, 'type': 'string' },
			},
		},
		'view-creation-successful': {
			'id': 1007,
			'publishable': 'true',
			'columns': {
				'type'     : { 'index': 0, 'type': 'int' },
				'viewName' : { 'index': 1, 'type': 'string' },
			},
		},
		'view-notification': {
			'id': 1008,
			'publishable': 'true',
			'columns': {
				'type'       : { 'index': 0, 'type': 'int' },
				'payLoad'    : { 'index': 1, 'type': 'binary' },
				'tableId'    : { 'index': 2, 'type': 'int' },
				'viewName'   : { 'index': 3, 'type': 'string' },
				'recordId'   : { 'index': 4, 'type': 'string' },
				'version'    : { 'index': 5, 'type': 'int' },
				'eventId'    : { 'index': 6, 'type': 'string' },
				'batchAction' : { 'index': 7, 'type': 'ubyte' },
			},
		},
		'view-initialization-commence': {
			'id': 1009,
			'publishable': 'true',
			'columns': {
				'viewName' : { 'index': 0, 'type': 'string' },
			},
		},
		'view-initialization-complete': {
			'id': 1010,
			'publishable': 'true',
			'columns': {
				'viewName' : { 'index': 0, 'type': 'string' },
			},
		},
		'view-clear-all': {
			'id': 1011,
			'publishable': 'true',
			'columns': {
				'viewName'  : { 'index': 0, 'type': 'string' },
			},
		},

		# Tables for Metadata exchange start at 1500
		'meta-field': {
		        'id': 1500,
			'publishable': 'false',
			'columns': {
			        'field': { 'index': 0, 'type': 'string' },
			        'value': { 'index': 1, 'type': 'string' },
			},
		},                

		# IvComMessage representation of a Service Discovery Proxy IvCom configuration update.
		# -Each 'service-discovery-config-node' table encountered represents one IvComConfigurationPatch.
		# -An IvComConfigurationPatch can be either a Map, List or Leaf(i.e. string) node with an action:
		#     1) Map nodes will have the 'configurationNodes' column set, and NOT have 
		#        the 'configurationNodeIsList' or 'configurationNodeValue' columns set. 
		#        A Map node may have the 'configurationNodeKey' column set, it means this Map 
		#        node is an entry in a previous parent Map node, otherwise it is an entry in
		#        a previous parent List node.  NOTE: The root Map node has NO parent node.
		#     2) List nodes will have the 'configurationNodes' and 'configurationNodeIsList' columns
		#        set, and NOT have the 'configurationNodeValue' column set.
		#        A List node may have the 'configurationNodeKey' column set, it means this List 
		#        node is an entry in a previous parent Map node, otherwise it is an entry in
		#        a previous parent List node.
		#     3) Leaf(i.e. string) nodes will have the 'configurationNodeValue' column set, and 
		#        NOT have the 'configurationNodes' or 'configurationNodeIsList' columns set.
		#        A Leaf node may have the 'configurationNodeKey' column set, it means this Leaf 
		#        node is an entry in a previous parent Map node, otherwise it is an entry in
		#        a previous parent List node.
		# -An action can have one of three values:
		#     1) 0: This indicates that this node is newly added and should be added to the existing configuration
		#        as part of this update.
		#     2) 1: This indicates that this node is modified and should be merged in the existing configuration
		#     3) 2: This indicates that the current node must be deleted from the existing configuration
		#        as part of this update. When action=2, the 'configurationNodeValue' must be set to an empty string "",
		#        and NOT have the 'configurationNodes' or 'configurationNodeIsList' columns set.
		'service-discovery-config-node': {
			'id': 1501,
			'publishable': 'true',
			'columns': {
				'configurationNodeIsList':   {'index': 0, 'type': 'int'},
				'configurationNodeKey':   {'index': 1, 'type': 'string'},
				'configurationNodeValue': {'index': 2, 'type': 'string'},
				'configurationNodes': {'index': 3, 'type': 'table', 'tablename': 'service-discovery-config-node'},
				'action': {'index': 4, 'type': 'int'}
			},
		},
		# Sent by a Service Discovery Proxy to update client application IvCom configurations.
		# The 'configurationSnapshotDataNode' column holds the root Map node of the updated configuration.
		# The 'configurationSnapshotType' column describes the type of the patch:
		#   0: Complete configuration snapshot
		#   1: Delta configuration patch
		'service-discovery-update': {
			'id': 1502,
			'publishable': 'true',
			'columns': {
				'uniqueApplicationId':   {'index': 0, 'type': 'string'},
				'serviceDiscoveryDomainName': {'index': 1, 'type': 'string'},
				'serverConfigSnapshotDigest': {'index': 2, 'type': 'string'},
				'configurationSnapshotDataNode': {'index': 3, 'type': 'table', 'tablename': 'service-discovery-config-node'},
				'configurationSnapshotType': {'index': 4, 'type': 'int'}
			},
		},
		# embedded in the create-dynamic-service-request its used to specify dynamic configuration options
		# from the client to the server.
		'dynamic-configuration-variable': {
			'id': 1503,
			'publishable': 'true',
			'columns': {
				'dynamicConfigurationVariable': { 'index': 0, 'type': 'string' },
				'dynamicConfigurationValue':    { 'index': 1, 'type': 'string' },
			},
		},                
		# Sent by an IvCom client to a server to request the create of dynamic service
		'create-dynamic-service-request': {
			'id': 1504,
			'publishable': 'true',
			'columns': {
				'dynamicServiceName':                   {'index': 0, 'type': 'string' },
				'dynamicServiceType':                   {'index': 1, 'type': 'string' },
				'dynamicConfigurationVariablesList':    {'index': 2, 'type': 'table', 'tablename': 'dynamic-configuration-variable'},
			},
		},
	},
    'rcsids' : [ "$Id: catalog.py,v 1.28 2014/11/19 12:34:25 ananas Exp $" ],
}

servercatalog = copy.deepcopy(basecatalog)
# This table is used for unit performance testing
servercatalog = {
	'subject': 'catalog',
	'tables' : {
        'TextMessage' : {
            'id': 9,
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
    }
}
