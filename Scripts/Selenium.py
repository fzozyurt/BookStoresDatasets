import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def add_driver_options(options):
    """
    Add configurable options
    """
    logging.info('add_driver_options function called')
    chrome_options = Options()
    for opt in options:
        chrome_options.add_argument(opt)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
    logging.debug('Driver options configured')
    return chrome_options

def initialize_driver(browser="edge"):
    """
    Initialize the web driver
    """
    logging.info(f'İnitialize Browser : {browser}')
    if browser == "chrome":
        logging.info('initialize_driver function called')
        driver_config = {
            "options": [
                "--headless",
                "--no-sandbox",
                "--start-fullscreen",
                "--allow-insecure-localhost",
                "--disable-dev-shm-usage",
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36"
            ],
        }
        logging.debug(f'Driver configuration: {driver_config}')
        options = add_driver_options(driver_config["options"])
        driver = webdriver.Chrome(options=options)
    elif browser =="edge":
        driver = webdriver.Edge()
    logging.debug('Web driver initialized')
    return driver