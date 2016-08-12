import catalog
import hermes
import hermesConfigUtil

def configure():
	om2Catalog = catalog.servercatalog
        om2Catalog['client-datastream-config'] = { 'channel': 'hermes-a', 'applicationid': 'hermes' }
        om2Catalog['server-datastream-config'] = { 'channel': 'hermes-a', 'catalog': [ 'catalog' ], 'applicationids': [ 'hermes' ] }

	config = {
		'catalog': om2Catalog,
		'channels': {
			'hermes-a': { 'connect-to': [ { 'host': 'localhost', 'port': 10012 } ] },
		},
		'server-request-managers': {
			'FUTNYQA-A': {
			    'channel': 'hermes-a',
			    'catalog': [ 'HermesCommand', 'HermesCommandResult', 'HermesCommandArgument', ],
			    'applicationids': [ 'hermes' ],
			    'auto-indicate-availability-load': 100,
			},
                },
		'hermes': {
                        'request-manager-name': 'FUTNYQA-A',
                },
	}

        # Set up some sample Hermes commands.
        hermesConfigUtil.updateHermesCommands(config['hermes'], hermes.getCommands()) 

        return config
