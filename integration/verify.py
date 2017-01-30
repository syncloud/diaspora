import os
import sys
from bs4 import BeautifulSoup
from os import listdir
from os.path import dirname, join, abspath, isdir
import time
from requests.adapters import HTTPAdapter
from subprocess import check_output, check_call
import pytest
import re

app_path = join(dirname(__file__), '..')
sys.path.append(join(app_path, 'src'))

lib_path = join(app_path, 'lib')
libs = [abspath(join(lib_path, item)) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(lambda x: sys.path.insert(0, x), libs)

import requests
import shutil

from integration.util.ssh import run_scp, ssh_command, SSH, run_ssh

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD

@pytest.fixture(scope="session")
def module_setup(request):
    print('setup')
    request.addfinalizer(module_teardown)


def module_teardown():
    print('tear down')
    os.mkdir(LOG_DIR)
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@localhost:/opt/data/platform/log/* {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)
    app_log_dir = join(LOG_DIR, 'app_log')
    os.mkdir(app_log_dir)
    run_scp('root@localhost:/opt/data/diaspora/log/*.log {0}'.format(app_log_dir), password=LOGS_SSH_PASSWORD)

    run_scp('root@localhost:/var/log/sam.log {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)

    print('systemd logs')
    run_ssh('journalctl | tail -200', password=LOGS_SSH_PASSWORD)

    print('-------------------------------------------------------')
    print('syncloud docker image is running')
    print('connect using: {0}'.format(ssh_command(LOGS_SSH_PASSWORD, SSH)))
    print('-------------------------------------------------------')


@pytest.fixture(scope='function')
def syncloud_session():
    session = requests.session()
    session.post('http://localhost/rest/login', data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def diaspora_session(user_domain):
    session = requests.session()
    response = session.get('https://127.0.0.1/login',
                           headers={"Host": user_domain},
                           allow_redirects=False, verify=False)
    assert response.status_code == 301, response.text

    response = session.post('https://127.0.0.1/users/sign_in',
                            headers={"Host": user_domain},
                            data={'user[username]': DEVICE_USER,
                                  'user[password]': DEVICE_PASSWORD,
                                  # 'authenticity_token': token,
                                  'user[remember_me]': '1',
                                  'commit': 'Sign in'},
                            allow_redirects=False, verify=False)
    print(response.text)
    assert response.status_code == 302, response.text
    assert 'getting_started' in response.headers['Location'], response.text
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)


def test_running_platform_web():
    print(check_output('nc -zv -w 1 localhost 80', shell=True))


def test_activate_device(auth):
    email, password, domain, release, version = auth

    run_ssh('/opt/app/sam/bin/sam update --release {0}'.format(release), password=DEFAULT_DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug upgrade platform', password=DEFAULT_DEVICE_PASSWORD)

    response = requests.post('http://localhost:81/rest/activate',
                             data={'main_domain': 'syncloud.info', 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_running_platform_web_after_activation():
    check_call('nc -zv -w 1 localhost 80', shell=True)


def test_platform_rest_after_activation():
    session = requests.session()
    session.mount('http://localhost', HTTPAdapter(max_retries=5))
    response = session.get('http://localhost', timeout=60)
    assert response.status_code == 200


#def test_enable_https(syncloud_session):
#    response = syncloud_session.get('http://localhost/rest/settings/set_protocol', params={'protocol': 'https'})
#    assert '"success": true' in response.text
#    assert response.status_code == 200


def test_install(app_archive_path):
    __local_install(app_archive_path)


def test_create_user(auth, user_domain):
    email, password, domain, release, version, arch = auth
    response = requests.post('https://127.0.0.1/users', headers={"Host": user_domain},
                             verify=False, allow_redirects=False,
                             data={
                                 'user[email]': email,
                                 'user[username]': DEVICE_USER,
                                 'user[password]': DEVICE_PASSWORD,
                                 'user[password_confirmation]': DEVICE_PASSWORD,
                                 'commit': "Sign+up"
                             })
    assert response.status_code == 302, response.text


# def test_upload_profile_photo(diaspora_session, user_domain):
#
#     response = diaspora_session.get('https://127.0.0.1/profile/edit',
#                                     headers={"Host": user_domain},
#                                     allow_redirects=False, verify=False)
#     assert response.status_code == 200, response.text
#
#     soup = BeautifulSoup(response.text, "html.parser")
#     token = soup.find_all('meta', {'name': 'csrf-token'})[0]['content']
#
#     response = diaspora_session.post('https://127.0.0.1/photos',
#                                      headers={
#                                          "Host": user_domain,
#                                          'X-File-Name': 'profile.png',
#                                          'X-CSRF-Token': token
#                                      },
#                                      verify=False, allow_redirects=False,
#                                      params={
#                                          'photo[pending]': 'true',
#                                          'photo[aspect_ids]': 'all',
#                                          'photo[set_profile_photo]': 'true',
#                                          'qqfile': 'profile.png'
#                                      })
#     assert response.status_code == 200, response.text

    # with open(join(DIR, 'images', 'profile.png'),'rb') as payload:
    #     headers = {'content-type': 'application/x-www-form-urlencoded'}
    #     r = requests.post('https://IP_ADDRESS/rest/rest/2', auth=('userid', 'password'),
    #                   data=payload, verify=False, headers=headers)

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


def __local_install(app_archive_path):
    run_scp('{0} root@localhost:/app.tar
gz'.format(DIR, app_archive_path), password=DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug install /app.tar.gz'.format(version, arch), password=DEVICE_PASSWORD)
    time.sleep(3)
