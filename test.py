from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Define the path to your chromedriver
chromedriver_path = "./chromedriver"  # Update this path

# Set up Chrome options
chrome_options = Options()
chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # Ensure this path is correct

# Set up the ChromeDriver service
service = Service(executable_path=chromedriver_path)

# Initialize the WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Example action: Open Google's homepage
driver.get("https://www.google.com")
print(driver.title)

# Close the browser
driver.quit()
