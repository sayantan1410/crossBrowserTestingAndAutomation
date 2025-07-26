import concurrent.futures
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from main import run_test
import logging

import json

# Loading config
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Assigning variables
BROWSERSTACK_USERNAME = config["BROWSERSTACK_USERNAME"]
BROWSERSTACK_ACCESS_KEY = config["BROWSERSTACK_ACCESS_KEY"]
NO_OF_ARTICLES = config["NO_OF_ARTICLES"]
BROWSER_COMBINATIONS = config["BROWSER_COMBINATIONS"]


logging.basicConfig(
    level=logging.INFO,
    filemode="w",
    format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
    filename="output.log",
)


def log(msg):
    print(msg, file=sys.stdout, flush=True)

def run_test_bstack(capabilities, NO_OF_ARTICLES):
    
    caps = capabilities.copy()
    caps['browserstack.user'] = BROWSERSTACK_USERNAME
    caps['browserstack.key'] = BROWSERSTACK_ACCESS_KEY
    caps['name'] = 'Parallel Test Example'
    
    url = "https://hub-cloud.browserstack.com/wd/hub"
    web_url = "https://elpais.com/"
    
    driver = None  # Initializing driver variable
    try:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.safari.options import Options as SafariOptions
        
        # Creating appropriate options based on browser
        options = ChromeOptions()  # Chrome options is default
        if 'browser' in caps:
            if caps['browser'].lower() == 'firefox':
                options = FirefoxOptions()
            elif caps['browser'].lower() == 'safari':
                options = SafariOptions()
        
        for key, value in caps.items():
            options.set_capability(key, value)
        
        driver = webdriver.Remote(command_executor=url, options=options)
        print(driver.session_id)
        logging.info(f"Driver created with options for capabilities: {caps}")
        run_test(driver, web_url, caps, NO_OF_ARTICLES)
        logging.info(f"Test completed successfully for: {caps}")
        
    except Exception as e:
        logging.error(f"Failed to create driver with options for {caps}: {e}", exc_info=True)
        raise
    finally:
        if driver:
            try:
                driver.quit()
                executor_object = {
                'action': 'setSessionStatus',
                'arguments': {
                    'status': "passed",
                    'reason': "driver.quit() executed successfully"
                    }
                }
                browserstack_executor = 'browserstack_executor: {}'.format(json.dumps(executor_object))
                driver.execute_script(browserstack_executor)
                driver.quit()
                logging.info(f"Driver closed for: {caps}")
            except Exception as e:
                logging.error(f"Error closing driver: {e}")

# Execute in parallel threads
if __name__ == "__main__":
    logging.info(f"Starting tests with browser combinations: {BROWSER_COMBINATIONS}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submitting all browser combinations to the thread pool
        future_to_capabilities = {
            executor.submit(run_test_bstack, capabilities, NO_OF_ARTICLES): capabilities 
            for capabilities in BROWSER_COMBINATIONS
        }
        
        # Waiting for all tasks to complete and handle results
        for future in concurrent.futures.as_completed(future_to_capabilities):
            capabilities = future_to_capabilities[future]
            try:
                result = future.result()
                logging.info(f"Completed test for: {capabilities}")
            except Exception as e:
                logging.error(f"Test failed for {capabilities}: {e}", exc_info=True)