#!/opt/app/platform/python/bin/python

from os import environ, listdir
from os.path import dirname, join, abspath, isdir
from subprocess import check_output
import sys

app_path = abspath(join(dirname(__file__), '..', '..', 'diaspora'))
lib_path = join(app_path, 'lib')
libs = [join(lib_path, item) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(sys.path.append, libs)

from diaspora.config import Config

config = Config(environ['SNAP_COMMON'])

environ['RAILS_ENV'] = config.rails_env()
environ['DB'] = config.db()
environ['GEM_HOME'] = config.gem_home()
environ['PATH'] = config.path()
environ['LD_LIBRARY_PATH'] = config.ld_library_path()

print(check_output(config.unicorn_cmd(), shell=True, cwd=config.diaspora_dir()))
