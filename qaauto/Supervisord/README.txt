Supervisord - a process manager and controler
==============================================


## OM2 schedule: SOD  JP Time: 1:30, End 2:30
## OM2 BOC: REINSTATE JP Time: 2:00


## cron jobs on qaauto-s (p2eqtwq@d153578-002) in HK time
## this is 0:30, 0:40 in AU Time.
############# restart on monday 
10 0 * * 1  /home/eqtdata/runtime/qaauto/Supervisord/bin/supervisord -c /home/eqtdata/runtime/qaauto/Supervisord/config/config.cfg

40 0 * * 1-5 /home/eqtdata/runtime/qaauto/Supervisord/bin/control.py > /tmp/daily_restart.log

30 2 * * 1-5 /home/eqtdata/runtime/qaauto/OM2RuleService/bin/run_snapshot_gen.sh > /tmp/daily_snapshot.log

