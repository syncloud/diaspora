from os import environ
from os.path import isdir, join
import shutil
from subprocess import check_output

from syncloud_app import logger

from syncloud_platform.gaplib import fs, linux

from syncloud_platform.application import api

from diaspora import postgres
from diaspora.config import Config
from diaspora.config import UserConfig
import yaml

SYSTEMD_NGINX_NAME = 'diaspora-nginx'
SYSTEMD_POSTGRESQL = 'diaspora-postgresql'
SYSTEMD_REDIS = 'diaspora-redis'
SYSTEMD_SIDEKIQ = 'diaspora-sidekiq'
SYSTEMD_UNICORN = 'diaspora-unicorn'

APP_NAME = 'diaspora'
USER_NAME = 'diaspora'

class DiasporaInstaller:
    def __init__(self):
        self.log = logger.get_logger('diaspora.installer')
        self.config = Config()
        self.app = api.get_app_setup(APP_NAME)

    def install(self):

        linux.fix_locale()

        linux.useradd(USER_NAME)

        self.log.info(fs.chownpath(self.app.get_install_dir(), USER_NAME, recursive=True))

        app_data_dir = self.app.get_data_dir()

        fs.makepath(join(app_data_dir, 'config'))
        fs.makepath(join(app_data_dir, 'postgresql'))
        fs.makepath(join(app_data_dir, 'redis'))
        fs.makepath(join(app_data_dir, 'log'))
        fs.makepath(join(app_data_dir, 'nginx'))

        fs.chownpath(app_data_dir, USER_NAME, recursive=True)

        print("setup systemd")

        self.app.add_service(SYSTEMD_POSTGRESQL)

        self.update_configuraiton()

        if not UserConfig().is_installed():
            self.initialize()

        self.log.info(fs.chownpath(self.config.install_path(), USER_NAME, recursive=True))

        self.app.add_service(SYSTEMD_REDIS)
        self.app.add_service(SYSTEMD_SIDEKIQ)
        self.app.add_service(SYSTEMD_UNICORN)
        self.app.add_service(SYSTEMD_NGINX_NAME)

        self.app.init_storage(USER_NAME)

        self.app.register_web(self.config.port())

    def remove(self):

        self.app.unregister_web()

        self.app.remove_service(SYSTEMD_NGINX_NAME)
        self.app.remove_service(SYSTEMD_UNICORN)
        self.app.remove_service(SYSTEMD_SIDEKIQ)
        self.app.remove_service(SYSTEMD_REDIS)
        self.app.remove_service(SYSTEMD_POSTGRESQL)

        if isdir(self.config.install_path()):
            shutil.rmtree(self.config.install_path())

    def initialize(self):

        print("initialization")
        postgres.execute("ALTER USER {0} WITH PASSWORD '{0}';".format(self.config.app_name()), database="postgres")

        self.environment()
        print(check_output(self.config.rake_db_cmd(), shell=True, cwd=self.config.diaspora_dir()))

        UserConfig().set_activated(True)

    def environment(self):
        environ['RAILS_ENV'] = self.config.rails_env()
        environ['DB'] = self.config.db()
        environ['GEM_HOME'] = self.config.gem_home()
        environ['PATH'] = self.config.path()

    def update_domain(self):
        self.update_configuraiton()

    def update_configuraiton(self):
        url = self.app.app_url()
        config = yaml.load(open(self.config.diaspora_config()))

        config['configuration']['environment']['url'] = url
        config['configuration']['environment']['assets']['host'] = url

        yaml.dump(config, open(self.config.diaspora_config(), 'w'))
