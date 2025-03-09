import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, create_model
import html2text
import tiktoken
import os
import time, datetime
import json
import httpx
import re
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from groq import Groq
from typing import List, Type
from data_source import URLS
from utils import USER_AGENTS,MODEL_PRICING,CHROME_HEADLESS_OPTIONS,AI_EXTRACTION_USER_PROMPT,LLAMA_FULL_MODEL_NAME,GROQ_LLAMA_FULL_MODEL_NAME, EXTRACTION_SYSTEM_MESSAGE

from chromium_helper import get_playwright_chromium_path, get_browser_version


load_dotenv()

# Set up the Chrome WebDriver options

def initialize_selenium():
    """
    Sets up and initializes the Selenium Chrome WebDriver.
    Adds randomized user agents and headless browser options for scraping.
    """
    options = Options()

    # Randomly select a user agent from the imported list
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")

    # Apply headless or other options as needed
    for option in CHROME_HEADLESS_OPTIONS:
        options.add_argument(option)

    chromium_path = get_playwright_chromium_path()
    print(f"Using Chromium binary at: {chromium_path}")
    options.binary_location = chromium_path

    # Retrieve the Chromium browser version
    browser_version = get_browser_version(chromium_path)
    print(f"Detected Chromium version: {browser_version}")

    # Use webdriver_manager to install the chromedriver matching the browser version
    from webdriver_manager.chrome import ChromeDriverManager
    service = Service(ChromeDriverManager(driver_version=browser_version).install())

    # Return the configured WebDriver instance
    driver = webdriver.Chrome(service=service, options=options)
    return driver

    

def click_cookies_accept(driver):
    """
    Searches for common cookie consent popups on a webpage and clicks 'Accept'.
    The function checks for a variety of text variations in multiple element types (button, a, div).
    """
    try:
        # Wait for any potential cookie popup to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button | //a | //div"))
        )
        
         # List of common accept/agree texts across websites
        accept_text_variations = [
            "accept", "agree", "allow", "consent", "continue", "ok", "I agree", "got it"
        ]
        
        # Check several HTML tags for these text variations
        for tag in ["button", "a", "div"]:
            for text in accept_text_variations:
                try:
                    # Create an XPath expression to locate elements that match these patterns
                    element = driver.find_element(By.XPATH, f"//{tag}[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                    if element:
                        element.click() # Click the button if found
                        print(f"Clicked the '{text}' button.")
                        return
                except:
                    continue

        print("No 'Accept Cookies' button found.")
    
    except Exception as e:
        print(f"Error finding 'Accept Cookies' button: {e}")




def fetch_html_selenium(url, driver):
    driver = initialize_selenium()
    try:
        # Load the webpage
        driver.get(url)
        
        # Simulate human interaction by waiting and scrolling
        time.sleep(1)  # Mimic time spent by a user on the web page 
        driver.maximize_window()
        

        # Handle cookie consent popup
        click_cookies_accept(driver)

        # Scroll to different sections of the page to mimic a real user's interaction
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(random.uniform(1.1, 1.8))  # Simulate time taken to scroll and read
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1.2);")
        time.sleep(random.uniform(1.1, 1.8))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1);")
        time.sleep(random.uniform(1.1, 2.1))
        time.sleep(3)

        # Get the full page's HTML source
        html = driver.page_source
        return html
    finally:
        driver.quit() # Close the WebDriver after completion


