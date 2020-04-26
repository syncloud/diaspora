import os
import shutil
import time
from os.path import dirname, join, exists

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'app_log')
screenshot_dir = join(DIR, 'screenshot')


@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode, artifact_dir):
    def module_teardown():
        tmp_dir = '/tmp/syncloud/ui'
        device.activated()
        device.run_ssh('mkdir -p {0}'.format(tmp_dir), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.ui.{1}.log'.format(tmp_dir, ui_mode), throw=False)
        device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(tmp_dir, ui_mode), throw=False)
      
        device.scp_from_device('{0}/*'.format(tmp_dir), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)    


def test_start(module_setup, app, domain, device_host):
    add_host_alias_by_ip(app, domain, device_host)


def test_index(driver, app_domain, ui_mode, screenshot_dir):
    url = "https://{0}".format(app_domain)
    driver.get(url)
    mobile_driver.get(url)
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'index-' + ui_mode)

    
def test_signup(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/users/sign_up".format(app_domain))
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'signup-' + ui_mode)

    user_email = driver.find_element_by_id("user_email")
    user_email.send_keys('user@example.com')
    user_username = driver.find_element_by_id("user_username")
    user_username.send_keys('username')
    user_password = driver.find_element_by_id("user_password")
    user_password.send_keys('password')
    user_password_confirmation = driver.find_element_by_id('user_password_confirmation')
    user_password_confirmation.send_keys('password')
    user_password_confirmation.send_keys(Keys.RETURN)
    user_password_confirmation.submit()

    screenshots(driver, screenshot_dir, 'signup-credentials-' + ui_mode)

    time.sleep(100)
    
    screenshots(driver, screenshot_dir, 'signup-done-' + ui_mode)


def test_stream(driver, app_domain, ui_mode, screenshot_dir):

    url = "https://{0}/stream".format(app_domain)
    driver.get(url)
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'stream-first-time-' + ui_mode)
    
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'stream+' + ui_mode)
    

def test_post(driver, app_domain, ui_mode, screenshot_dir):
   
    url = "https://{0}/stream".format(app_domain)
    driver.get(url)
    
    time.sleep(10)
    status_message_text = driver.find_element_by_id("status_message_text")
    status_message_text.send_keys('test message')
    status_message_text.submit()
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'post-' + ui_mode)
 

def test_profile_picture(driver, app_domain, ui_mode, screenshot_dir):
   
    url = "https://{0}/profile/edit".format(app_domain)
    driver.get(url)
    time.sleep(10)
        
    screenshots(driver, screenshot_dir, 'profile-' + ui_mode)
    
    file = driver.find_element_by_css_selector('input[type="file"]')
    driver.execute_script("arguments[0].removeAttribute('style')", file)
    time.sleep(2)
    screenshots(driver, screensho_dir, 'profile-file-style-' + ui_mode)
    
    file.send_keys(join(DIR, 'images', 'profile.jpeg'))
    screenshots(driver, screenshot_dir, 'profile-before-new-picture-' + ui_mode)
    
    #file.submit()

    time.sleep(10)

    screenshots(driver, screenshot_dir, 'profile-new-picture-' + ui_mode)
    

