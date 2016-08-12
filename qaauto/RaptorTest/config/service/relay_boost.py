import subprocess
import logging
import signal

from time import sleep
from conf import settings

logging.config.dictConfig(settings.LOG_CFG)
log = logging.getLogger(__name__)

def construct_args(config, host):
    args = ['cat', 'relay.py', '|', 'ssh']
    if host == 'tse':
        args.append('gset-tse-q01.tk.eq.gs.com')
    else:
        args.append('gset-jnx-q01.tk.eq.gs.com')
    args += ['python', '-']
    args += ['--incoming-binding-host', config[host]['incoming_binding'][0]]
    args += ['--incoming-binding-port', config[host]['incoming_binding'][1]]
    args += ['--outgoing-connecting-host', config[host]['outgoing_connecting'][0]]
    args += ['--outgoing-connecting-port', config[host]['outgoing_connecting'][1]]
    if 'outgoing_binding' in config[host]:
        args += ['--outgoing-binding-host', config[host]['outgoing_binding'][0]]
        args += ['--outgoing-binding-port', config[host]['outgoing_binding'][1]]

    return args

config = settings.RELAY_CFG

args_tse = construct_args(config, 'tse')
args_jnx = construct_args(config, 'jnx')

proc_tse = subprocess.Popen(args_tse, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
proc_jnx = subprocess.Popen(args_jnx, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

def clean_up():
    log.info('clean_up triggered, stopping relay processes...')
    proc_tse.send_signal(signal.SIGINT)
    proc_jnx.send_signal(signal.SIGINT)
    
    for i in range(10):
        sleep(1)
        ## check if both of them has 
        if proc_tse.poll() is not None and proc_jnx.poll() is not None:
            break
        if i == 9:
            ## SIGINT doesn't work so we have to kill here
            proc_tse.kill()
            proc_jnx.kill()

    (tse_out, tse_err) = proc_tse.communicate()
    (jnx_out, jnx_err) = proc_jnx.communicate()
    log.info('Output from TSE relay: %s' % tse_out)
    log.info('Error from TSE relay: %s' % tse_err)
    log.info('Output from JNX relay: %s' % jnx_out)
    log.info('Error from JNX relay: %s' % jnx_err)
    sys.exit(0)
         
signal.signal(signal.SIGINT, clean_up)

while True:
    sleep(1)
    ## if one of the scripts dies
    if proc_tse.poll() is not None or proc_jnx.poll() is not None:
        clean_up()


