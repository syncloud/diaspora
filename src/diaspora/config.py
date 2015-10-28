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

    def port(self):
        return self.parser.getint('diaspora', 'port')

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

    def root_path(self):
        return self.parser.get('diaspora', 'root_path')

    def psql(self):
        return self.parser.get('diaspora', 'psql')

    def db_user(self):
        return self.parser.get('diaspora', 'db_user')

    def db_name(self):
        return self.parser.get('diaspora', 'db_name')

    def db_socket(self):
        return self.parser.get('diaspora', 'db_socket')


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

    def is_installed(self):
        return self.parser.getboolean('diaspora', 'activated')

    def set_activated(self, value):
        self.parser.set('diaspora', 'activated', str(value))
        self.__save()

    def __save(self):
        with open(self.filename, 'wb') as f:
            self.parser.write(f)
