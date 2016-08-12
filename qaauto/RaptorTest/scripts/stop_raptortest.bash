#!/bin/ksh

typeset pathToThisScript=$(dirname $0)

$pathToThisScript/stop_raptortest_server.bash
sleep 5
$pathToThisScript/stop_raptor.sh
sleep 5
$pathToThisScript/stop_mxsim.sh


return 0

