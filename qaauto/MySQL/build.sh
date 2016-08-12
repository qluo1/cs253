#!/bin/bash
#download extract mysql server
  
MYSQL=mysql-5.6.28-linux-glibc2.5-x86_64
wget http://nexus.software.services.gs.com:8080/nexus/content/repositories/sam/oracle/mysql-5.6.28-linux-glibc2.5-x86_64.tar/5.6.28/"$MYSQL".tar-5.6.28.tar.gz
tar xvf "$MYSQL".tar-5.6.28.tar.gz

rm "$MYSQL"*.tar.gz

CUR_DIR=${PWD}
pushd .

if [ -e $MYSQL ]; then

    cd $MYSQL
    ./scripts/mysql_install_db -ldata ./data
    cp ../conf/my.cnf . 
    popd
    # link bin for conveniene
    ln -s $CUR_DIR/$MYSQL/bin bin 
else
    echo "failed to copy my.cnf"
fi
