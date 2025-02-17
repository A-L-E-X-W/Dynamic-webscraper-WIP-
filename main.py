import os
import re
import json
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup
from web_scraper import fetch_html_selenium, html_to_markdown, scrape_url
from data_source import URLS
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from fields import field_tags
from chromium_helper import initialize_selenium  # Import our custom helper

# Import the PDF crawler module (new functionality)
from pdf_crawler import crawl_for_pdfs

def generate_unique_folder_name(url):
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path.split('/')[0]
    domain = re.sub(r'^www\.', '', domain)
    clean_domain = re.sub(r'\W+', '_', domain)
    return f"{clean_domain}_{timestamp}"

def extract_pagination_links(soup, base_url):
    """
    Extracts pagination URLs from a BeautifulSoup object.
    """
    pagination_urls = []
    pagination = soup.find("nav", class_="woocommerce-pagination")
    
    if pagination:
        for link in pagination.find_all("a", href=True):
            full_url = urljoin(base_url, link['href'])
            if full_url not in pagination_urls:
                pagination_urls.append(full_url)

    return pagination_urls

def attended_mode(driver, url):
    """
    The purpose of the attended mode is to manage:

    1. Login: 

    When you are needed to login to a site to be able to get the data you want.

    2. UI interaction (clicks...): 
    
    If for example the cookie accept function isn't working for a specific site you can help the scrapeing process by navigating to the cookie accept button click on it and then continue the scraping process.

    Another example is if you need to click on a button to get certain information that you want, like an extended button, show more, and so on. This cannot be done by the program so you will need to use the attended mode to manually click the button and then continue the scraping.

    3. Fallback method: 
    
    In the case of when the normal scraping process isn't working instead of the program crashing or stops the scraping process you will be able to manually interact with the process like in the two eariler examples 1 and 2.
    """
    # Open the specified URL in the browser for attended mode
    print(f"Attended mode activated for {url}. Please navigate to the required section and press Enter to continue.")
    
    # Navigate to the intended URL
    driver.get(url)
    
    # Wait for user input to continue
    input("Press Enter to continue after manual navigation...")
    
    # Return the current page source after user navigation
    return driver.page_source

def scrape_multiple_urls(urls, fields, selected_model):
    output_folder = os.path.join('output', generate_unique_folder_name(urls[0]))
    os.makedirs(output_folder, exist_ok=True)

    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0
    all_data = []
    first_url_markdown = None

    # Use our custom initialization function instead of a default call
    driver = initialize_selenium()

    

    # original
    #driver = webdriver.Chrome()  # Adjust based on your setup

    

    for url in urls:
        page_urls_to_scrape = [url]
        scraped_urls = set()

        while page_urls_to_scrape:
            current_url = page_urls_to_scrape.pop(0)
            if current_url in scraped_urls:
                continue

            raw_html = fetch_html_selenium(current_url, driver)
            soup = BeautifulSoup(raw_html, "html.parser")
            markdown = html_to_markdown(raw_html)

            if first_url_markdown is None:
                first_url_markdown = markdown

            input_tokens, output_tokens, cost, formatted_data = scrape_url(
                current_url, fields, selected_model, output_folder, len(all_data) + 1, markdown)

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_cost += cost

            print(f"\nFormatted data for URL {current_url}: {formatted_data}")  # Debugging line













           

            # original
            """
            # Check for missing fields, ensuring formatted_data is valid
            if isinstance(formatted_data, dict) and 'listings' in formatted_data:
                listings = formatted_data['listings']
                # Check if the listings are empty or if all fields in listings are empty
                if not listings or all(not item.get('weather') and not item.get('water') for item in listings):
                    missing_fields = ['weather', 'water']  # Define what you consider as missing fields
                else:
                    missing_fields = []
            else:
                print(f"Warning: formatted_data for {current_url} is not in the expected format: {formatted_data}")
                missing_fields = ['weather', 'water']  # Treat this case as missing fields

            print(f"Missing fields detected for {current_url}: {missing_fields}")  # Debugging line

            if missing_fields:
                print(f"Entering attended mode for {current_url} due to missing fields.")
                raw_html = attended_mode(driver, current_url)  # Manual navigation
                # Re-scrape with the updated page source after manual navigation
                input_tokens, output_tokens, cost, formatted_data = scrape_url(
                    current_url, fields, selected_model, output_folder, len(all_data) + 1, html_to_markdown(raw_html))
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_cost += cost
            """
            
            # New 
            
            # Check for missing fields based on field_tags from fields.py
            missing_fields = []
            if isinstance(formatted_data, dict) and 'listings' in formatted_data:
                listings = formatted_data['listings']
                for field in field_tags:
                    # If there are no listings or every listing is missing a non-empty value for this field,
                    # consider the field as missing.
                    if not listings or all(not item.get(field) for item in listings):
                        missing_fields.append(field)
            else:
                print(f"Warning: formatted_data for {current_url} is not in the expected format: {formatted_data}")
                missing_fields = field_tags.copy()  # Treat all as missing in this case

            print(f"Missing fields detected for {current_url}: {missing_fields}")  # Debugging line

            if missing_fields:
                print(f"Entering attended mode for {current_url} due to missing fields.")
                raw_html = attended_mode(driver, current_url)  # Manual navigation
                # Re-scrape with the updated page source after manual navigation
                input_tokens, output_tokens, cost, formatted_data = scrape_url(
                    current_url, fields, selected_model, output_folder, len(all_data) + 1, html_to_markdown(raw_html))
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_cost += cost
            
            
                


            if formatted_data is not None:  # Ensure we only append valid data
                all_data.append(formatted_data)
            else:
                print(f"Warning: No valid formatted_data to append for {current_url}")

            scraped_urls.add(current_url)

            # Extract and queue pagination URLs
            pagination_urls = extract_pagination_links(soup, current_url)
            for page_url in pagination_urls:
                if page_url not in scraped_urls and page_url not in page_urls_to_scrape:
                    page_urls_to_scrape.append(page_url)
                    print(f"Added new page URL to scrape: {page_url}")

    driver.quit()
    return output_folder, total_input_tokens, total_output_tokens, total_cost, all_data, first_url_markdown



def read_fields_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            fields = [line.strip() for line in f if line.strip()]
        return fields
    except Exception as e:
        print(f"Error reading fields from file: {e}")
        return []

def perform_scrape():
    urls = URLS
    model_selection = "Groq Llama3.1 70b"
    tags = field_tags

    # --- New Step: Crawl for PDFs ---
    #for url in urls:
     #   print(f"Starting PDF crawl for {url}...")
      #  crawl_for_pdfs(url)

    all_data = []
    output_folder, total_input_tokens, total_output_tokens, total_cost, all_data, first_url_markdown = scrape_multiple_urls(urls, tags, model_selection)

    return all_data, total_input_tokens, total_output_tokens, total_cost, output_folder

if __name__ == "__main__":
    results = perform_scrape()
    all_data, input_tokens, output_tokens, total_cost, output_folder = results

    try:
        combine_command = f"python merged_scraped_data.py {output_folder}"
        subprocess.check_call(combine_command, shell=True)
        print("Combining XLSX files completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while combining XLSX files: {e}")

    print("Scraping completed.")
    print(f"Total Input Tokens: {input_tokens}")
    print(f"Total Output Tokens: {output_tokens}")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Results saved in folder: {output_folder}")
    for data in all_data:
        print(json.dumps(data, indent=4))