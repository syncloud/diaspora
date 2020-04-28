#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [ -z "$SNAP_COMMON" ]; then
  echo "SNAP_COMMON environment variable must be set"
  exit 1
fi

# shellcheck source=config/db.env
. "${SNAP_COMMON}/config/db.env"
export LD_LIBRARY_PATH=${DIR}/postgresql/lib

if [[ "$(whoami)" == "diaspora" ]]; then
    ${DIR}/postgresql/bin/psql -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
else
    sudo -E -H -u diaspora LD_LIBRARY_PATH=${LD_LIBRARY_PATH} ${DIR}/postgresql/bin/psql -p ${PSQL_PORT} -h ${PSQL_DATABASE} "$@"
fi
