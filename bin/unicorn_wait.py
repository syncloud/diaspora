#!/opt/app/platform/python/bin/python

from os import listdir
from os.path import dirname, join, abspath, isdir
import time
import sys

app_path = abspath(join(dirname(__file__), '..', '..', 'diaspora'))
lib_path = join(app_path, 'lib')
libs = [join(lib_path, item) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(sys.path.append, libs)

import requests
from diaspora.config import Config


def wait_for_unicorn(delay=2, retries=20):
    config = Config()
    for retry in range(0, retries):
        unicorn_url = 'http://localhost:{0}'.format(config.unicorn_port())
        try:
            response = requests.get(unicorn_url, allow_redirects=False)
            if response.status_code == 200:
                return True
        except Exception, e:
            print(e.message)
        print('unable to {0}'.format(unicorn_url))
        retry += 1
        time.sleep(delay)

    return False

if wait_for_unicorn():
    sys.exit(0)
else:
    sys.exit('unable to detect running unicorn')
