#!/bin/bash

PID=`ps -ef | grep python | grep fix_service | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -2 $PID
    echo "fix_service is killed..."
else
    echo "fix_service is not running..."
fi

PID=`ps -ef | grep python | grep zcmd_service | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -2 $PID
    echo "zcmd_service is killed..."
else
    echo "zcmd_service is not running..."
fi

PID=`ps -ef | grep python | grep dc_service | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -2 $PID
    echo "dc_service is killed..."
else
    echo "dc_service is not running..."
fi
