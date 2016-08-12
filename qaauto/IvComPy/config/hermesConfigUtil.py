"""Helper function to abstract the structure of the Hermes command configuration dictionary"""

# Assumes it has been handed the 'hermes' Map node.
def updateHermesCommands(config, commands):
    if 'configuration' not in config:
        config['configuration'] = {}
    if 'whiteListedCommands' not in config['configuration']:
        config['configuration']['whiteListedCommands'] = []
    if 'allowedHandlers' not in config['configuration']:
        config['configuration']['allowedHandlers'] = []
    if 'commands' not in config['configuration']:
        config['configuration']['commands'] = {}

    for k in commands.keys():
        found = 0
        if k not in config['configuration']['whiteListedCommands']:
            config['configuration']['whiteListedCommands'].append(k)
        else:
            found += 1

        if k not in config['configuration']['allowedHandlers']:
            config['configuration']['allowedHandlers'].append(k)
        else:
            found += 1

        if found != 0:
            print 'hermesCommandHelper.py-W-updateHermesCommands() detected repeat command definition for [' + k + ']'

    config['configuration']['commands'].update(commands)

