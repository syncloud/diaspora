#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start|post-start]"
    exit 1
fi

. $SNAP_COMMON/config/diaspora.env

case $1 in
start)
    cd $DIR/diaspora
    exec ${DIR}/ruby/bin/bundle exec "unicorn -c config/unicorn.rb -E $RAILS_ENV -D"
    ;;
post-start)
    timeout 600 /bin/bash -c 'until echo > /dev/tcp/localhost/'$UNICORN_PORT'; do sleep 2; done'
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac