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
    driver.set_window_size(1024, 768)
    return driver
    
    
@pytest.fixture(scope="module")
def mobile_driver():    
    profile = new_profile("Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16")
    driver = new_driver(profile)
    driver.set_window_position(0, 0)
    driver.set_window_size(400, 2000)
    return driver
    

def test_index(driver, mobile_driver, user_domain):
    url = "https://{0}".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)
    time.sleep(10)
    
    screenshots(driver, 'index')
    screenshots(mobile_driver, 'index-mobile')
    
    
def test_desktop_signup(driver, mobile_driver, user_domain):
    driver.get("https://{0}/users/sign_up".format(user_domain))
    time.sleep(10)
    
    screenshots(driver, 'signup')

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


def test_mobile_signin(mobile_driver, user_domain):

    mobile_driver.get("https://{0}/users/sign_in".format(user_domain))
    screenshots(mobile_driver, 'signin-mobile')

    user_username = mobile_driver.find_element_by_id("user_username")
    user_username.send_keys('username')
    user_password = mobile_driver.find_element_by_id("user_password")
    user_password.send_keys('password')
    user_password.submit()

    screenshots(mobile_driver, 'signin-mobile-progress')

    time.sleep(10)

    screenshots(mobile_driver, 'signin-mobile-done')


def test_stream(driver, user_domain):

    url = "https://{0}/stream".format(user_domain)
    driver.get(url)
    time.sleep(10)
    
    screenshots(driver, 'stream-first-time')
    
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    driver.find_element_by_css_selector('.popover-title .close').click()
    time.sleep(10)
    
    screenshots(driver, 'stream')
    

def test_mobile_stream(mobile_driver, user_domain):

    url = "https://{0}/stream".format(user_domain)
    mobile_driver.get(url)
    time.sleep(10)
    
    screenshots(mobile_driver, 'stream-first-time-mobile')
    

def test_post(driver, user_domain):
   
    url = "https://{0}/stream".format(user_domain)
    driver.get(url)
    
    time.sleep(10)
    status_message_text = driver.find_element_by_id("status_message_text")
    status_message_text.send_keys('test message')
    status_message_text.submit()
    time.sleep(10)
    
    screenshots(driver, 'post')
 

def test_mobile_post(mobile_driver, user_domain):
   
    url = "https://{0}/stream".format(user_domain)
    mobile_driver.get(url)
    
    time.sleep(10)
    screenshots(mobile_driver, 'post-mobile')


def test_profile_picture(driver, mobile_driver, user_domain):
   
    url = "https://{0}/profile/edit".format(user_domain)
    driver.get(url)
    mobile_driver.get(url)    
    time.sleep(10)
        
    screenshots(driver, 'profile')
    screenshots(mobile_driver, 'profile-mobile')
    
    file = mobile_driver.find_element_by_css_selector('input[type="file"]')
    mobile_driver.execute_script("arguments[0].removeAttribute('style')", file)
    time.sleep(2)
    screenshots(mobile_driver, 'profile-mobile-file-style')
    
    file.send_keys(join(DIR, 'images', 'profile.jpeg'))
    screenshots(mobile_driver, 'profile-mobile-before-new-picture')
    
    #file.submit()

    time.sleep(10)

    screenshots(mobile_driver, 'profile-mobile-new-picture')
    
    driver.get(url)    
    time.sleep(10)
    screenshots(driver, 'profile-new-picture')
    

def screenshots(driver, name):
 
    driver.get_screenshot_as_file(join(screenshot_dir, '{0}.png'.format(name)))
  
    with open(join(screenshot_dir, '{0}.html.log'.format(name)), "w") as f:
        f.write(driver.page_source.encode("utf-8"))
   
    with open(join(screenshot_dir, '{0}.js.log'.format(name)), "w") as f:
        try:
            f.write(str(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []')))
        except WebDriverException, e:
            print("unable to get js errors: {0}".format(e))



 