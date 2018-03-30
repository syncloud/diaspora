#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

export TMPDIR=/tmp
export TMP=/tmp

NAME=diaspora
DIASPORA_VERSION=0.7.3.1
DIASPORA_ARCHIVE=v${DIASPORA_VERSION}
DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

if [[ -z "$2" ]]; then
    echo "usage $0 version installer"
    exit 1
fi

ARCH=$(uname -m)
VERSION=$1
INSTALLER=$2

if [ -n "$DRONE" ]; then
    echo "running under drone, removing coin cache"
    rm -rf ${DIR}/.coin.cache
fi

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

cd ${DIR}
coin --to lib py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin --to lib py https://pypi.python.org/packages/ec/6b/b3fcd16215e3742c67a740fbb313e78f38741da5e40ee97681c9f9472aa5/syncloud-lib-27.tar.gz#md5=fa82721a7da75f570cd4ba8b4ce7a779
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

cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp -r ${DIR}/lib ${BUILD_DIR}

cd ${BUILD_DIR}

mkdir META
echo ${NAME} >> META/app
echo ${VERSION} >> META/version

echo "getting latest diaspora source"
wget --progress=dot:giga https://github.com/diaspora/diaspora/archive/v${DIASPORA_VERSION}.tar.gz 2>&1 -O ${BUILD_DIR}/v${DIASPORA_VERSION}.tar.gz
tar xzf v${DIASPORA_VERSION}.tar.gz
rm v${DIASPORA_VERSION}.tar.gz
mv ${BUILD_DIR}/diaspora-${DIASPORA_VERSION} ${BUILD_DIR}/diaspora


cd diaspora

sed -i "s/.*config.force_ssl =.*/  config.force_ssl = false/g" config/environments/production.rb

echo "installing libraries"
apt -y install binutils-gold
update-alternatives --install "/usr/bin/ld" "ld" "/usr/bin/ld.gold" 20
update-alternatives --install "/usr/bin/ld" "ld" "/usr/bin/ld.bfd" 10

update-alternatives --config ld

ld --version

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

export RAILS_ENV=production
${BUILD_DIR}/diaspora/bin/bundle install --deployment --without test development --with postgresql
rm -rf ${DIASPORA_RUBY_CACHE}

if [ -z "$DRONE" ]; then
   cp -r ${BUILD_DIR}/ruby ${DIASPORA_RUBY_CACHE}
fi

find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l
find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l -exec readlink {} \;
find ${BUILD_DIR}/diaspora/vendor/bundle/ruby/ -type l -exec sh -c 'cp --remove-destination $(readlink {}) {}' \; || true

ls -la ${BUILD_DIR}/ruby/lib

cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpq.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgmp*.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgssapi_krb5.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libldap_r-2.4.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpthread.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libc.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libdl.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libkrb5.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libk5crypto.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libcom_err.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libkrb5support.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libkeyutils.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libresolv.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/liblber-2.4.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libsasl2.so* ${BUILD_DIR}/ruby/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libz.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libp11-kit.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libtasn1.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libnettle.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libhogweed.so* ${BUILD_DIR}/ruby/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libffi.so* ${BUILD_DIR}/ruby/lib

ls -la ${BUILD_DIR}/ruby/lib

ldd ${BUILD_DIR}/ruby/lib/libpq.so

${BUILD_DIR}/diaspora/bin/rake assets:precompile
rm config/diaspora.yml
rm config/database.yml

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
