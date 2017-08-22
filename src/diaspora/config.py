from ConfigParser import ConfigParser
from os.path import isfile, join

default_config_path = '/opt/app/diaspora/config'
default_config_file = join(default_config_path, 'diaspora.cfg')

default_user_config_path = '/opt/data/diaspora/config'
default_user_config_file = join(default_user_config_path, 'user_diaspora.cfg')


class Config:

    def __init__(self, filename=default_config_file):
        self.parser = ConfigParser()
        self.parser.read(filename)
        self.filename = filename

    def unicorn_port(self):
        return self.parser.getint('diaspora', 'unicorn_port')

    def app_name(self):
        return self.parser.get('diaspora', 'app_name')

    def url(self):
        return self.parser.get('diaspora', 'url')

    def site_config_file(self):
        return self.parser.get('diaspora', 'site_config_file')

    def site_name(self):
        return self.parser.get('diaspora', 'site_name')

    def install_path(self):
        return self.parser.get('diaspora', 'install_path')

    def data_dir(self):
        return self.parser.get('diaspora', 'data_dir')

    def bin_dir(self):
        return self.parser.get('diaspora', 'bin_dir')

    def psql(self):
        return self.parser.get('diaspora', 'psql')

    def db_user(self):
        return self.parser.get('diaspora', 'db_user')

    def db_name(self):
        return self.parser.get('diaspora', 'db_name')

    def db_socket(self):
        return self.parser.get('diaspora', 'db_socket')

    def db_port(self):
        return self.parser.get('diaspora', 'db_port')

    def rails_env(self):
        return self.parser.get('diaspora', 'rails_env')

    def db(self):
        return self.parser.get('diaspora', 'db')

    def gem_home(self):
        return self.parser.get('diaspora', 'gem_home')

    def path(self):
        return self.parser.get('diaspora', 'path')

    def ld_library_path(self):
        return self.parser.get('diaspora', 'ld_library_path')

    def unicorn_cmd(self):
        return self.parser.get('diaspora', 'unicorn_cmd')

    def rake_db_cmd(self):
        return self.parser.get('diaspora', 'rake_db_cmd')

    def diaspora_dir(self):
        return self.parser.get('diaspora', 'diaspora_dir')

    def diaspora_config(self):
        return self.parser.get('diaspora', 'diaspora_config')


class UserConfig:

    def __init__(self, filename=default_user_config_file):
        self.parser = ConfigParser()
        self.parser.read(filename)
        self.filename = filename
        if not isfile(self.filename):
            self.parser.add_section('diaspora')
            self.set_activated(False)
            self.__save()
        else:
            self.parser.read(self.filename)

        if not self.parser.has_section('diaspora'):
            self.parser.add_section('diaspora')

    def is_activated(self):
        return self.parser.getboolean('diaspora', 'activated')

    def set_activated(self, value):
        self.parser.set('diaspora', 'activated', str(value))
        self.__save()

    def __save(self):
        with open(self.filename, 'wb') as f:
            self.parser.write(f)
