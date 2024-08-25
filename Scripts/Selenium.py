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
    try:
        for opt in options:
            chrome_options.add_argument(opt)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
        logging.debug('Driver options configured successfully')
    except Exception as e:
        logging.error(f'Error configuring driver options: {e}')
    return chrome_options

def initialize_driver():
    """
    Initialize the web driver
    """
    logging.info('initialize_driver function called')
    driver_config = {
        "options": add_driver_options(["--headless", "--disable-gpu"])
    }
    try:
        driver = webdriver.Chrome(options=driver_config["options"])
        logging.debug('Web driver initialized successfully')
    except Exception as e:
        logging.error(f'Error initializing web driver: {e}')
        driver = None
    return driver