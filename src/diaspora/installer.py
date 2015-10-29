from os import environ
from os.path import isdir, join
import shutil
from subprocess import check_output

import massedit
from syncloud_app import logger

from syncloud_platform.systemd.systemctl import remove_service, add_service
from syncloud_platform.tools import app
from syncloud_platform.tools.nginx import Nginx
from syncloud_platform.tools.hardware import Hardware
from syncloud_platform.tools import chown, locale
from diaspora import postgres
from diaspora.config import Config
from diaspora.config import UserConfig

SYSTEMD_NGINX_NAME = 'diaspora-nginx'
SYSTEMD_POSTGRESQL = 'diaspora-postgresql'
SYSTEMD_REDIS = 'diaspora-redis'
SYSTEMD_SIDEKIQ = 'diaspora-sidekiq'
SYSTEMD_UNICORN = 'diaspora-unicorn'
INSTALL_USER = 'installer'


class DiasporaInstaller:
    def __init__(self):
        self.log = logger.get_logger('diaspora.installer')
        self.config = Config()

    def install(self):

        locale.fix_locale()

        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        app_data_dir = app.get_app_data_root(self.config.app_name(), self.config.app_name())

        if not isdir(join(app_data_dir, 'config')):
            app.create_data_dir(app_data_dir, 'config', self.config.app_name())

        if not isdir(join(app_data_dir, 'postgresql')):
            app.create_data_dir(app_data_dir, 'postgresql', self.config.app_name())

        if not isdir(join(app_data_dir, 'redis')):
            app.create_data_dir(app_data_dir, 'redis', self.config.app_name())

        if not isdir(join(app_data_dir, 'log')):
            app.create_data_dir(app_data_dir, 'log', self.config.app_name())

        if not isdir(join(app_data_dir, 'nginx')):
            app.create_data_dir(app_data_dir, 'nginx', self.config.app_name())

        print("setup systemd")

        add_service(self.config.install_path(), SYSTEMD_POSTGRESQL)

        if not UserConfig().is_installed():
            self.initialize()

        add_service(self.config.install_path(), SYSTEMD_REDIS)
        add_service(self.config.install_path(), SYSTEMD_SIDEKIQ)
        add_service(self.config.install_path(), SYSTEMD_UNICORN)
        add_service(self.config.install_path(), SYSTEMD_NGINX_NAME)

        self.prepare_storage()

        Nginx().add_app('diaspora', self.config.port())

    def remove(self):

        Nginx().remove_app('diaspora')
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
        # postgres.execute("create database diaspora_production;", database="postgres")
        environ['RAILS_ENV'] = 'production'
        environ['DB'] = 'postgres'
        environ['GEM_HOME'] = '{0}/ruby'.format(self.config.install_path())
        environ['PATH'] = '{0}/ruby/bin:{0}/nodejs/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'.format(self.config.install_path())
        check_output('{0}/diaspora/bin/rake db:create db:schema:load'.format(self.config.install_path()),
                     shell=True,
                     cwd='{0}/diaspora'.format(self.config.install_path()))

        check_output('{0}/diaspora/bin/rake assets:precompile'.format(self.config.install_path()),
                     shell=True,
                     cwd='{0}/diaspora'.format(self.config.install_path()))
        self.log.info(chown.chown(self.config.app_name(), self.config.install_path()))

        UserConfig().set_activated(True)

    def prepare_storage(self):
        hardware = Hardware()
        hardware.init_app_storage(self.config.app_name(), self.config.app_name())
