import os
import shutil
from os.path import dirname, join, exists
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'app_log')
screenshot_dir = join(DIR, 'screenshot')

@pytest.fixture(scope="module")
def driver():

    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    firefox_path = '{0}/firefox/firefox'.format(DIR)
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    profile = webdriver.FirefoxProfile()
    profile.add_extension('{0}/JSErrorCollector.xpi'.format(DIR))
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    driver = webdriver.Firefox(profile, capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR), firefox_binary=binary, executable_path=join(DIR, 'geckodriver/geckodriver'))
    #driver.set_page_load_timeout(30)
    #print driver.capabilities['version']
    return driver


def test_login(driver, user_domain):

    driver.get("https://{0}".format(user_domain))
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'login')
    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_signup(driver, user_domain):

    driver.get("https://{0}/users/sign_up".format(user_domain))
    time.sleep(10)
    
    screenshots(driver, screenshot_dir, 'signup_empty')
    print(driver.page_source.encode("utf-8"))
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
    screenshots(driver, screenshot_dir, 'signup')
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'signup_done')

    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))

def screenshots(driver, dir, name):
    desktop_w = 1280
    desktop_h = 2000
    driver.set_window_position(0, 0)
    driver.set_window_size(desktop_w, desktop_h)

    driver.get_screenshot_as_file(join(dir, '{}.png'.format(name)))

    mobile_w = 400
    mobile_h = 2000
    driver.set_window_position(0, 0)
    driver.set_window_size(mobile_w, mobile_h)
    driver.get_screenshot_as_file(join(dir, '{}-mobile.png'.format(name)))
    
    driver.set_window_position(0, 0)
    driver.set_window_size(desktop_w, desktop_h)

