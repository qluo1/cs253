#!/bin/bash

typeset pathToThisScript=$(dirname $0)

typeset parentDir=$pathToThisScript/..

$pathToThisScript/stop_raptortest.bash

echo "Deleting logs and data ..."
if [ -d $parentDir/logs ]; then
    rm -rf $parentDir/logs/*
fi
if [ -d $parentDir/log ]; then
    rm -rf $parentDir/log/*
fi
if [ -d $parentDir/db ]; then
    rm -rf $parentDir/db/*
fi
if [ -d $parentDir/data ]; then
    rm -rf $parentDir/data/*
fi

$pathToThisScript/start_raptor.sh
$pathToThisScript/start_mxsim.sh

# Start test server after raptor finish initialization
sleep 5
$pathToThisScript/run_raptortest_server.bash
sleep 2
$pathToThisScript/run_raptortest.bash

