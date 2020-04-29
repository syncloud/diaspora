#!/bin/bash -xe


DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=ruby
VERSION=2.4.1
PREFIX=${DIR}/build

echo "building ${NAME}"

command curl -sSL https://rvm.io/mpapis.asc | gpg2 --import -
command curl -sSL https://rvm.io/pkuczynski.asc | gpg2 --import -

#useradd -p ruby ruby

rm -rf ${PREFIX}
mkdir ${PREFIX}

curl -sSL https://get.rvm.io | bash -s stable --path ${PREFIX}
source ${PREFIX}/scripts/rvm
rvm install ${VERSION} --movable

rm /etc/rvmrc
rm /etc/profile.d/rvm.sh

rm -rf ${DIR}/${NAME}.tar.gz

cp -r ${PREFIX}/rubies/${NAME}-${VERSION} ${PREFIX}/ruby
mv ${PREFIX}/ruby/bin/ruby ${PREFIX}/ruby/bin/ruby.bin
cp -r ${DIR}/bin  ${PREFIX}/ruby
cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libyaml* ${PREFIX}/ruby/lib
cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libssl*.so* ${PREFIX}/ruby/lib
cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libcrypto.so* ${PREFIX}/ruby/lib
cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libcurl.so* ${PREFIX}/ruby/lib
cp --remove-destination /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgnutls*.so* ${PREFIX}/ruby/lib

#echo "remove incompatible lib"
#rm -rf ${PREFIX}/ruby/lib/libdl.so"

echo "original libs"
ldd ${PREFIX}/ruby/bin/ruby.bin

export LD_LIBRARY_PATH=${PREFIX}/ruby/lib

echo "embedded libs"
ldd ${PREFIX}/ruby/bin/ruby.bin

ldd ${PREFIX}/ruby/lib/libcurl.so