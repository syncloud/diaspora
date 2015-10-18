#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$1" || -z "$2" || -z "$3" || -z "$4" || -z "$5" || -z "$6" ]]; then
    echo "usage $0 redirect_user redirect_password redirect_domain release app_version app_arch"
    exit 1
fi

./docker.sh

apt-get install sshpass
SCP="sshpass -p syncloud scp -o StrictHostKeyChecking=no -P 2222"

${SCP} ${DIR}/../diaspora-${5}-${6}.tar.gz root@localhost:/

pip2 install -U pytest

py.test -s verify.py --email=$1 --password=$2 --domain=$3 --release=$4 --app-version=$5 --arch=$6

${SCP} root@localhost:/opt/data/platform/log/\* .