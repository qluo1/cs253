#!/bin/bash

PID=`ps -ef | grep python | grep ahd_service | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -SIGINT $PID
    echo "ahd_service is killed..."
else
    echo "ahd_service is not running..."
fi

PID=`ps -ef | grep python | grep zcmd_service | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -SIGINT $PID
    echo "zcmd_service is killed..."
else
    echo "zcmd_service is not running..."
fi

PID=`ps -ef | grep python | grep dc_service | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -SIGINT $PID
    echo "dc_service is killed..."
else
    echo "dc_service is not running..."
fi

PID=`ps -ef | grep python | grep relay_boost | grep -v grep | awk '{print $2}'`
if [ "x$PID" != "x"  ]; then
    kill -SIGINT $PID
    echo "relay is killed..."
else
    echo "relay is not running..."
fi
