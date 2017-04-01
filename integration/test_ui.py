import os
import shutil
from os.path import dirname, join, exists

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'app_log')


def test_web_with_selenium(user_domain):

    os.environ['PATH'] = os.environ['PATH'] + ":" + join(DIR, 'geckodriver')

    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps["binary"] = "/usr/bin/firefox"
    caps["acceptInsecureCerts"] = True

    profile = webdriver.FirefoxProfile()
    profile.set_preference("webdriver.log.file", "{0}/firefox.log".format(log_dir))
    profile.accept_untrusted_certs = True
    driver = webdriver.Firefox(profile, capabilities=caps)

    screenshot_dir = join(DIR, 'screenshot')
    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    driver.get("https://{0}".format(user_domain))
    WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))

    