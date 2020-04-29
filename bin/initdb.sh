#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [ -z "$SNAP_COMMON" ]; then
  echo "SNAP_COMMON environment variable must be set"
  exit 1
fi

export LD_LIBRARY_PATH=${DIR}/postgresql/lib

if [[ "$(whoami)" == "diaspora" ]]; then
    ${DIR}/postgresql/bin/initdb "$@"
else
    sudo -E -H -u diaspora LD_LIBRARY_PATH=${LD_LIBRARY_PATH} ${DIR}/postgresql/bin/initdb "$@"
fi
