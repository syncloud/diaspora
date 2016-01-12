#!/bin/bash -x

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

apt-get install -y libgmp3-dev

export TMPDIR=/tmp
export TMP=/tmp

NAME=diaspora
DIASPORA_VERSION=0.5.4.0
DIASPORA_ARCHIVE=v${DIASPORA_VERSION}

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
wget --progress=dot:giga https://github.com/diaspora/diaspora/archive/v${DIASPORA_VERSION}.tar.gz 2>&1 -O ${BUILD_DIR}/v${DIASPORA_VERSION}.tar.gz
tar xzf v${DIASPORA_VERSION}.tar.gz
rm v${DIASPORA_VERSION}.tar.gz
mv ${BUILD_DIR}/diaspora-${DIASPORA_VERSION} ${BUILD_DIR}/diaspora
cd diaspora
cp ${DIR}/config/diaspora/database.yml config/database.yml
cp ${DIR}/config/diaspora/diaspora.yml config/diaspora.yml

#sed -i 's#Backbone.history.start({pushState: true});#Backbone.history.start({pushState: true, root: "/diaspora/"});#g' app/assets/javascripts/app/app.js
#sed -i 's#"users/sign_up"#"diaspora/users/sign_up"#g' app/assets/javascripts/app/router.js
#sed -i "/get 'login' => redirect('\/users\/sign_in')/a \ \ get 'diaspora\/users\/sign_up'   => 'users\/registrations#new',   :as => :new_user_registration_path" config/routes.rb
#sed -i "/config.cache_classes = true/a \ \ config.relative_url_root = '/diaspora'" config/environments/production.rb
#sed -i "/config.cache_classes = true/a \ \ config.action_controller.relative_url_root = '/diaspora'" config/environments/production.rb
sed -i "s/.*config.force_ssl =.*/  config.force_ssl = false/g" config/environments/production.rb

echo "patching"
#patch -p0 < ${DIR}/patches/filemtime.patch

echo "installing libraries"

export PATH=${BUILD_DIR}/ruby/bin:${BUILD_DIR}/nodejs/bin:$PATH
export GEM_HOME=${BUILD_DIR}/ruby
#export RAILS_RELATIVE_URL_ROOT='/diaspora'

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
export DB=postgres
export RAILS_ENV=production

bin/bundle install --without test development
rm -rf ${DIASPORA_RUBY_CACHE}

if [ -z "$TEAMCITY_VERSION" ]; then
   cp -r ${BUILD_DIR}/ruby ${DIASPORA_RUBY_CACHE}
fi

find ${BUILD_DIR}/ruby/ -type l

find ${BUILD_DIR}/ruby/ -type l -exec readlink {} \;

find ${BUILD_DIR}/ruby/ -type l -exec sh -c 'cp --remove-destination $(readlink {}) {}' \;

#bin/rake assets:precompile

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
