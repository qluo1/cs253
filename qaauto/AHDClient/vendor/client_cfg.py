import logging

CFGOld = {
    'remoteIp':'10.100.193.36',
    'remotePort': 9233,
    'localIp':'162.98.40.243',
    'localPort': 12002,
    'vsNum': 'VS0021',
    'hbtInterval': 10,
    'hbtTimeout': 60,
    'participantCode': '11560',
    'logLevel': logging.INFO,
    'bindWaitTime': 60,
    }

# Connect to sim (uat-secondary) over NATing
CFG_sim_NAT = {
#CFG = {
    'remoteIp':'3.3.3.1',
    'remotePort': 9445,
    'localIp':'10.147.72.38',
    'localPort': 19450,
    'vsNum': 'VS0026',
    'hbtInterval': 10,
    'hbtTimeout': 60,
    'participantCode': '11560',
    'logLevel': logging.INFO,
    'bindWaitTime': 60,
    }
# Connect to TSE over NATing
#CFG_tse_NAT = {
CFG = {
    'remoteIp':'3.3.3.2',
    'remotePort': 10001,
    'localIp':'2.2.2.2',
    'localPort': 11002,
    'vsNum': 'D61A02',
    'hbtInterval': 10,
    'hbtTimeout': 60,
    'participantCode': '11560',
    'logLevel': logging.INFO,
    'bindWaitTime': 60,
    }
