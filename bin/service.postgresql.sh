#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

# shellcheck source=config/db.env
. "${SNAP_COMMON}/config/db.env"
export LD_LIBRARY_PATH=${DIR}/postgresql/lib

case $1 in
start)
    exec ${DIR}/postgresql/bin/pg_ctl -w -s -D ${PSQL_DATABASE}/database start
    ;;
reload)
    exec ${DIR}/postgresql/bin/pg_ctl -s -D ${PSQL_DATABASE}/database reload
    ;;
stop)
    exec ${DIR}/postgresql/bin/pg_ctl -s -D ${PSQL_DATABASE}/database stop -m fast
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac