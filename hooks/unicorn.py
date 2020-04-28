from os import environ, listdir
from os.path import dirname, join, abspath, isdir
from subprocess import check_output
import sys
from config import Config

config = Config(environ['SNAP_COMMON'])

environ['RAILS_ENV'] = config.rails_env()
environ['DB'] = config.db()
environ['GEM_HOME'] = config.gem_home()
environ['PATH'] = config.path()

print(check_output(config.unicorn_cmd(), shell=True, cwd=config.diaspora_dir()))
