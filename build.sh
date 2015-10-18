#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=diaspora
#OWNCLOUD_VERSION=8.1.3

ARCH=$(dpkg-architecture -qDEB_HOST_GNU_CPU)
if [ ! -z "$1" ]; then
    ARCH=$1
fi

VERSION="local"
if [ ! -z "$2" ]; then
    VERSION=$2
fi

./coin_lib.sh

cp -r ${DIR}/src lib/syncloud-diaspora-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://build.syncloud.org:8111/guestAuth/repository/download

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_ruby_${ARCH}/lastSuccessful/ruby-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_nginx_${ARCH}/lastSuccessful/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_postgresql_${ARCH}/lastSuccessful/postgresql-${ARCH}.tar.gz

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}
cp -r lib ${BUILD_DIR}

cd ${BUILD_DIR}

#mv ${BUILD_DIR}/owncloud/config ${BUILD_DIR}/owncloud/config.orig

mkdir META
echo ${NAME} >> META/app
echo ${VERSION} >> META/version

echo "getting latest diaspora source"
git clone -b master git://github.com/diaspora/diaspora.git
rm -rf diaspora/.git
cd diaspora
cp config/database.yml.example config/database.yml
cp config/diaspora.yml.example config/diaspora.yml

echo "patching"
#patch -p0 < ${DIR}/patches/filemtime.patch

echo "installing libraries"
export PATH=$PATH:${BUILD_DIR}/ruby/bin
export GEM_HOME=${BUILD_DIR}/ruby
${BUILD_DIR}/ruby/bin/gem install bundler
RAILS_ENV=production DB=postgres bin/bundle install --without test development

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
