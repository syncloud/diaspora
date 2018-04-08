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
from subprocess import check_output, STDOUT

from syncloud_app import logger

from syncloud_platform.gaplib import fs, linux, gen

from syncloud_platform.application import api

import postgres
from config import Config
from config import UserConfig
import yaml

SYSTEMD_NGINX_NAME = 'diaspora-nginx'
SYSTEMD_POSTGRESQL = 'diaspora-postgresql'
SYSTEMD_REDIS = 'diaspora-redis'
SYSTEMD_SIDEKIQ = 'diaspora-sidekiq'
SYSTEMD_UNICORN = 'diaspora-unicorn'

APP_NAME = 'diaspora'
USER_NAME = 'diaspora'

PSQL_PORT = 5434
DB_NAME = 'diaspora'
DB_USER = 'diaspora'
DB_PASS = 'diaspora'
UNICORN_PORT = 1084
DB_TYPE = 'postgres'


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
        self.log = logger.get_logger('diaspora.installer')
        self.app = api.get_app_setup(APP_NAME)
        self.device_domain_name = self.app.device_domain_name()
        self.app_domain_name = self.app.app_domain_name()
        self.app_dir = self.app.get_install_dir()

    def install(self):

        linux.fix_locale()

        linux.useradd(USER_NAME)

        self.log.info(fs.chownpath(self.app.get_install_dir(), USER_NAME, recursive=True))

        app_data_dir = self.app.get_data_dir()
        database_path = '{0}/database'.format(app_data_dir)
        gem_home = '{0}/ruby'.format(self.app_dir)
        path = '{0}/ruby/bin:{0}/nodejs/bin:{0}/ImageMagick/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'.format(self.app_dir)
        ld_library_path = '{0}/ruby/lib:{0}/ImageMagick/lib:{0}/postgresql/lib'.format(self.app_dir)

        variables = {
            'app_dir': self.app_dir,
            'app_data_dir': app_data_dir,
            'db_psql_path': database_path,
            'db_psql_port': PSQL_PORT,
            'db_name': DB_NAME,
            'db_user': DB_USER,
            'db_password': DB_PASS,
            'unicorn_port': UNICORN_PORT,
            'rails_env': 'production',
            'db_type': DB_TYPE,
            'gem_home': gem_home,
            'path': path,
            'ld_library_path': ld_library_path
        }

        templates_path = join(self.app_dir, 'config.templates')
        config_path = join(app_data_dir, 'config')
        gen.generate_files(templates_path, config_path, variables)

        fs.makepath(join(app_data_dir, 'config'))
        fs.makepath(join(app_data_dir, 'redis'))
        fs.makepath(join(app_data_dir, 'log'))
        fs.makepath(join(app_data_dir, 'nginx'))

        fs.chownpath(app_data_dir, USER_NAME, recursive=True)

        self.log.info("setup systemd")

        user_config = UserConfig(app_data_dir)
        is_first_time = not user_config.is_activated()
        if is_first_time:
            database_init(self.log, self.app_dir, app_data_dir, database_path, USER_NAME)

        self.app.add_service(SYSTEMD_POSTGRESQL)

        config = Config(app_data_dir)
        symlink(join(config_path, 'diaspora', 'diaspora.yml'), join(self.app_dir, 'diaspora', 'config', 'diaspora.yml'))
        symlink(join(config_path, 'diaspora', 'database.yml'), join(self.app_dir, 'diaspora', 'config', 'database.yml'))
        self.update_configuraiton(config)

        if is_first_time:
            self.initialize(app_data_dir, config)

        self.log.info(fs.chownpath(self.app_dir, USER_NAME, recursive=True))

        self.app.add_service(SYSTEMD_REDIS)
        self.app.add_service(SYSTEMD_SIDEKIQ)
        self.app.add_service(SYSTEMD_UNICORN)
        self.app.add_service(SYSTEMD_NGINX_NAME)

        self.app.init_storage(USER_NAME)


    def remove(self):

        self.app.remove_service(SYSTEMD_NGINX_NAME)
        self.app.remove_service(SYSTEMD_UNICORN)
        self.app.remove_service(SYSTEMD_SIDEKIQ)
        self.app.remove_service(SYSTEMD_REDIS)
        self.app.remove_service(SYSTEMD_POSTGRESQL)

        if isdir(self.app_dir):
            shutil.rmtree(self.app_dir)

    def initialize(self, app_data_dir, config):

        self.log.info("initialization")
        postgres.execute("ALTER USER {0} WITH PASSWORD '{0}';".format(APP_NAME), config, "postgres")

        self.environment(config)
        self.log.info(check_output(config.rake_db_cmd(), shell=True, cwd=config.diaspora_dir()))

        UserConfig(app_data_dir).set_activated(True)

    def environment(self, config):
        environ['RAILS_ENV'] = config.rails_env()
        environ['DB'] = config.db()
        environ['GEM_HOME'] = config.gem_home()
        environ['PATH'] = config.path()
        environ['LD_LIBRARY_PATH'] = config.ld_library_path()

    def update_domain(self, config):
        self.update_configuraiton(config)

    def update_configuraiton(self, config):
        url = self.app.app_url()
        diaspora_config = yaml.load(open(config.diaspora_config()))

        diaspora_config['configuration']['environment']['url'] = url
        diaspora_config['configuration']['environment']['assets']['host'] = url

        yaml.dump(diaspora_config, open(config.diaspora_config(), 'w'))
