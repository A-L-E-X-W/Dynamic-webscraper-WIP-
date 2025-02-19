import os
import random
import subprocess
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils import USER_AGENTS, CHROME_HEADLESS_OPTIONS

def get_playwright_chromium_path():
    """
    Uses Playwright to obtain the path to the Chromium binary.
    If the binary is not present, installs it via Playwright.
    """
    with sync_playwright() as p:
        chromium_path = p.chromium.executable_path

    if not os.path.exists(chromium_path):
        print(f"Chromium not found at {chromium_path}. Installing via Playwright...")
        subprocess.run(["playwright", "install", "chromium"], check=True)
        with sync_playwright() as p:
            chromium_path = p.chromium.executable_path
    return chromium_path

def get_browser_version(chromium_path):
    """
    Retrieves the version of the Chromium binary by calling it with --version.
    Expected output: "Chromium 133.0.6943.16"
    """
    result = subprocess.run([chromium_path, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    version_str = result.stdout.strip()
    try:
        # Split the output to extract the version number
        version = version_str.split()[1]
    except IndexError:
        raise ValueError(f"Could not parse browser version from output: {version_str}")
    return version

def initialize_selenium():
    """
    Initializes the Selenium Chrome WebDriver using the Chromium binary from Playwright,
    and employs webdriver_manager to automatically manage the correct chromedriver.
    This setup is cross-platform (Windows, macOS, Linux).
    """
    options = Options()
    
    # Apply headless and other options from utils
    for option in CHROME_HEADLESS_OPTIONS:
        options.add_argument(option)
    
    # Set a random user agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")

    # Use Playwright's Chromium binary
    chromium_path = get_playwright_chromium_path()
    print(f"Using Chromium binary at: {chromium_path}")
    options.binary_location = chromium_path

    # Retrieve the browser version from the Chromium binary
    browser_version = get_browser_version(chromium_path)
    print(f"Detected Chromium version: {browser_version}")

    # Pass the version to ChromeDriverManager using 'driver_version'
    service = Service(ChromeDriverManager(driver_version=browser_version).install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver
