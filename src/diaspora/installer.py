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
from syncloud_platform.tools import chown
from diaspora import postgres
from diaspora.config import Config

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

        if 'LANG' in environ:
            lang = environ['LANG']
            if lang not in check_output(['locale', '-a']):
                print("generating locale: {0}".format(lang))
                fix_locale_gen(lang)
                check_output('locale-gen')

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
        add_service(self.config.install_path(), SYSTEMD_REDIS)
        add_service(self.config.install_path(), SYSTEMD_SIDEKIQ)
        add_service(self.config.install_path(), SYSTEMD_UNICORN)
        add_service(self.config.install_path(), SYSTEMD_NGINX_NAME)

        self.prepare_storage()

        if not self.installed():
            self.initialize()

        Nginx().add_app('owncloud', self.config.port())

    def remove(self):

        config = Config()
        Nginx().remove_app('owncloud')
        remove_service(SYSTEMD_NGINX_NAME)
        # remove_service(SYSTEMD_PHP_FPM_NAME)
        remove_service(SYSTEMD_POSTGRESQL)

        if isdir(config.install_path()):
            shutil.rmtree(config.install_path())

    def installed(self):
        config = Config()
        # if not isfile(config.config_file()):
        #     return False
        #
        # return 'installed' in open(config.config_file()).read().strip()
        return False

    def initialize(self):

            print("initialization")
            postgres.execute("ALTER USER {0} WITH PASSWORD '{0}';".format(self.config.app_name()), database="postgres")

            # Setup().finish(INSTALL_USER, unicode(uuid.uuid4().hex))

    def prepare_storage(self):
        hardware = Hardware()
        hardware.init_app_storage(self.config.app_name(), self.config.app_name())

def fix_locale_gen(lang, locale_gen='/etc/locale.gen'):
    editor = massedit.MassEdit()
    editor.append_code_expr("re.sub('# {0}', '{0}', line)".format(lang))
    editor.edit_file(locale_gen)

