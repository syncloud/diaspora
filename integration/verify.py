import os
import shutil
import time
from os.path import dirname, join
from subprocess import check_output, check_call

import pytest
import requests
from requests.adapters import HTTPAdapter

from syncloudlib.integration.installer import local_install, wait_for_installer
from syncloudlib.integration.loop import loop_device_add, loop_device_cleanup
from syncloudlib.integration.hosts import add_host_alias_by_ip
from requests.packages.urllib3.exceptions import InsecureRequestWarning

DIR = dirname(__file__)


@pytest.fixture(scope="session")
def module_setup(request, device, platform_data_dir, app_dir, artifact_dir):
    def module_teardown():
        platform_log_dir = join(artifact_dir, 'platform_log')
        os.mkdir(platform_log_dir)
        device.run_ssh('ls -la /var/snap/duaspora/common', throw=False)
   
        device.scp_from_device('{0}/log/* {1}'.format(platform_data_dir, platform_log_dir), throw=False) 
        device.run_ssh('mkdir {0}'.format(TMP_DIR))

        device.run_ssh('journalctl > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/ > {1}/app.ls.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/diaspora/ > {1}/app.diaspora.ls.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/diaspora/log/ > {1}/app.diaspora.log.ls.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/diaspora/public/ > {1}/app.diaspora.public.ls.log'.format(app_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/ > {1}/data.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/log/ > {1}/data.log.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/diaspora/ > {1}/data.diaspora.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/diaspora/log/ > {1}/data.diaspora.log.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('ls -la {0}/database/ > {1}/data.database.ls.log'.format(data_dir, TMP_DIR), throw=False)
        device.run_ssh('journalctl -u {0}diaspora.unicorn --no-pager -n1000 > {1}/systemd.unicorn.log'.format(service_prefix, TMP_DIR), throw=False)
        device.run_ssh('journalctl -u {0}diaspora.sidekiq --no-pager -n1000 > {1}/systemd.sidekiq.log'.format(service_prefix, TMP_DIR), throw=False)
   
        app_log_dir = join(LOG_DIR, 'diaspora_log')
        os.mkdir(app_log_dir)
        device.scp_from_device('/var/log/messages* {0}'.format(app_log_dir), throw=False)
        device.scp_from_device('/var/log/*syslog* {0}'.format(app_log_dir), throw=False) 
        device.scp_from_device('{0}/config {1}'.format(data_dir, app_log_dir), throw=False)
    
        device.scp_from_device('{0}/log/*.log {1}'.format(data_dir, app_log_dir), throw=False)
        device.scp_from_device('{0}/*.log {1}'.format(TMP_DIR, app_log_dir), throw=False)
    
    request.addfinalizer(module_teardown)



@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('https://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD}, verify=False)
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


@pytest.fixture(scope='function')
def diaspora_session(device_host, app_domain):
    session = requests.session()
    response = session.get('https://{0}/login'.format(device_host),
                           headers={"Host": app_domain},
                           allow_redirects=False, verify=False)
    assert response.status_code == 301, response.text

    response = session.post('https://{0}/users/sign_in'.format(device_host),
                            headers={"Host": app_domain},
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


def test_activate_device(device_host, main_domain, domain):
    
    response = requests.post('http://{0}:81/rest/activate'.format(device_host),
                             data={'main_domain': main_domain,
                                   'redirect_email': REDIRECT_USER,
                                   'redirect_password': REDIRECT_PASSWORD,
                                   'user_domain': domain,
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


def test_install(app_archive_path, device_host, app_domain):
    local_install(device_host, DEVICE_PASSWORD, app_archive_path)


def test_create_user(app_domain, device_host):

    response = requests.post('https://{0}/users'.format(app_domain),
                             verify=False, allow_redirects=False,
                             data={
                                 'user[email]': REDIRECT_USER,
                                 'user[username]': DEVICE_USER,
                                 'user[password]': DEVICE_PASSWORD,
                                 'user[password_confirmation]': DEVICE_PASSWORD,
                                 'commit': "Sign+up"
                             })
    assert response.status_code == 302, response.text


# def test_upload_profile_photo(diaspora_session, app_domain, device_host):
#
#     response = diaspora_session.get('https://{0}/profile/edit'.format(device_host),
#                                     headers={"Host": app_domain},
#                                     allow_redirects=False, verify=False)
#     assert response.status_code == 200, response.text
#
#     soup = BeautifulSoup(response.text, "html.parser")
#     token = soup.find_all('meta', {'name': 'csrf-token'})[0]['content']
#
#     response = diaspora_session.post('https://{0}/photos'.format(device_host),
#                                      headers={
#                                          "Host": app_domain,
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
