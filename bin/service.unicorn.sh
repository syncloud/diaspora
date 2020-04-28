#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start|post-start]"
    exit 1
fi

. $SNAP_COMMON/config/diaspora.env

case $1 in
pre-start)
    timeout 5 /bin/bash -c 'until [ -S '${DB_SOCKET}' ]; do echo "waiting for ${DB_SOCKET}"; sleep 1; done'
    ${DIR}/hooks/db-migrate
    ;;
start)
    cd $DIR/diaspora
    export LD_LIBRARY_PATH=$DIR/ruby/lib:$DIR/ImageMagick/lib:$DIR/postgresql/lib
    exec ${DIR}/ruby/bin/bundle exec "unicorn -c config/unicorn.rb -E $RAILS_ENV -d"
    ;;
post-start)
    timeout 600 /bin/bash -c 'until echo > /dev/tcp/localhost/'$UNICORN_PORT'; do sleep 2; done'
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac