import os
import sys
from bs4 import BeautifulSoup
from os import listdir
from os.path import dirname, join, abspath, isdir
import time
from subprocess import check_output

import pytest
import re

app_path = join(dirname(__file__), '..')
sys.path.append(join(app_path, 'src'))

lib_path = join(app_path, 'lib')
libs = [abspath(join(lib_path, item)) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(lambda x: sys.path.insert(0, x), libs)

import requests
import shutil

from integration.util.ssh import run_scp, ssh_command, SSH, run_ssh, set_docker_ssh_port

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'


@pytest.fixture(scope='module')
def user_domain(auth):
    email, password, domain, release, version, arch = auth
    return 'diaspora.{0}.{1}'.format(domain, SYNCLOUD_INFO)


@pytest.fixture(scope='function')
def syncloud_session():
    session = requests.session()
    session.post('http://localhost/server/rest/login', data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def diaspora_session(user_domain):
    session = requests.session()
    response = session.post('http://127.0.0.1',
                            headers={"Host": user_domain},
                            data={'user': DEVICE_USER, 'password': DEVICE_PASSWORD},
                            allow_redirects=False)
    assert response.status_code == 302, response.text
    return session


def test_remove_logs():
    shutil.rmtree(LOG_DIR, ignore_errors=True)


def test_activate_device(auth):
    email, password, domain, release, version, arch = auth
    response = requests.post('http://localhost:81/server/rest/activate',
                             data={'redirect-email': email, 'redirect-password': password, 'redirect-domain': domain,
                                   'name': DEVICE_USER, 'password': DEVICE_PASSWORD,
                                   'api-url': 'http://api.syncloud.info:81', 'domain': 'syncloud.info',
                                   'release': release})
    assert response.status_code == 200


def test_enable_https(syncloud_session):
    response = syncloud_session.get('http://localhost/server/rest/settings/external_access_enable?mode=https')
    assert '"success": true' in response.text
    assert response.status_code == 200


def test_install(auth):
    __local_install(auth)


def test_non_authenticated_resource(user_domain):
    response = requests.get('https://127.0.0.1', headers={"Host": user_domain}, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")
    smiley_png_url = soup.find_all('img', {'alt': 'Smiley laughing'})[0]['src']
    smiley_png_localurl = re.match("https://.*/assets/(.*)".format(SYNCLOUD_INFO), smiley_png_url).group(1)
    print(smiley_png_localurl)
    response = requests.get('https://127.0.0.1/assets/{0}'.format(smiley_png_localurl), headers={"Host": user_domain}, verify=False)
    assert response.status_code == 200, response.text


# def test_authenticated_resource(diaspora_session):
#     response = diaspora_session.get('http://localhost/diaspora/', allow_redirects=False)
#     soup = BeautifulSoup(response.text, "html.parser")
#     requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
#     response = diaspora_session.post('http://localhost/diaspora/index.php',
#                             data={'user': device_user, 'password': device_password, 'requesttoken': requesttoken},
#                             allow_redirects=False)
#
#     assert response.status_code == 302, response.text
#
#     assert session.get('http://localhost/diaspora/core/img/filetypes/text.png').status_code == 200

# def test_admin():
#     response = session.get('http://localhost/diaspora/index.php/settings/admin', allow_redirects=False)
#     assert response.status_code == 200, response.text

# def test_remove():
#     session.post('http://localhost/server/rest/login', data={'name': device_user, 'password': device_password})
#     response = session.get('http://localhost/server/rest/remove?app_id=diaspora', allow_redirects=False)
#     assert response.status_code == 200, response.text


# def test_reinstall(auth):
#     __local_install(auth)


def test_copy_logs():
    os.mkdir(LOG_DIR)
    run_scp('root@localhost:/opt/data/platform/log/* {0}'.format(LOG_DIR), password=DEVICE_PASSWORD)

    print('-------------------------------------------------------')
    print('syncloud docker image is running')
    print('connect using: {0}'.format(ssh_command(DEVICE_PASSWORD, SSH)))
    print('-------------------------------------------------------')


def __local_install(auth):
    email, password, domain, release, version, arch = auth
    run_scp('{0}/../diaspora-{1}-{2}.tar.gz root@localhost:/'.format(DIR, version, arch), password=DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug install /diaspora-{0}-{1}.tar.gz'.format(version, arch), password=DEVICE_PASSWORD)
    time.sleep(3)
