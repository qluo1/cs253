import catalog
import hermes
import hermesConfigUtil
import hermesCatalog
import copy

the_channel = "hermesstandalone"
the_appId = "hermes"

def configure():
    om2Catalog = copy.deepcopy(catalog.servercatalog)

    ## include hermesCatalog here
    om2Catalog['tables'].update(hermesCatalog.hermesCatalog['tables'])
    om2Catalog['client-datastream-config'] = { 'channel': the_channel, 'applicationid': the_appId}
    om2Catalog['server-datastream-config'] = { 'channel': the_channel, 'catalog': [ 'catalog' ], 'applicationids': [ the_appId] }

    config = {
        'catalog': om2Catalog,
        'channels': {
            the_channel: 
                ## server channel
                { 
                  'accept-on' : [ { 'port': 10013} ] ,
                  'connecter-accepter': 'true'
                },
        },
        'server-request-managers': {
            'hermes-test-request': {
                'channel': the_channel,
                'catalog': [ 'HermesCommand', 'HermesCommandResult', 'HermesCommandArgument', ],
                'applicationids': [ the_appId],
                'auto-indicate-availability-load': 100,
            },
        },
        'hermes': {
                'request-manager-name': 'hermes-test-request',
        },
        ## required
        'ivcom' : {
         'application-id' : the_appId,
         'application-type' : 'ivcom-hermesstandalone',
        },

    }

    # Set up some sample Hermes commands.
    hermesConfigUtil.updateHermesCommands(config['hermes'], hermes.getCommands())

    return config

