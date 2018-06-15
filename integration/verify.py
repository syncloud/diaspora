import os
import shutil
import time
from os.path import dirname, join
from subprocess import check_output, check_call

import pytest
import requests
from requests.adapters import HTTPAdapter

from syncloudlib.integration.installer import local_install, wait_for_sam, wait_for_rest, local_remove, \
    get_data_dir, get_app_dir, get_service_prefix, get_ssh_env_vars
from syncloudlib.integration.loop import loop_device_cleanup
from syncloudlib.integration.ssh import run_scp, run_ssh

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD
TMP_DIR = '/tmp/syncloud'
APP = "diaspora"

@pytest.fixture(scope="session")
def platform_data_dir(installer):
    return get_data_dir(installer, 'platform')

    
@pytest.fixture(scope="session")
def data_dir(installer):
    return get_data_dir(installer, APP)


@pytest.fixture(scope="session")
def app_dir(installer):
    return get_app_dir(installer, APP)
    

@pytest.fixture(scope="session")
def service_prefix(installer):
    return get_service_prefix(installer)


@pytest.fixture(scope="session")
def module_setup(request, device_host, data_dir, platform_data_dir, app_dir):
    request.addfinalizer(lambda: module_teardown(device_host, data_dir, platform_data_dir, app_dir))


def module_teardown(device_host, data_dir, platform_data_dir, app_dir, service_prefix):
    platform_log_dir = join(LOG_DIR, 'platform_log')
    os.mkdir(platform_log_dir)
    run_ssh(device_host, 'ls -la {0}'.format(data_dir), password=LOGS_SSH_PASSWORD, throw=False)
   
    run_scp('root@{0}:{1}/log/* {2}'.format(device_host, platform_data_dir, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False) 
    run_scp('root@{0}:/var/log/sam.log {1}'.format(device_host, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'mkdir {0}'.format(TMP_DIR), password=LOGS_SSH_PASSWORD)

    run_ssh(device_host, 'journalctl > {0}/journalctl.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/ > {1}/app.ls.log'.format(app_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/diaspora/ > {1}/app.diaspora.ls.log'.format(app_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/diaspora/log/ > {1}/app.diaspora.log.ls.log'.format(app_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/ > {1}/data.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/log/ > {1}/data.log.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/diaspora/ > {1}/data.diaspora.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/diaspora/log/ > {1}/data.diaspora.log.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'ls -la {0}/database/ > {1}/data.database.ls.log'.format(data_dir, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'journalctl -u {0}diaspora.unicorn --no-pager -n1000 > {1}/systemd.unicorn.log".format(service_prefix, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(device_host, 'journalctl -u {0}diaspora.sidekiq --no-pager -n1000 > {1}/systemd.unicorn.log".format(service_prefix, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
   
    app_log_dir = join(LOG_DIR, 'diaspora_log')
    os.mkdir(app_log_dir)
    run_scp('root@{0}:/var/log/messages* {1}'.format(device_host, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    run_scp('root@{0}:/var/log/*syslog* {1}'.format(device_host, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False) 
    run_scp('-r root@{0}:{1}/config {2}'.format(device_host, data_dir, app_log_dir), throw=False, password=LOGS_SSH_PASSWORD)
    
    run_scp('root@{0}:{1}/log/*.log {2}'.format(device_host, data_dir, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    run_scp('root@{0}:{1}/*.log {2}'.format(device_host, TMP_DIR, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    

@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('https://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD}, verify=False)
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


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
    os.mkdir(LOG_DIR)


def test_activate_device(auth, device_host):
    email, password, domain = auth

    response = requests.post('http://{0}:81/rest/activate'.format(device_host),
                             data={'main_domain': 'syncloud.info', 'redirect_email': email,
                                   'redirect_password': password, 'user_domain': domain,
                                   'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_running_platform_web_after_activation(device_host):
    check_call('nc -zv -w 1 {0} 80'.format(device_host), shell=True)


def test_platform_rest_after_activation(device_host):
    session = requests.session()
    url = 'https://{0}'.format(device_host)
    session.mount(url, HTTPAdapter(max_retries=5))
    response = session.get(url, timeout=60, verify=False)
    assert response.status_code == 200


def test_install(app_archive_path, device_host, installer, user_domain):
    local_install(device_host, DEVICE_PASSWORD, app_archive_path, installer)


def test_create_user(auth, user_domain, device_host):
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


# def test_remove(device_host):
#     session.post('http://{0}/server/rest/login'.format(device_host),
#                  data={'name': device_user, 'password': device_password})
#     response = session.get('http://{0}/server/rest/remove?app_id=diaspora'.format(device_host), allow_redirects=False)
#     assert response.status_code == 200, response.text


# def test_reinstall(app_archive_path, device_host):
#     __local_install(app_archive_path, device_host)
