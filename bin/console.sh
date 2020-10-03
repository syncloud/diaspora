#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [ -z "$SNAP_COMMON" ]; then
  echo "SNAP_COMMON environment variable must be set"
  exit 1
fi

source $SNAP_COMMON/config/diaspora.env
cd ${DIR}/diaspora
exec bundle exec rails console "$@"