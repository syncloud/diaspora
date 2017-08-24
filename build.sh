#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

export TMPDIR=/tmp
export TMP=/tmp

NAME=diaspora
DIASPORA_VERSION=0.6.6.0
DIASPORA_ARCHIVE=v${DIASPORA_VERSION}
DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

if [ -z "$1" ]; then
    echo "usage: $0 version"
fi

ARCH=$(uname -m)
VERSION=$1

if [ -n "$DRONE" ]; then
    echo "running under drone, removing coin cache"
    rm -rf ${DIR}/.coin.cache
fi

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

cd ${DIR}
coin --to lib py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin --to lib py https://pypi.python.org/packages/source/s/syncloud-lib/syncloud-lib-2.tar.gz
coin --to lib py ${DOWNLOAD_URL}/PyYAML-x86_64.tar.gz
cp -r ${DIR}/src lib/syncloud-diaspora-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

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

mkdir META
echo ${NAME} >> META/app
echo ${VERSION} >> META/version

#cp ${DIR}/config/postgresql/postgresql.conf ${BUILD_DIR}/postgresql/share/postgresql.conf.sample

echo "getting latest diaspora source"
wget --progress=dot:giga https://github.com/diaspora/diaspora/archive/v${DIASPORA_VERSION}.tar.gz 2>&1 -O ${BUILD_DIR}/v${DIASPORA_VERSION}.tar.gz
tar xzf v${DIASPORA_VERSION}.tar.gz
rm v${DIASPORA_VERSION}.tar.gz
mv ${BUILD_DIR}/diaspora-${DIASPORA_VERSION} ${BUILD_DIR}/diaspora

cp -r ${DIR}/config ${BUILD_DIR}/config.templates

cd diaspora
#cp ${DIR}/config/diaspora/database.yml config/database.yml
#cp ${DIR}/config/diaspora/diaspora.yml config/diaspora.yml

sed -i "s/.*config.force_ssl =.*/  config.force_ssl = false/g" config/environments/production.rb

echo "installing libraries"

export PATH=${BUILD_DIR}/ruby/bin:${BUILD_DIR}/nodejs/bin:$PATH
export GEM_HOME=${BUILD_DIR}/ruby
export LD_LIBRARY_PATH=${BUILD_DIR}/ruby/lib

DIASPORA_RUBY_CACHE=${DIR}/.ruby.cache
if [ ! -z "$DRONE" ]; then
  echo "running under build serer, cleaning ruby dependencies cache"
  rm -rf ${DIASPORA_RUBY_CACHE}
fi

if [ -d "$DIASPORA_RUBY_CACHE" ]; then
    echo "using diaspora ruby dependencies cache: ${DIASPORA_RUBY_CACHE}"
    rm -rf ${BUILD_DIR}/ruby
    cp -r ${DIASPORA_RUBY_CACHE} ${BUILD_DIR}/ruby
fi

cp ${DIR}/config/diaspora/diaspora-dummy.yml config/diaspora.yml
cp ${DIR}/config/diaspora/database-dummy.yml config/database.yml

${BUILD_DIR}/ruby/bin/gem install bundler
${BUILD_DIR}/ruby/bin/bundle update rake -j 1

export RAILS_ENV=production
${BUILD_DIR}/ruby/bin/bundle install --deployment --without test development --with postgresql
rm -rf ${DIASPORA_RUBY_CACHE}

if [ -z "$DRONE" ]; then
   cp -r ${BUILD_DIR}/ruby ${DIASPORA_RUBY_CACHE}
fi

find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l
find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l -exec readlink {} \;
find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l -exec sh -c 'cp --remove-destination $(readlink {}) {}' \; || true

cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpq.so* ${BUILD_DIR}/ruby/lib
cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgmp*.so* ${BUILD_DIR}/ruby/lib

${BUILD_DIR}/ruby/bin/rake assets:precompile
rm config/diaspora.yml
rm config/database.yml

ln -s ../../config/diaspora/diaspora.yml config/diaspora.yml
ln -s ../../config/diaspora/database.yml config/database.yml

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
