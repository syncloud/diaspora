from os.path import dirname, join

import yaml


def test_yaml():
    with open(join(dirname(__file__), '..', 'config', 'diaspora', 'diaspora.yml')) as f:
        config = yaml.load(f)
        config['configuration']['environment']['url'] = '{0}/diaspora'.format('test')
        config['configuration']['environment']['assets']['host'] = '{0}/diaspora'.format('test')
