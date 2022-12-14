#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# we need this to be version agnostic
RPMFILE=`ls ${SCRIPT_DIR}/../../release/hypercane-*.x86_64.rpm`
RPMFILEBASE=`basename $RPMFILE`

echo starting container
docker run --name centos8test --privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro -d -p 8000:8000 local/c8-systemd

echo installing MongoDB
docker cp ${SCRIPT_DIR}/centos8/mongodb-org.repo centos8test:/etc/yum.repos.d/mongodb-org.repo
docker exec -it centos8test dnf install -y mongodb-org
docker exec -it centos8test systemctl enable mongod.service
docker exec -it centos8test systemctl start mongod.service

echo copying $RPMFILE to container /root/ directory
docker cp $RPMFILE centos8test:/root

echo installing Hypercane
docker exec -it centos8test dnf install -y /root/${RPMFILEBASE}

echo starting Hypercane
docker exec -it centos8test systemctl start hypercane-django.service

echo starting shell
docker exec -it centos8test /bin/bash
