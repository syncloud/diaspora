from os.path import dirname, join, abspath, isdir
from os import listdir
import sys

app_path = abspath(join(dirname(__file__), '..'))

lib_path = join(app_path, 'lib')
libs = [join(lib_path, item) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(lambda l: sys.path.insert(0, l), libs)

from os import environ, symlink
from os.path import isdir, join
import shutil
from subprocess import check_output, STDOUT, CalledProcessError

from syncloud_app import logger

from syncloudlib.application import paths, urls, storage, ports
from syncloudlib import fs, linux, gen

import postgres
from config import Config
from config import UserConfig
import yaml
import logging


SYSTEMD_NGINX_NAME = 'diaspora.nginx'
SYSTEMD_POSTGRESQL = 'diaspora.postgresql'
SYSTEMD_REDIS = 'diaspora.redis'
SYSTEMD_SIDEKIQ = 'diaspora.sidekiq'
SYSTEMD_UNICORN = 'diaspora.unicorn'

APP_NAME = 'diaspora'
USER_NAME = 'diaspora'

PSQL_PORT = 5434
DB_NAME = 'diaspora'
DB_USER = 'diaspora'
DB_PASS = 'diaspora'
UNICORN_PORT = 1084
DB_TYPE = 'postgres'


logger.init(logging.DEBUG, console=True, line_format='%(message)s')


def database_init(logger, app_dir, app_data_dir, database_path, user_name):
    logger.info("creating database files")
    if not isdir(database_path):
        psql_initdb = join(app_dir, 'postgresql/bin/initdb')
        logger.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, '-E', 'UTF8', database_path], stderr=STDOUT))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(app_data_dir, 'config', 'postgresql', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)
    else:
        logger.info('Database path "{0}" already exists'.format(database_path))


class DiasporaInstaller:
    def __init__(self):
        self.log = logger.get_logger('diaspora')
          
        self.app_dir = paths.get_app_dir(APP_NAME)
        self.app_data_dir = paths.get_data_dir(APP_NAME)
        self.app_url = urls.get_app_url(APP_NAME)
        self.app_domain_name = urls.get_app_domain_name(APP_NAME)
        self.platform_app_dir = paths.get_app_dir('platform')
        self.platform_data_dir = paths.get_data_dir('platform')
        self.device_domain_name = urls.get_device_domain_name()
        self.rails_env = 'production'
        self.gem_home = '{0}/ruby'.format(self.app_dir)
        self.path = '{0}/ruby/bin:{0}/nodejs/bin:{0}/ImageMagick/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'.format(self.app_dir)
        self.ld_library_path = '{0}/ruby/lib:{0}/ImageMagick/lib:{0}/postgresql/lib'.format(self.app_dir)
        self.rake_db_cmd = '{0}/bin/update_db'.format(self.app_dir)
        self.diaspora_dir = '{0}/diaspora'.format(self.app_dir)
        self.psql_bin = '{0}/postgresql/bin/psql'.format(self.app_dir)
        self.diaspora_config = '{0}/config/diaspora/diaspora.yml'.format(self.app_data_dir)
        self.database_path = '{0}/database'.format(self.app_data_dir)
        self.database_socket = '{0}/.s.PGSQL.{1}'.format(self.database_path, PSQL_PORT)
        self.database_path_escaped = self.database_path.replace("/", "%2F")
        self.database_url = "postgresql://diaspora:diaspora@{0}:{1}/diaspora?encoding=unicode".format(self.database_path_escaped, PSQL_PORT)
        self.diaspora_gemfile = '{0}/Gemfile'.format(self.diaspora_dir)
        
        environ['RAILS_ENV'] = self.rails_env
        environ['DB'] = DB_TYPE
        environ['GEM_HOME'] = self.gem_home
        environ['PATH'] = self.path
        environ['LD_LIBRARY_PATH'] = self.ld_library_path
        environ['DIASPORA_CONFIG_DIR'] = '{0}/config/diaspora'.format(self.app_data_dir)
        environ['DATABASE_URL'] = self.database_url
        environ['BUNDLE_GEMFILE'] = self.diaspora_gemfile

    def install(self):


        home_folder = join('/home', USER_NAME)
        linux.useradd(USER_NAME, home_folder=home_folder)
        
        self.regenerate_config()
        
        fs.makepath(join(self.app_data_dir, 'config'))
        fs.makepath(join(self.app_data_dir, 'redis'))
        fs.makepath(join(self.app_data_dir, 'log'))
        fs.makepath(join(self.app_data_dir, 'nginx'))
        fs.makepath(join(self.app_data_dir, 'tmp'))

        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)
        if 'SNAP' not in environ:
            self.log.info(fs.chownpath(self.app_dir, USER_NAME, recursive=True))

        self.log.info("setup systemd")

        if not UserConfig(self.app_data_dir).is_activated():
            database_init(self.log, self.app_dir, self.app_data_dir, self.database_path, USER_NAME)
    
    def regenerate_config(self):
        variables = {
            'app_dir': self.app_dir,
            'app_data_dir': self.app_data_dir,
            'db_psql_port': PSQL_PORT,
            'db_psql_path': self.database_path,
            'db_password': DB_PASS,
            'unicorn_port': UNICORN_PORT,
            'rails_env': self.rails_env,
            'db_type': DB_TYPE,
            'gem_home': self.gem_home,
            'path': self.path,
            'ld_library_path': self.ld_library_path,
            'platform_app_dir': self.platform_app_dir,
            'database_url': self.database_url,
            'diaspora_gemfile': self.diaspora_gemfile,
            'database_socket': self.database_socket,
            'app_url': self.app_url,
            'device_domain_name': self.device_domain_name
        }

        templates_path = join(self.app_dir, 'config.templates')
        config_path = join(self.app_data_dir, 'config')
        gen.generate_files(templates_path, config_path, variables)


    def db_migrate(self):
        if not UserConfig(self.app_data_dir).is_activated():
            self.initialize()

    def initialize(self):

        self.log.info("initialization")
        postgres.execute("ALTER USER {0} WITH PASSWORD '{0}';".format(APP_NAME), self.psql_bin, DB_USER, self.database_path, PSQL_PORT, "postgres")
        env = dict(environ, RAILS_LOG_TO_STDOUT='true')
        try:
            output = check_output("{0}/diaspora/bin/rake db:create db:migrate 2>&1".format(self.app_dir), shell=True, cwd=self.diaspora_dir, env=env)
            self.log.info(output)
        except CalledProcessError, e:
            self.log.info(e.output)
            raise e
        
    def configure(self):
        self.prepare_storage()
        UserConfig(self.app_data_dir).set_activated(True)
        
    def update_domain(self):
        self.regenerate_config()

    def on_storage_change(self):
        self.prepare_storage()

    def prepare_storage(self):
        storage.init_storage(APP_NAME, USER_NAME)
        storage_dir = storage.get_storage_dir(APP_NAME)
        
        tmp_dir = join(storage_dir, 'tmp')
        fs.makepath(tmp_dir)
        fs.chownpath(tmp_dir, USER_NAME)
        
        uploads_dir = join(storage_dir, 'uploads')
        fs.makepath(uploads_dir)
        fs.chownpath(uploads_dir, USER_NAME)
        
        if 'SNAP' not in environ:
            diaspora_dir = join(self.app_dir, 'diaspora')
       
            symlink(tmp_dir, join(diaspora_dir, 'tmp'))
            symlink(uploads_dir, join(diaspora_dir, 'public', 'uploads'))

        
        
