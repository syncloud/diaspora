from ConfigParser import ConfigParser
from os.path import isfile, join


class UserConfig:

    def __init__(self, data_dir):
        self.parser = ConfigParser()
        filename = join(data_dir, 'config', 'user_diaspora.cfg')
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
