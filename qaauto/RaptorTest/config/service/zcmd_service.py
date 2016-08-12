## setup local python path
import cfg

import zerorpc
import gevent
import os
import logging
import logging.config
import subprocess
import sys

## setting module
from conf import settings
from singleton import SingleInstance
from conf import settings

logging.config.dictConfig(settings.LOG_CFG)
log = logging.getLogger(__name__)

class ZcmdServer(object):
    """ zcmd server
    - handle zcmd request via zerorpc server
    """

    def __init__(self):
        self.server_ = zerorpc.Server(
            methods = {
                settings.ZCMD_API: self.zcmd_request,
            }
        )
        log.info('zcmd server binding: %s' % settings.ZCMD_API_ENDPOINT)
        self.server_.bind(settings.ZCMD_API_ENDPOINT)

    def get_root_path(self):
        root_path = settings.SCRIPT_DIR
        if os.getenv('ZCMD_ROOT_PATH', '') != '':
            root_path = os.getenv('ZCMD_ROOT_PATH', '')
        return root_path


    def zcmd_request(self, component, args):
        assert type(args) == list
        zcmd_script = self.get_zcmd_script(component)
        args = [zcmd_script] + args
        log.info('Calling Zcmd %s: %s' % (component, str(args)))

        p = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        out, err = p.communicate()
        log.info('Zcmd STDOUT: %s' % out)
        log.info('Zcmd STDERR: %s' % err)

        if p.returncode != 0:
            raise Exception('Zcmd return value is %d != 0' % p.returncode)
        #if len(err) != 0:
        #    raise Exception('Zcmd error')
        return out

    def start(self):
        self.server_.run()

    def stop(self):
        self.server_.close()
        
class HKZcmdServer(ZcmdServer):
    def get_zcmd_script(self, component):
        root_path = self.get_root_path()
        if component == 'raptor':
            return root_path + '/zcmd.sh'
        elif component == 'mxsim': 
            return root_path + '/zcmd.sim.sh'
        else:
            raise Exception('Unknown zcmd component %s' % component)

class JPRawZcmdServer(ZcmdServer):
    def get_zcmd_script(self, component):
        root_path = self.get_root_path()
        if component == 'raptor':
            return root_path + '/zcmd.sh'
        elif component == 'mxsim':
            return root_path + '/zcmd_mxsim-ahd.sh'
        else:
            raise Exception('Unknown zcmd component %s' % component)

def run_as_service():
    import signal
    single_instance_lock = SingleInstance('zcmd_service')

    if settings.INSTANCE == 'HK':
        zcmd_service = HKZcmdServer()
    elif settings.INSTANCE == 'JP_RAW':
        zcmd_service = JPRawZcmdServer()
    else:
        raise Exception('Unknown INSTANCE: %s', settings.INSTANCE)

    def trigger_shutdown():
        log.info('signal SIGINT received, stopping zcmd service')
        zcmd_service.stop()
        log.info('zcmd service stopped, exiting...')
        
    log.info('setting up signal for SIGINT...')
    gevent.signal(signal.SIGINT, trigger_shutdown)

    log.info('running zcmd_service for [%s]...' % os.getenv('SETTINGS_MODULE'))
    zcmd_service.start()
    log.info('zcmd_service stopped cleanly')

if __name__ == '__main__':
    import os
    BASE_DIR = os.getenv('BASE_DIR')
    os.chdir(BASE_DIR)
    run_as_service()
