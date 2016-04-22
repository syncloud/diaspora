from os import environ
from os.path import isdir, join
import shutil
from subprocess import check_output

from syncloud_app import logger

from syncloud_platform.systemd.systemctl import remove_service, add_service

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

    def install(self):

        linux.fix_locale()

        linux.useradd(USER_NAME)

        app_setup = api.get_app_setup(APP_NAME)

        self.log.info(fs.chownpath(app_setup.get_install_dir(), USER_NAME, recursive=True))

        app_data_dir = app_setup.get_data_dir()

        fs.makepath(join(app_data_dir, 'config'))
        fs.makepath(join(app_data_dir, 'postgresql'))
        fs.makepath(join(app_data_dir, 'redis'))
        fs.makepath(join(app_data_dir, 'log'))
        fs.makepath(join(app_data_dir, 'nginx'))

        fs.chownpath(app_data_dir, USER_NAME, recursive=True)

        print("setup systemd")

        add_service(self.config.install_path(), SYSTEMD_POSTGRESQL)

        self.update_configuraiton()

        if not UserConfig().is_installed():
            self.initialize()

        #self.recompile_assets()

        self.log.info(fs.chownpath(self.config.install_path(), USER_NAME, recursive=True))

        add_service(self.config.install_path(), SYSTEMD_REDIS)
        add_service(self.config.install_path(), SYSTEMD_SIDEKIQ)
        add_service(self.config.install_path(), SYSTEMD_UNICORN)
        add_service(self.config.install_path(), SYSTEMD_NGINX_NAME)

        app_setup.init_storage(USER_NAME)

        app_setup.register_web(self.config.port())

    def remove(self):

        app_setup = api.get_app_setup(APP_NAME)

        app_setup.unregister_web()

        remove_service(SYSTEMD_NGINX_NAME)
        remove_service(SYSTEMD_UNICORN)
        remove_service(SYSTEMD_SIDEKIQ)
        remove_service(SYSTEMD_REDIS)
        remove_service(SYSTEMD_POSTGRESQL)

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
        self.recompile_assets()

    #def recompile_assets(self):
    #    self.environment()
    #    print(check_output(self.config.rake_assets(), shell=True, cwd=self.config.diaspora_dir()))

    def update_configuraiton(self):
        app_setup = api.get_app_setup(APP_NAME)
        url = app_setup.app_url()
        config = yaml.load(open(self.config.diaspora_config()))

        config['configuration']['environment']['url'] = url
        config['configuration']['environment']['assets']['host'] = url

        yaml.dump(config, open(self.config.diaspora_config(), 'w'))
