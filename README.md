# Web Scraper with Dynamic Data Structuring

## Overview

This project is a versatile web scraping tool designed to extract and structure data from any website, dynamically adjusting to the data structure without hardcoded parameters. The scraper uses **Selenium** and **BeautifulSoup** for web interaction and HTML parsing, while the **Groq LLM** models handle data alignment and unification. The data is output in **JSON** and **Excel** formats for easy analysis.

### Key Features:
- **Flexible Scraping**: No hardcoded fields. Adapts to any website’s structure.
- **Dynamic Column Mapping**: Uses an LLM to infer and unify columns across different websites.
- **Multi-format Outputs**: Saves data in Markdown, JSON, and Excel.
- **Scalable Design**: Handles large datasets with token management for API efficiency.
- **User-Agent Rotation**: Mimics human browsing behavior to avoid detection.



### Requirements

### Python Dependencies

pip install -r requirements.txt


Dependencies include:

* pandas: Data handling.
* BeautifulSoup (bs4): HTML parsing.
* Selenium: Web automation.
* html2text: Converts HTML to Markdown.
* pydantic: Creates dynamic models.
* tiktoken: Manages tokenization for the LLMs.

## Tools Required

* ChromeDriver: Required by Selenium. Download [here](https://googlechromelabs.github.io/chrome-for-testing/#stable).
* Groq API: For LLM-based data processing. Add your API key to the .env file.



## Setup

1. Clone the Repository


git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name



## 2. Install Dependencies


pip install -r requirements.txt


## 3. Configure Environment Variables

In the project root, create a .env file:

# .env file
GROQ_API_KEY=your-groq-api-key



## 4. Add URLs to Scrape

Update data_source.py with the URLs to scrape:

URLS = [
    "https://example.com/page1",
    "https://example.com/page2"
]

## 5. Download ChromeDriver

Download and place it in the project root.

Usage
Run the Scraper program

python main.py

## Output Formats

* Markdown: Cleaned webpage content.
* JSON: Structured data output.
* Excel: Human-readable structured data.

Files are saved in output/, with a timestamped directory for each session:

output/
└── 20241017_123456/
    ├── scraped_data_20241017123456.md
    ├── formatted_data_20241017123456.json
    └── formatted_data_20241017123456.xlsx


## Dynamic Field Handling

The scraper dynamically adjusts field names during the scraping process. To extend or modify fields, you can customize this logic within scraper.py.