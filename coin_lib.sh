#!/usr/bin/env bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [ ! -z "$TEAMCITY_VERSION" ]; then
  echo "running under TeamCity, cleaning coin cache"
  rm -rf /tmp/coin.cache
fi

if [ ! -d lib ]; then
  mkdir lib
fi

rm -rf lib/*

cd lib

coin py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin py https://pypi.python.org/packages/source/s/syncloud-app/syncloud-app-0.38.tar.gz
cd ..