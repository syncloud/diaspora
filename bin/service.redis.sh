#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start|stop]"
    exit 1
fi

case $1 in
start)
    exec ${DIR}/redis/bin/redis-server ${SNAP_COMMON}/config/redis/redis.conf
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac