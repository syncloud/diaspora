#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=diaspora
#requires ruby 2.2.2
#DIASPORA_VERSION=0.6.4.1
DIASPORA_VERSION=0.6.3.0
DIASPORA_ARCHIVE=v${DIASPORA_VERSION}

if [ -z "$1" ]; then
    echo "usage: $0 version"
fi

ARCH=$(uname -m)
VERSION=$1

./coin_lib.sh

cp -r ${DIR}/src lib/syncloud-diaspora-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/ruby-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postgresql-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/redis-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/nodejs-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/ImageMagick-${ARCH}.tar.gz

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
wget --progress=dot:giga https://github.com/diaspora/diaspora/archive/v${DIASPORA_VERSION}.tar.gz 2>&1 -O ${BUILD_DIR}/v${DIASPORA_VERSION}.tar.gz
tar xzf v${DIASPORA_VERSION}.tar.gz
rm v${DIASPORA_VERSION}.tar.gz
mv ${BUILD_DIR}/diaspora-${DIASPORA_VERSION} ${BUILD_DIR}/diaspora
cd diaspora
cp ${DIR}/config/diaspora/database.yml config/database.yml
cp ${DIR}/config/diaspora/diaspora.yml config/diaspora.yml

sed -i "s/.*config.force_ssl =.*/  config.force_ssl = false/g" config/environments/production.rb

echo "installing libraries"

export PATH=${BUILD_DIR}/ruby/bin:${BUILD_DIR}/nodejs/bin:$PATH
export GEM_HOME=${BUILD_DIR}/ruby

DIASPORA_RUBY_CACHE=${DIR}/.ruby.cache
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
export RAILS_ENV=production
bin/bundle install --deployment --without test development --with postgresql
rm -rf ${DIASPORA_RUBY_CACHE}

if [ -z "$TEAMCITY_VERSION" ]; then
   cp -r ${BUILD_DIR}/ruby ${DIASPORA_RUBY_CACHE}
fi

find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l
find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l -exec readlink {} \;
find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l -exec sh -c 'cp --remove-destination $(readlink {}) {}' \; || true

bin/rake assets:precompile

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
