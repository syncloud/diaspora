,import os
import sys
from bs4 import BeautifulSoup
from os import listdir
from os.path import dirname, join, abspath, isdir
import time
from requests.adapters import HTTPAdapter
from subprocess import check_output, check_call
import pytest
import re
import requests
import shutil

from integration.util.ssh import run_scp, ssh_command, run_ssh

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD

@pytest.fixture(scope="session")
def module_setup(request, device_host):
    print('setup')
    request.addfinalizer(lambda: module_teardown(device_host))


def module_teardown(device_host):
    print('tear down')
    os.mkdir(LOG_DIR)
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_scp('root@{0}:/opt/data/platform/log/* {1}'.format(device_host, platform_log_dir), password=LOGS_SSH_PASSWORD)
    app_log_dir = join(LOG_DIR, 'diaspora_log')
    os.mkdir(app_log_dir)
    run_scp('root@{0}:/opt/data/diaspora/log/*.log {1}'.format(device_host, app_log_dir), password=LOGS_SSH_PASSWORD)
    run_scp('root@{0}:/opt/app/diaspora/diaspora/log/*.log {1}'.format(device_host, app_log_dir), password=LOGS_SSH_PASSWORD)

    run_scp('root@{0}:/var/log/sam.log {1}'.format(device_host, platform_log_dir), password=LOGS_SSH_PASSWORD)

    print('systemd logs')
    run_ssh('journalctl | tail -200', password=LOGS_SSH_PASSWORD)


@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('http://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def diaspora_session(device_host, user_domain):
    session = requests.session()
    response = session.get('https://{0}/login'.format(device_host),
                           headers={"Host": user_domain},
                           allow_redirects=False, verify=False)
    assert response.status_code == 301, response.text

    response = session.post('https://{0}/users/sign_in'.format(device_host),
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


def test_running_platform_web(device_host):
    print(check_output('nc -zv -w 1 {0} 80'.format(device_host), shell=True))


def test_activate_device(auth, device_host):
    email, password, domain = auth

    run_ssh(device_host, '/opt/app/sam/bin/sam update --release stable', password=DEFAULT_DEVICE_PASSWORD)
    run_ssh(device_host, '/opt/app/sam/bin/sam --debug upgrade platform', password=DEFAULT_DEVICE_PASSWORD)

    response = requests.post('http://{0}:81/rest/activate'.format(device_host),
                             data={'main_domain': 'syncloud.info', 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_running_platform_web_after_activation(device_host):
    check_call('nc -zv -w 1 {0} 80'.format(device_host), shell=True)


def test_platform_rest_after_activation(device_host):
    session = requests.session()
    url = 'http://{0}'.format(device_host)
    session.mount(url, HTTPAdapter(max_retries=5))
    response = session.get(url, timeout=60)
    assert response.status_code == 200


#def test_enable_https(syncloud_session, device_host):
#    response = syncloud_session.get('http://{0}/rest/settings/set_protocol'.format(device_host), params={'protocol': 'https'})
#    assert '"success": true' in response.text
#    assert response.status_code == 200


def test_install(app_archive_path, device_host):
    __local_install(app_archive_path, device_host)


def test_create_user(auth, user_domain):
    email, password, domain = auth
    response = requests.post('https://{0}/users'.format(device_host),
                             headers={"Host": user_domain},
                             verify=False, allow_redirects=False,
                             data={
                                 'user[email]': email,
                                 'user[username]': DEVICE_USER,
                                 'user[password]': DEVICE_PASSWORD,
                                 'user[password_confirmation]': DEVICE_PASSWORD,
                                 'commit': "Sign+up"
                             })
    assert response.status_code == 302, response.text


# def test_upload_profile_photo(diaspora_session, user_domain, device_host):
#
#     response = diaspora_session.get('https://{0}/profile/edit'.format(device_host),
#                                     headers={"Host": user_domain},
#                                     allow_redirects=False, verify=False)
#     assert response.status_code == 200, response.text
#
#     soup = BeautifulSoup(response.text, "html.parser")
#     token = soup.find_all('meta', {'name': 'csrf-token'})[0]['content']
#
#     response = diaspora_session.post('https://{0}/photos'.format(device_host),
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

# def test_authenticated_resource(diaspora_session, device_host):
#     response = diaspora_session.get('http://{0}/diaspora/'.format(device_host), allow_redirects=False)
#     soup = BeautifulSoup(response.text, "html.parser")
#     requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
#     response = diaspora_session.post('http://{0}/diaspora/index.php'.format(device_host),
#                             data={'user': device_user, 'password': device_password, 'requesttoken': requesttoken},
#                             allow_redirects=False)
#
#     assert response.status_code == 302, response.text
#
#     assert session.get('http://localhost/diaspora/core/img/filetypes/text.png').status_code == 200

# def test_admin(device_host):
#     response = session.get('http://{0}/diaspora/index.php/settings/admin'.format(device_host), allow_redirects=False)
#     assert response.status_code == 200, response.text

# def test_remove(device_host):
#     session.post('http://{0}/server/rest/login'.format(device_host), data={'name': device_user, 'password': device_password})
#     response = session.get('http://{0}/server/rest/remove?app_id=diaspora'.format(device_host), allow_redirects=False)
#     assert response.status_code == 200, response.text


# def test_reinstall(app_archive_path, device_host):
#     __local_install(app_archive_path, device_host)


def __local_install(app_archive_path, device_host):
    run_scp('{0} root@{1}:/app.tar.gz'.format(app_archive_path, device_host), password=DEVICE_PASSWORD)
    run_ssh(device_host, '/opt/app/sam/bin/sam --debug install /app.tar.gz', password=DEVICE_PASSWORD)
    time.sleep(3)
