import os
import shutil
import time
from os.path import dirname, join, exists

import pytest
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'app_log')
screenshot_dir = join(DIR, 'screenshot')


def new_profile(user_agent):
    profile = webdriver.FirefoxProfile()
    profile.add_extension('{0}/JSErrorCollector.xpi'.format(DIR))
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    profile.set_preference("general.useragent.override", user_agent)

    return profile

def new_driver(profile):

    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    firefox_path = '{0}/firefox/firefox'.format(DIR)
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    return webdriver.Firefox(profile, capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR),
                             firefox_binary=binary, executable_path=join(DIR, 'geckodriver/geckodriver'))


@pytest.fixture(scope="module")
def driver():
    profile = new_profile("Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0")
    driver = new_driver(profile)
    driver.set_window_position(0, 0)
    driver.set_window_size(1280, 2000)
    return driver
    
    
@pytest.fixture(scope="module")
def mobile_driver():    
    profile = new_profile("Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16")
    driver = new_driver(profile)
    driver.set_window_position(0, 0)
    driver.set_window_size(400, 700)
    return driver
    

def test_login(driver, mobile_driver, user_domain):
    url = "https://{0}".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)
    time.sleep(10)
    
    screenshots(driver, 'login')
    screenshots(mobile_driver, 'login-mobile')
    
    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_signup(driver, mobile_driver, user_domain):

    url = "https://{0}/users/sign_up".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)
    time.sleep(10)
    
    screenshots(driver, 'signup')
    screenshots(mobile_driver, 'signup-mobile')
     
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
    
    screenshots(driver, 'signup-credentials')
    time.sleep(100)
    
    screenshots(driver, 'signup-done')

    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_stream(driver, mobile_driver, user_domain):

    url = "https://{0}/stream".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)
    time.sleep(10)
    
    screenshots(driver, 'stream-first-time')
    screenshots(mobile_driver, 'stream-first-time-mobile')
    
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    driver.find_element_by_css_selector('.popover-title .close').click()
    
    screenshots(driver, 'stream')
    screenshots(mobile_driver, 'stream-mobile')

    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_post(driver, mobile_driver, user_domain):
   
    url = "https://{0}/stream".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)
    
    time.sleep(10)
    status_message_text = driver.find_element_by_id("status_message_text")
    status_message_text.send_keys('test message')
    status_message_text.submit()
    time.sleep(10)
    
    screenshots(driver, 'post')
    screenshots(mobile_driver, 'post-mobile')
    
    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_profile_picture(driver, mobile_driver, user_domain):
   
    url = "https://{0}/profile/edit".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)    
    time.sleep(10)
        
    screenshots(driver, 'profile')
    screenshots(mobile_driver, 'profile-mobile')
    
    # upload new photo
    time.sleep(10)

    screenshots(driver, 'profile-new-picture')
    
    mobile_driver.get(url)    
    time.sleep(10)
    screenshots(mobile_driver, 'profile-new-picture-mobile')
    
    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def screenshots(driver, name):
    driver.get_screenshot_as_file(join(screenshot_dir, '{0}.png'.format(name)))
    with open(join(screenshot_dir, '{0}.html'.format(name)), "w") as f:
        f.write(driver.page_source.encode("utf-8"))
 

 