import os
import random
import subprocess
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from utils import USER_AGENTS, CHROME_HEADLESS_OPTIONS

def get_playwright_chromium_path():
    """
    Uses Playwright to obtain the path to the Chromium binary.
    If the binary is not present, installs it via Playwright.
    """
    with sync_playwright() as p:
        chromium_path = p.chromium.executable_path

    # If the expected Chromium binary does not exist, install it
    if not os.path.exists(chromium_path):
        print(f"Chromium not found at {chromium_path}. Installing via Playwright...")
        subprocess.run(["playwright", "install", "chromium"], check=True)
        # Retrieve the path again after installation
        with sync_playwright() as p:
            chromium_path = p.chromium.executable_path
    return chromium_path

def initialize_selenium():
    """
    Initializes the Selenium Chrome WebDriver to use the Chromium binary
    provided by Playwright. This setup is cross-platform (Windows, macOS, Linux).
    """
    options = Options()

    """
    # Set a random user agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")

    
    # You can add any additional Chrome options here
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    """
    
    # Use the helper to obtain the Chromium binary path
    chromium_path = get_playwright_chromium_path()
    print(f"Using Chromium binary at: {chromium_path}")
    options.binary_location = chromium_path

    # Adjust the chromedriver path if needed (here we assume it's in the project root)
    #service = Service("./chromedriver")
    #driver = webdriver.Chrome(service=service, options=options)
    driver = webdriver.Chrome() 
    return driver

