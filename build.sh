#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

apt-get install -y libgmp3-dev

export TMPDIR=/tmp
export TMP=/tmp

NAME=diaspora

if [ -z "$1" ]; then
    echo "usage: $0 arch [version]"
fi

ARCH=$1

VERSION="local"
if [ ! -z "$2" ]; then
    VERSION=$2
fi

wget --no-check-certificate --progress=dot:giga -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py 2>&1
python /tmp/get-pip.py
pip install coin
apt-get install -y git build-essential

./coin_lib.sh

cp -r ${DIR}/src lib/syncloud-diaspora-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://build.syncloud.org:8111/guestAuth/repository/download

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_ruby_${ARCH}/lastSuccessful/ruby-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_nginx_${ARCH}/lastSuccessful/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_postgresql_${ARCH}/lastSuccessful/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_redis_${ARCH}/lastSuccessful/redis-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_nodejs_${ARCH}/lastSuccessful/nodejs-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_ImageMagick_${ARCH}/lastSuccessful/ImageMagick-${ARCH}.tar.gz

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}
cp -r lib ${BUILD_DIR}

cd ${BUILD_DIR}

#mv ${BUILD_DIR}/owncloud/config ${BUILD_DIR}/owncloud/config.orig

mkdir META
echo ${NAME} >> META/app
echo ${VERSION} >> META/version

cp ${DIR}/config/postgresql/postgresql.conf ${BUILD_DIR}/postgresql/share/postgresql.conf.sample

echo "getting latest diaspora source"
git clone -b stable git://github.com/diaspora/diaspora.git
rm -rf diaspora/.git
cd diaspora
cp ${DIR}/config/diaspora/database.yml config/database.yml
cp ${DIR}/config/diaspora/diaspora.yml config/diaspora.yml

echo "patching"
#patch -p0 < ${DIR}/patches/filemtime.patch

echo "installing libraries"

export PATH=${BUILD_DIR}/ruby/bin:$PATH
export GEM_HOME=${BUILD_DIR}/ruby

DIASPORA_RUBY_CACHE=/tmp/diaspora_ruby_cache
if [ ! -z "$TEAMCITY_VERSION" ]; then
  echo "running under TeamCity, cleaning ruby dependencies cache"
  rm -rf ${DIASPORA_RUBY_CACHE}
fi

if [ -d "$DIASPORA_RUBY_CACHE" ]; then
    echo "using diaspora ruby dependencies cache: ${DIASPORA_RUBY_CACHE}"
    rm -rf ${BUILD_DIR}/ruby
    cp -r ${DIASPORA_RUBY_CACHE} ${BUILD_DIR}/ruby
fi

${BUILD_DIR}/ruby/bin/gem install bundler
DB=postgres bundle update
RAILS_ENV=production DB=postgres bin/bundle install --without test development
rm -rf ${DIASPORA_RUBY_CACHE}
cp -r ${BUILD_DIR}/ruby ${DIASPORA_RUBY_CACHE}

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
