import os
import catalog
import hermesCatalog
import string

def hermesChannels(config, instanceInfo):
        """
        instanceInfo format: <instanceName>,<channelName>,<instanceHost>,<instancePort>,<instanceGroups>
        instanceGroups can have multiple groups separated by colon.
        E.g. QAGSCOPTA-Primary,hermes-primary-QAGSCOPTA,qagscopta-1.qa.om2.services.gs.com,4802,PT-OM2:NY-OM2
        """

        instanceInfo = string.strip(instanceInfo)
        instanceArray = instanceInfo.split(',')
        instanceName = instanceArray[0].strip(" ")
        channelName = instanceArray[1].strip(" ")
        instanceHost = instanceArray[2].strip(" ")
        instancePort = instanceArray[3].strip(" ")
        instanceGroups = instanceArray[4].strip(" ")

        config[ 'client-request-managers' ][ instanceName ] = {
                'channel': channelName,
                'catalog': [ 'HermesCommand', 'HermesCommandResult', 'HermesCommandArgument', ],
                'applicationid': 'hermes',
                'request-failure-interval': 300,
                'auto-indicate-availability-load': 100,
        }
        config[ 'channels' ][ channelName ] = {
                ## client channel
                 'connect-to': [ { 'host': instanceHost, 'port': instancePort } ] 
        }

        instanceGroupsList = instanceGroups.split(':')
        for instanceGroup in instanceGroupsList:
            instanceGroup = instanceGroup.strip(" ")
            if instanceGroup not in config[ 'hermes' ][ 'groups' ]:
                config[ 'hermes' ][ 'groups' ][ instanceGroup ]=[]
            config[ 'hermes' ][ 'groups' ][ instanceGroup ].append(instanceName)


def configure():
    hermesCollectorCatalog = catalog.basecatalog
    hermesCollectorCatalog['tables'].update(hermesCatalog.hermesCatalog['tables'])

    hermesCollectorPort = os.getenv('hermesCollectorPort')
    replayLimit = os.getenv('replayLimit')

    config = {
        'catalog': hermesCollectorCatalog,
        'channels': {},
        'client-request-managers': {},
        'hermes': {
            'gui-accept-on-port': hermesCollectorPort,
            'replay-limit': replayLimit,
            'groups': {},

        },
        'ivcom': {
                'application-id' : os.getenv('instance'),
                'application-type' : 'hermescollector',
        },
    }

    instanceList = os.getenv('instanceList')
    instances = instanceList.split(';')
    for instanceInfo in instances:
        instanceInfo = instanceInfo.strip(" ")
        if instanceInfo != '':
            hermesChannels(config, instanceInfo)

    return config;


if __name__ == "__main__":
    """
      unit test
    """
    config = configure()

    from pprint import pprint
    pprint(config)



