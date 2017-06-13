#!/usr/bin/env bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [ ! -d lib ]; then
  mkdir lib
fi

rm -rf lib/*

coin --to lib py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin --to lib py https://pypi.python.org/packages/source/s/syncloud-lib/syncloud-lib-2.tar.gz
coin --to lib py http://artifact.syncloud.org/3rdparty/PyYAML-x86_64.tar.gz