def clean_html(html_content):
    """
    Cleans the raw HTML content by removing unwanted tags like headers and footers.
    Uses BeautifulSoup to parse and modify the HTML structure.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted header and footer sections
    for element in soup.find_all(['header', 'footer']):
        element.decompose()  # Remove the tag and its content

    return str(soup)


def html_to_markdown(html_content):
    """
    Converts cleaned HTML content into Markdown format using the html2text library.
    This simplifies the structure of the webpage for further text processing.
    """

    # Clean HTML before conversion
    cleaned_html = clean_html(html_content)  
    
    # Initialize the markdown converter and convert the HTML
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False # Preserve links in the markdown
    markdown_content = markdown_converter.handle(cleaned_html)
    
    return markdown_content


    
def save_raw_data(raw_data: str, output_folder: str, file_name: str):
    """
    Saves raw markdown data to a file in the specified output directory.
    Ensures that the directory exists before saving.
    """
    os.makedirs(output_folder, exist_ok=True)
    raw_output_path = os.path.join(output_folder, file_name)
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
    print(f"Raw data saved to {raw_output_path}")
    return raw_output_path

# Remove URLs from a given markdown file using a regex pattern
def remove_urls(file_path):
    # Regex pattern to find URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    # Create a new filename for the cleaned content
    base, ext = os.path.splitext(file_path)
    new_file_path = f"{base}_cleaned{ext}"

    # Read the original markdown content
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    # Replace URLs with an empty string
    cleaned_content = re.sub(url_pattern, '', markdown_content)

    # Write the cleaned content back to a new file
    with open(new_file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)
    print(f"Cleaned file saved as: {new_file_path}")
    return cleaned_content

# Dynamically create a Pydantic model for listing fields
def dynamic_listing_model(field_names: List[str]) -> Type[BaseModel]:
    """
    Dynamically generates a Pydantic model based on a list of field names.
    This model will represent a structured listing extracted from the markdown content.
    """
    # Create a dictionary of field definitions for each field name
    field_definitions = {field: (str, ...) for field in field_names}
    # Return the dynamically created model
    return create_model('DynamicListingModel', **field_definitions)

# Create a container model that holds a list of listings (Pydantic models)
def listings_container_model(listing_model: Type[BaseModel]) -> Type[BaseModel]:
    """
    Generates a Pydantic container model that holds a list of listing models.
    The container model can be used to organize multiple listings together.
    """
    return create_model('DynamicListingsContainer', listings=(List[listing_model], ...))



# Ensure text does not exceed the token limit for the chosen model
def token_limit(text, model, max_tokens=120000):
    """
    Trims the input text if it exceeds the specified token limit for the LLM model.
    This function encodes the text, counts tokens, and decodes a truncated version if necessary.
    """
    encoder = tiktoken.encoding_for_model(model)
    tokens = encoder.encode(text)
    if len(tokens) > max_tokens:
        trimmed_text = encoder.decode(tokens[:max_tokens])
        return trimmed_text
    return text

def system_message(listing_model: BaseModel) -> str:
    """
    Dynamically creates a system message for the LLM based on the schema of the listing model.
    The system message instructs the model to extract and format data into JSON.
    """
    # Extract the model's JSON schema
    schema_info = listing_model.model_json_schema()

    # Build descriptions for each field in the schema
    field_descriptions = []
    for field_name, field_info in schema_info["properties"].items():
        # Get the field type from the schema info
        field_type = field_info["type"]
        field_descriptions.append(f'"{field_name}": "{field_type}"')

    # Create the JSON schema structure for the listings
    schema_structure = ",\n".join(field_descriptions)

    # Generate the system message dynamically
    system_message = f"""
    You are an intelligent text extraction and conversion assistant. Your task is to extract structured information 
                        from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text, 
                        with no additional commentary, explanations, or extraneous information. 
                        You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                        Please process the following text and provide the output in pure JSON format with no words before or after the JSON:
    Please ensure the output strictly follows this schema:

    {{
        "listings": [
            {{
                {schema_structure}
            }}
        ]
    }} """

    return system_message





def format_data(data, DynamicListingsContainer, DynamicListingModel, selected_model):
    token_counts = {}
    
    try:
        # Create a custom httpx client with no proxy settings
        http_client = httpx.Client()  # No proxies specified
        # Initialize the Groq client with the custom httpx client
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"), http_client=http_client)
        
        if selected_model == "Llama3.1 8B":
            sys_message = system_message(DynamicListingModel)
            completion = client.chat.completions.create(
                model=LLAMA_FULL_MODEL_NAME,
                messages=[
                    {"role": "system", "content": sys_message},
                    {"role": "user", "content": AI_EXTRACTION_USER_PROMPT + data}
                ],
                temperature=0.7,
            )
            response_content = completion.choices[0].message.content
            print(response_content)
            parsed_response = json.loads(response_content)
            token_counts = {
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens
            }
            return parsed_response, token_counts

        elif selected_model == "llama-3.3-70b-versatile":
            sys_message = system_message(DynamicListingModel)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_message},
                    {"role": "user", "content": AI_EXTRACTION_USER_PROMPT + data}
                ],
                model=GROQ_LLAMA_FULL_MODEL_NAME,
            )
            response_content = completion.choices[0].message.content
            parsed_response = json.loads(response_content)
            token_counts = {
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens
            }
            return parsed_response, token_counts
        else:
            raise ValueError(f"Unsupported model: {selected_model}")
    except Exception as e:
        print(f"Error during formatting data: {e}")
        # Return empty values to signal failure (which may trigger attended mode)
        return {}, {}





def save_formatted_data(formatted_data, output_folder: str, json_file_name: str, excel_file_name: str):
    """Save formatted data as JSON and Excel in the specified output folder."""
    os.makedirs(output_folder, exist_ok=True)
    
    # Parse the formatted data if it's a JSON string
    if isinstance(formatted_data, str):
        try:
            formatted_data_dict = json.loads(formatted_data)
        except json.JSONDecodeError:
            raise ValueError("The provided formatted data is a string but not valid JSON.")
    else:
        # Handle data from the model
        formatted_data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data

    # Save the formatted data as JSON
    json_output_path = os.path.join(output_folder, json_file_name)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data_dict, f, indent=4)
    print(f"Formatted data saved to JSON at {json_output_path}")

    # Prepare data for DataFrame
    if isinstance(formatted_data_dict, dict):
        # If the data is a dictionary containing lists, assume these lists are records
        data_for_df = next(iter(formatted_data_dict.values())) if len(formatted_data_dict) == 1 else formatted_data_dict
    elif isinstance(formatted_data_dict, list):
        data_for_df = formatted_data_dict
    else:
        raise ValueError("Formatted data is neither a dictionary nor a list, cannot convert to DataFrame")

    # Create DataFrame
    try:
        df = pd.DataFrame(data_for_df)
        print("DataFrame created successfully.")

        # Save the DataFrame to an Excel file
        excel_output_path = os.path.join(output_folder, excel_file_name)
        df.to_excel(excel_output_path, index=False)
        print(f"Formatted data saved to Excel at {excel_output_path}")
        
        return df
    except Exception as e:
        print(f"Error creating DataFrame or saving Excel: {str(e)}")
        return None

def calculate_price(token_counts, model):
    input_token_count = token_counts.get("input_tokens", 0)
    output_token_count = token_counts.get("output_tokens", 0)
    
    # Calculate the costs
    input_cost = input_token_count * MODEL_PRICING[model]["input"]
    output_cost = output_token_count * MODEL_PRICING[model]["output"]
    total_cost = input_cost + output_cost
    
    return input_token_count, output_token_count, total_cost


def generate_unique_folder_name(url):
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    url_name = re.sub(r'\W+', '_', url.split('//')[1].split('/')[0])  # Extract domain name and replace non-alphanumeric characters
    return f"{url_name}_{timestamp}"


def scrape_urls_list(urls, selected_model):
    """
    Scrapes a list of URLs and extracts specified fields.
    The fields are read from a text file.
    """
    # Use the URLs from data_source.py
    urls = URLS
    """
    if not os.path.exists('fields.txt'):
        print("Error: fields.txt not found.")
        return


    # Read the fields from fields.txt
    fields = read_fields_from_file('fields.txt')

    if not fields:
        print("No fields provided for scraping. Exiting.")
        return"""

    # Generate output folder based on the first URL
    output_folder = os.path.join('output', generate_unique_folder_name(urls[0]))
    os.makedirs(output_folder, exist_ok=True)
    
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0
    all_data = []
    markdown = None  # Store the markdown for the first (or only) URL
    
    for i, url in enumerate(urls, start=1):
        raw_html = fetch_html_selenium(url)
        current_markdown = html_to_markdown(raw_html)
        if i == 1:
            markdown = current_markdown  # Store markdown for the first URL
        
        #input_tokens, output_tokens, cost, formatted_data = scrape_url(url, fields, selected_model, output_folder, i, current_markdown)
        input_tokens, output_tokens, cost, formatted_data = scrape_url(url, selected_model, output_folder, i, current_markdown)
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_cost += cost
        all_data.append(formatted_data)
    
    return output_folder, total_input_tokens, total_output_tokens, total_cost, all_data, markdown


def scrape_url(url: str, fields: List[str], selected_model: str, output_folder: str, file_number: int, markdown: str):
    """Scrape a single URL and save the results."""
    try:
        # Save raw data
        save_raw_data(markdown, output_folder, f'rawData_{file_number}.md')

        # Create the dynamic listing model
        DynamicListingModel = dynamic_listing_model(fields)

        # Create the container model that holds a list of the dynamic listing models
        DynamicListingsContainer = listings_container_model(DynamicListingModel)
        
        # Format data
        formatted_data, token_counts = format_data(markdown, DynamicListingsContainer, DynamicListingModel, selected_model)
        
        # Save formatted data
        save_formatted_data(formatted_data, output_folder, f'sorted_data_{file_number}.json', f'sorted_data_{file_number}.xlsx')

        # Calculate and return token usage and cost
        input_tokens, output_tokens, total_cost = calculate_price(token_counts, selected_model)
        return input_tokens, output_tokens, total_cost, formatted_data

    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return 0, 0, 0, None
