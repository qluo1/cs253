#!/bin/bash
CUR_DIR=${PWD##}

## download
wget http://nexus.software.services.gs.com:8080/nexus/content/repositories/sam/nginx__inc//release-1.10.0.tar/1.10.0/release-1.10.0.tar-1.10.0.tar.gz

tar xvf release-1.10.0.tar-1.10.0.tar.gz

if [ -e nginx-release-1.10.0 ]; then
    cd $CUR_DIR/nginx-release-1.10.0
    #echo $CUR_DIR/nginx-release-1.10.0/auto/configure
    #echo ${PWD}
    #`$CUR_DIR/nginx-release-1.10.0/auto/configure --prefix=. --with-debug > /dev/null 2>&1` 
    `$CUR_DIR/nginx-release-1.10.0/auto/configure --prefix=. > /dev/null 2>&1` 

    `make -j 4 > /dev/null 2>&1 `

    if [ -e objs/nginx ];then
        mv objs/nginx ${CUR_DIR}
        echo "build ngix 1.10.0 successful"
        cd $CUR_DIR
        `rm -r nginx-release-1.10.0`
        `rm release-1.10.0.tar-1.10.0.tar.gz`
    else
        echo "build nginx failed"
    fi
else
    echo "unexpected: download/extract nginx failed";
    return -1
fi


