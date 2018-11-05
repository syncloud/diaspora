#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [ "$#" -lt 6 ]; then
    echo "usage $0 redirect_user redirect_password redirect_domain version release device_host"
    exit 1
fi

DOMAIN=$3
VERSION=$4
RELEASE=$5
DEVICE_HOST=$6

APP=diaspora
GECKODRIVER=0.14.0
FIREFOX=52.0
ARCH=$(uname -m)

if [ $ARCH == "x86_64" ]; then
    SNAP_ARCH=amd64
else
    SNAP_ARCH=armhf
fi

ARCHIVE=${APP}_${VERSION}_${SNAP_ARCH}.snap
APP_ARCHIVE_PATH=$(realpath "$ARCHIVE")

cd ${DIR}

echo ${APP_ARCHIVE_PATH}

if [ "$ARCH" == "x86_64" ]; then
    TEST_SUITE="verify.py test-ui.py"
else
    TEST_SUITE=verify.py
fi

cd ${DIR}

attempts=100
attempt=0
DOCKER_SSH="sshpass -p syncloud ssh -o StrictHostKeyChecking=no root@${DEVICE_HOST}"

set +e
$DOCKER_SSH date
while test $? -gt 0
do
  if [ $attempt -gt $attempts ]; then
    exit 1
  fi
  sleep 3
  echo "Waiting for SSH $attempt"
  attempt=$((attempt+1))
  $DOCKER_SSH date
done
set -e

sshpass -p syncloud scp -o StrictHostKeyChecking=no install-${INSTALLER}.sh root@${DEVICE_HOST}:/installer.sh

$DOCKER_SSH /installer.sh ${RELEASE}

#fix dns
device_ip=$(getent hosts ${DEVICE_HOST} | awk '{ print $1 }')
echo "$device_ip $APP.$DOMAIN.syncloud.info" >> /etc/hosts

cat /etc/hosts
pip2 install -r ${DIR}/dev_requirements.txt
xvfb-run -l --server-args="-screen 0, 1024x4096x24" py.test -x -s ${TEST_SUITE} --email=$1 --password=$2 --domain=$DOMAIN --release=$RELEASE --app-archive-path=${APP_ARCHIVE_PATH} --device-host=${DEVICE_HOST}