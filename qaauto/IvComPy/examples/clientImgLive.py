'''
    Author: Luiz Ribeiro (Melbourne Technology Division)
    January, 2015
'''

import os
import sys
import inspect
from threading import Thread

# getting paths
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_DIR = os.path.join(CUR_DIR,"config")
PARENT_DIR = os.path.dirname(CUR_DIR)

LOG_DIR = os.path.join(CUR_DIR, "logs")
LOG_CONF = os.path.join(CFG_DIR, 'logConfig.gslog')
LOG_NAME = 'imageLiveClientLog'

# timeout for joinning the IvComManager thread. If it is joined too soon
# after its creation, it MAY cause the client to deadlock.
TIMEOUT = 5

# adding IvComPy path to sys
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# registering config script to import it 
if CFG_DIR not in sys.path:
    sys.path.append(CFG_DIR)

from IvComPy import *
from client import configure


class ImageLiveClient:
    
    def __init__(self, clients, logName, logConf=LOG_CONF, logPath=LOG_DIR):
        
        self.manager = IvComPyManager()
    
        # configure log dumping file
        if not self.manager.setuplog(logConf, logName, logPath):
            raise EnvironmentError('Failed to initialize the log file.')

        # load client data
        if not self.manager.initJson(clients):
            raise EnvironmentError('Failed to load clients configuration data.')

        # the example uses just the single imglive server on the config file
        self.clientName = self.manager.getImageLiveClientNames[0]
        if len(clients) < 1:
            raise EnvironmentError('Make sure that the configuration file specified at least one node ' + 
                                    'on [image-live-clients]')
    
        print 'Demo client: %s' % self.clientName
        # subscribe a simple filter into this server
        imgClient = self.manager.getImageLiveClient(self.clientName)
        imgClient.registerCallbacks(self, 'onNotify', 'onEvent')

        # first try to create a invaid filter (The only valid symbols for this test are IBM, AAPL, HPQ)
        invalidFilter = {'symbol': ['GOOG']}
        success = imgClient.requestViewCreation('invalidDemo', invalidFilter)
        print 'Attempted to subscribe an invalid filter into the server. Succeded? %r' % success
   
        newFilter = {'symbol': ['HPQ']}
        success = imgClient.requestViewCreation('viewDemo', newFilter)
        print 'Attempted to subscribe an valid filter into the server. Succeded? %r' % success

        # running the client into a new thread
        self.clientThread = Thread(target=self.manager.run)
        self.clientThread.start()
        if not self.clientThread.isAlive():
            raise RuntimeError("Failed to create client thread.")
        
        self.received = 0

   
    def onNotify(self, args):

        # Notice that it takes a while for the server to process the requests (update/cancel), so it is
        # normal to receive some "noise" messages that don't reflect the requested changes

        print 'onNotify invoked. Reason: %s. Message: %s' % (args['event'], args['message']['text'])
        
        if self.received == 0:
            updatedFilter = {
                'symbol' : ['AAPL']
            }
    
            imgClient = self.manager.getImageLiveClient(self.clientName)
            print 'Replaced symbol IBM for AAPL. Succeeded? %r' % imgClient.requestViewUpdate('viewDemo', updatedFilter)
        
        
        if self.received == 3:
            imgClient = self.manager.getImageLiveClient(self.clientName)
            print 'Removig filter for AAPL. Succeeded? %r' % imgClient.requestViewCancel('viewDemo')
        

        self.received += 1


    def onEvent(self, args):
        if args['reason'] != None:
            print 'onEvent invoked. The view %s triggered the event %s. Reason: %s.' \
                    % (args['viewName'], args['event'], args['reason'])
        else:
            print 'onEvent invoked. The view %s triggered the event %s.' % (args['viewName'], args['event'])

        if args['event'] == 'onClearAllRecords':
            print 'Server has unregistered the view.' 
    

    def stop(self):
        '''
            Tries to terminate the client thread. This method may fail if its invoked
            too soon after initializing the IvCom manager thread (aka. invoking the run() metod).
            This function waits TIMEOUT seconds for the child thread to join. In case of
            timeout the application has to be forcely terminated, as Python waits for all threads
            to finish before leaving.

            @returns bool: True if the client thread stopped successfully. False otherwise.
        '''
    
        self.manager.stop()
        self.clientThread.join(TIMEOUT)
        return not self.clientThread.isAlive()
    

def loadClientConf():
    '''
        Loads client configuration from script (py dict) and returns as a JSON (string)
    '''

    import json
    return json.dumps(configure())


if __name__ == '__main__':
    from time import sleep
    
    client = ImageLiveClient(loadClientConf(), LOG_NAME, LOG_CONF, LOG_DIR)
    print '----------------------------'
    print 'Client running. CTRL+C quits'
    print '----------------------------\n'
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass
    print 'Main loop ended'
    print 'Server stopped? %r' % client.stop()
    
