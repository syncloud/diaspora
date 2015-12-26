import sys
from os import listdir
from os.path import dirname, join, abspath, isdir
import time
from subprocess import check_output

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
device_user = 'user'
device_password = 'password'

def test_remove_logs():
    shutil.rmtree(LOG_DIR, ignore_errors=True)

def test_activate_device(auth):
    email, password, domain, release, version, arch = auth
    response = requests.post('http://localhost:81/server/rest/activate',
                             data={'redirect-email': email, 'redirect-password': password, 'redirect-domain': domain,
                                   'name': device_user, 'password': device_password,
                                   'api-url': 'http://api.syncloud.info:81', 'domain': 'syncloud.info',
                                   'release': release})
    assert response.status_code == 200


def test_install(auth):
    __local_install(auth)

session = requests.session()


# def test_visible_through_platform():
#     response = session.get('http://localhost/diaspora/', allow_redirects=False)
#     assert response.status_code == 200, response.text


# def test_login():
#     response = session.get('http://localhost/diaspora/', allow_redirects=False)
#     soup = BeautifulSoup(response.text, "html.parser")
#     requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
#     response = session.post('http://localhost/diaspora/index.php',
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
    run_scp('root@localhost:/opt/data/platform/log/* {0}'.format(LOG_DIR), password=device_password)

    print('-------------------------------------------------------')
    print('syncloud docker image is running')
    print('connect using: {0}'.format(ssh_command(device_password, SSH)))
    print('-------------------------------------------------------')


def __local_install(auth):
    email, password, domain, release, version, arch = auth
    run_scp('{0}/../diaspora-{1}-{2}.tar.gz root@localhost:/'.format(DIR, version, arch), password=device_password)
    run_ssh('/opt/app/sam/bin/sam --debug install /diaspora-{0}-{1}.tar.gz'.format(version, arch), password=device_password)
    time.sleep(3)
