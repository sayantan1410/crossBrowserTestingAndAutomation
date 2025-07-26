import logging
import os
import re
import shutil
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from translate import translate_to_english
from collections import Counter


logging.basicConfig(
    level=logging.INFO,
    filemode="w",
    format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
    filename="output.log",
)

def save_image_with_thread_folder(caps, article_index, img_index, img_url):

    base_folder = "Images"
    thread_folder = f"capability_{caps['id']}"
    full_folder_path = os.path.join(base_folder, thread_folder)
    
    # Creating folders if they don't exist
    os.makedirs(full_folder_path, exist_ok=True)
    
    # Downloading image
    img_data = requests.get(img_url).content
    
    # Creating filename with thread prefix so that multiple threads doesn't save in conflicting locations
    filename = f"th{caps['id']}_article_{article_index+1}_{img_index+1}.jpg"
    full_file_path = os.path.join(full_folder_path, filename)
    
    # Saving image
    with open(full_file_path, 'wb') as f:
        f.write(img_data)
    del img_data #free the memory for image data once image is saved
    
    print(f"Image saved: {full_file_path}")
    return full_file_path

def cleanup_images_folder():
    """Clean up images folder before starting"""
    if os.path.exists("Images"):
        shutil.rmtree("Images")

def is_valid_content(text):
    """Check if content is valid and not empty"""
    return text and text.strip() and len(text.strip()) > 3

def safe_get_text(element):
    """Safely extract text from element with validation"""
    try:
        text = element.text.strip()
        return text if is_valid_content(text) else None
    except:
        return None

def find_opinion_section(driver, wait):
    """Find Opinion section with fallback selectors"""
    opinion_selectors = [
        "//nav//a[contains(text(), 'Opinión')]",           # Primary
        "//nav//a[contains(@href, 'opinion')]",            # Fallback 1
        "//a[contains(text(), 'Opinion')]",                # Fallback 2
        "//nav//a[contains(text(), 'Columnas')]",          # Fallback 3
        "//nav//a[contains(@class, 'opinion')]"            # Fallback 4
    ]
    
    for selector in opinion_selectors:
        try:
            opinion_link = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            return opinion_link
        except Exception as e:
            logging.error(f"exception - {e}")
    
    raise Exception("Could not find Opinion section with any known selector")

        

def run_test(driver, url, caps, no_of_article):
    is_mobile = 'device' in caps
    driver.get(url)
    if(not is_mobile):
        try:
            driver.maximize_window()
        except Exception as e:
            logging.error(f"exception while maximizing window - {e}")
    wait = WebDriverWait(driver, 30)
    cleanup_images_folder() # so that the folder doesn't grow in size indefinitely as we keep running the tests
    time.sleep(3) # explicit time.sleep for the cookie notification to come in.
    try:
        time.sleep(3)
        if is_mobile  and ('iPhone' in caps['device']):
           wait.until( EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'pmConsentWall-button') and contains(text(), 'Accept and continue')]"))).click()
        else:
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            accept_button.click()
    except Exception as e:
        logging.error(f"exception = {e}" )

    if is_mobile:
        wait.until(EC.element_to_be_clickable((By.ID, "btn_open_hamburger"))).click()
        time.sleep(2)  # explicit time.sleep to allow menu to fully slide in

    try:
        opinion_link = find_opinion_section(driver, wait)
        driver.execute_script("arguments[0].click();", opinion_link)
    except Exception as e:
        logging.error(f"exception - {e}")

    h2_texts = []
    translated_h2_texts = []
    paragraph_texts = []
    freq_map = Counter()
        
    try:
        article_elements = driver.find_elements(By.XPATH, "//div[starts-with(@class, 'b-d_')]//article")
        for index, article in enumerate(article_elements):
            if index < no_of_article:
                try:
                    fresh_articles = driver.find_elements(By.XPATH, "//div[starts-with(@class, 'b-d_')]//article")
                    article = fresh_articles[index]
                    h2 = article.find_element(By.XPATH, ".//header//h2")
                    h2_text = safe_get_text(h2)
                    if h2_text:
                        translated_h2_text = translate_to_english(h2_text)
                        if translated_h2_text:
                            words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", translated_h2_text)
                            words = [word.lower() for word in words]
                            freq_map.update(words)
                            h2_texts.append(h2_text)
                            translated_h2_texts.append(translated_h2_text)
                            print(f"capability id {caps['id']} - [{index+1}] Heading: {h2_text}")
                            print(f"capability id {caps['id']} - Translated text : {translated_h2_text}")
                except Exception as e:
                    logging.error(f"exception = {e}" )
                
                try:
                    fresh_articles = driver.find_elements(By.XPATH, "//div[starts-with(@class, 'b-d_')]//article")
                    article = fresh_articles[index]
                    p_element = article.find_element(By.XPATH, ".//p")
                    paragraph = safe_get_text(p_element)
                    if paragraph:
                        paragraph_texts.append(paragraph)
                        print(f"capability id {caps['id']} - [{index+1}] Paragraph: {paragraph}")
                except Exception as e:
                    logging.error(f"exception = {e}" )

                try:
                    fresh_articles = driver.find_elements(By.XPATH, "//div[starts-with(@class, 'b-d_')]//article")
                    article = fresh_articles[index]
                    all_images = article.find_elements(By.XPATH, ".//figure//img")
                    for ind, img in enumerate(all_images):
                        img_url = img.get_attribute("src")
                        save_image_with_thread_folder(caps, index, ind, img_url)
                except Exception as e:
                    logging.error(f"exception = {e}" )
            else:
                break

    except Exception as e:
        logging.error(f"exception = {e}" )
    article_elements.clear()
    del article_elements

    print("----Repeated Words----")
    for key, value in freq_map.items():
        if value > 1:
            print(f"Word : {key} - Repetation: {value}")