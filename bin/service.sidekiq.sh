#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start|post-start]"
    exit 1
fi

. $SNAP_COMMON/config/diaspora.env

case $1 in
start)
    cd ${DIR}/diaspora
    exec ${DIR}/ruby/bin/bundle exec "sidekiq -e production -L $SNAP_COMMON/log/sidekiq.log >> $SNAP_COMMON/log/sidekiq.log 2>&1"
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac