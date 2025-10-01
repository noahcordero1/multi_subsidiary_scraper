#!/usr/bin/env python3
"""
Final Multi-Subsidiary Web Scraper for OffeneVergaben.at
Simplified and clean implementation

Requirements:
pip install selenium beautifulsoup4 pandas webdriver-manager
"""

import time
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiSubsidiaryScraperConfig:
    """Configuration class for multi-subsidiary scraper"""

    # Complete ÖBB Subsidiaries Configuration (22 subsidiaries total)
    SUBSIDIARIES = {
        "obb_business": {
            "name": "ÖBB-Business Competence Center",
            "id": "8550",
            "url": "https://offenevergaben.at/auftraggeber/8550"
        },
        "obb_infrastruktur": {
            "name": "ÖBB-Infrastruktur AG",
            "id": "8538",
            "url": "https://offenevergaben.at/auftraggeber/8538"
        },
        "obb_technische_services": {
            "name": "ÖBB-Technische Services Gesellschaft",
            "id": "11068",
            "url": "https://offenevergaben.at/auftraggeber/11068"
        },
        "obb_holding_all": {
            "name": "ÖBB Holding AG mit allen verbundenen Unternehmen",
            "id": "11074",
            "url": "https://offenevergaben.at/auftraggeber/11074"
        },
        "obb_personenverkehr": {
            "name": "ÖBB-Personenverkehr AG",
            "id": "8547",
            "url": "https://offenevergaben.at/auftraggeber/8547"
        },
        "obb_produktion": {
            "name": "ÖBB-Produktion",
            "id": "8545",
            "url": "https://offenevergaben.at/auftraggeber/8545"
        },
        "obb_postbus": {
            "name": "ÖBB-Postbus",
            "id": "8581",
            "url": "https://offenevergaben.at/auftraggeber/8581"
        },
        "obb_holding": {
            "name": "ÖBB-Holding AG",
            "id": "11217",
            "url": "https://offenevergaben.at/auftraggeber/11217"
        },
        "obb_immobilienmanagement": {
            "name": "ÖBB-Immobilienmanagement",
            "id": "11090",
            "url": "https://offenevergaben.at/auftraggeber/11090"
        },
        "obb_werbung": {
            "name": "ÖBB-Werbung",
            "id": "11224",
            "url": "https://offenevergaben.at/auftraggeber/11224"
        },
        "obb_rail_tours": {
            "name": "ÖBB Rail Tours Austria",
            "id": "11446",
            "url": "https://offenevergaben.at/auftraggeber/11446"
        },
        "obb_infrastruktur_ag": {
            "name": "ÖBB-Infrastruktur Aktiengesellschaft",
            "id": "28842",
            "url": "https://offenevergaben.at/auftraggeber/28842"
        },
        "obb_infrastruktur_gb_projekt": {
            "name": "ÖBB-Infrastruktur AG GB Projekt",
            "id": "24814",
            "url": "https://offenevergaben.at/auftraggeber/24814"
        },
        "obb_infrastruktur_2": {
            "name": "ÖBB Infrastruktur AG (2)",
            "id": "36280",
            "url": "https://offenevergaben.at/auftraggeber/36280"
        },
        "obb_personenverkehr_2": {
            "name": "ÖBB Personenverkehr AG (2)",
            "id": "19826",
            "url": "https://offenevergaben.at/auftraggeber/19826"
        },
        "obb_immobilienmanagement_2": {
            "name": "ÖBB-Immobilienmanagement (2)",
            "id": "33422",
            "url": "https://offenevergaben.at/auftraggeber/33422"
        },
        "obb_technische_services_2": {
            "name": "ÖBB-Technische Services-Gesellschaft (2)",
            "id": "37657",
            "url": "https://offenevergaben.at/auftraggeber/37657"
        },
        "obb_personenverkehr_3": {
            "name": "ÖBB-Personenverkehr AG (3)",
            "id": "24566",
            "url": "https://offenevergaben.at/auftraggeber/24566"
        },
        "obb_personenverkehr_4": {
            "name": "ÖBB Personenverkehr AG (4)",
            "id": "29519",
            "url": "https://offenevergaben.at/auftraggeber/29519"
        },
        "obb_personenverkehr_5": {
            "name": "ÖBB Personenverkehr AG (5)",
            "id": "28047",
            "url": "https://offenevergaben.at/auftraggeber/28047"
        },
        "obb_business_2": {
            "name": "ÖBB-Business Competence Center (2)",
            "id": "37203",
            "url": "https://offenevergaben.at/auftraggeber/37203"
        },
        "obb_business_3": {
            "name": "ÖBB-Business Competence Center (3)",
            "id": "37202",
            "url": "https://offenevergaben.at/auftraggeber/37202"
        }
    }

    # Configuration
    BATCH_SIZE = 1000  # Write data every 1000 rows
    OUTPUT_DIR = "../data"

class FinalMultiSubsidiaryScraper:
    """Final simplified multi-subsidiary scraper"""

    def __init__(self):
        self.config = MultiSubsidiaryScraperConfig()
        self.driver = None
        self.ensure_output_dir()

    def ensure_output_dir(self):
        """Ensure output directory exists"""
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver initialized")

    def validate_page_content(self, page_url):
        """Validate if page has content - adapted from your function"""
        try:
            self.driver.get(page_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            time.sleep(1)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tbody = soup.find('tbody')

            # Check if tbody is empty
            if not tbody or len(tbody.find_all('tr')) == 0:
                return False, 0

            rows = tbody.find_all('tr')
            return True, len(rows)

        except Exception as e:
            logger.error(f"Error validating page {page_url}: {str(e)}")
            return False, 0

    def extract_page_data(self):
        """Extract data from current page"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table')

            if not table:
                return [], []

            # Extract headers
            headers = []
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

            # Extract data rows
            tbody = table.find('tbody')
            if not tbody:
                return headers, []

            page_data = []
            for row in tbody.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    page_data.append(row_data)

            return headers, page_data

        except Exception as e:
            logger.error(f"Error extracting page data: {str(e)}")
            return [], []

    def save_data_batch(self, subsidiary_info, headers, data_batch, file_path, write_headers=False):
        """Save a batch of data to CSV"""
        try:
            mode = 'w' if write_headers else 'a'
            with open(file_path, mode, newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                if write_headers:
                    # Add subsidiary columns to headers
                    enhanced_headers = ['subsidiary_name', 'subsidiary_id'] + headers
                    writer.writerow(enhanced_headers)

                # Write data with subsidiary info
                for row in data_batch:
                    enhanced_row = [subsidiary_info['name'], subsidiary_info['id']] + row
                    writer.writerow(enhanced_row)

            logger.info(f"Saved {len(data_batch)} rows to file")

        except Exception as e:
            logger.error(f"Error saving data batch: {str(e)}")

    def scrape_subsidiary(self, subsidiary_key, subsidiary_info):
        """Scrape all pages for one subsidiary"""
        logger.info(f"Starting to scrape: {subsidiary_info['name']}")

        # Setup output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_{subsidiary_key}_{timestamp}.csv"
        file_path = os.path.join(self.config.OUTPUT_DIR, filename)

        page = 1
        headers = []
        all_data = []
        total_rows = 0
        headers_written = False

        while True:
            page_url = f"{subsidiary_info['url']}?page={page}"
            logger.info(f"Scraping page {page} for {subsidiary_info['name']}")

            # Validate page content
            has_content, row_count = self.validate_page_content(page_url)

            if not has_content:
                logger.info(f"Empty page found at page {page}. Scraping complete for {subsidiary_info['name']}")
                break

            # Extract data
            page_headers, page_data = self.extract_page_data()

            # Set headers from first page
            if not headers and page_headers:
                headers = page_headers

            if page_data:
                all_data.extend(page_data)
                total_rows += len(page_data)
                logger.info(f"Extracted {len(page_data)} rows from page {page}")

                # Write batch if we've reached batch size
                if len(all_data) >= self.config.BATCH_SIZE:
                    self.save_data_batch(subsidiary_info, headers, all_data, file_path, not headers_written)
                    headers_written = True
                    all_data = []  # Clear batch

            page += 1
            time.sleep(1)  # Be respectful

        # Write remaining data
        if all_data:
            self.save_data_batch(subsidiary_info, headers, all_data, file_path, not headers_written)

        logger.info(f"Completed {subsidiary_info['name']}: {page-1} pages, {total_rows} total rows")
        return total_rows

    def scrape_all_subsidiaries(self):
        """Scrape all subsidiaries"""
        try:
            self.setup_driver()
            total_subsidiaries = len(self.config.SUBSIDIARIES)
            grand_total_rows = 0

            logger.info(f"Starting to scrape {total_subsidiaries} subsidiaries")

            for i, (subsidiary_key, subsidiary_info) in enumerate(self.config.SUBSIDIARIES.items(), 1):
                logger.info(f"Processing subsidiary {i}/{total_subsidiaries}: {subsidiary_info['name']}")

                try:
                    rows_scraped = self.scrape_subsidiary(subsidiary_key, subsidiary_info)
                    grand_total_rows += rows_scraped
                except Exception as e:
                    logger.error(f"Failed to scrape {subsidiary_info['name']}: {str(e)}")
                    continue

            logger.info(f"Multi-subsidiary scraping completed. Total rows: {grand_total_rows}")

        except Exception as e:
            logger.error(f"Error during multi-subsidiary scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

def test_single_subsidiary(start_page=105):
    """Test with single subsidiary starting from specific page"""
    print(f"🧪 Testing ÖBB Business starting from page {start_page}")

    scraper = FinalMultiSubsidiaryScraper()
    subsidiary_info = scraper.config.SUBSIDIARIES["obb_business"]

    try:
        scraper.setup_driver()
        page = start_page
        found_empty = False

        while not found_empty and page < start_page + 20:  # Test max 20 pages
            page_url = f"{subsidiary_info['url']}?page={page}"
            print(f"📄 Testing page {page}")

            has_content, row_count = scraper.validate_page_content(page_url)

            if not has_content:
                print(f"🛑 Empty page found at page {page} - TEST SUCCESSFUL!")
                found_empty = True
            else:
                print(f"✅ Page {page}: {row_count} rows")

            page += 1

        if not found_empty:
            print(f"⚠️  No empty page found in {page - start_page} pages tested")

    finally:
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    # Test single subsidiary
    # test_single_subsidiary(105)

    # Full scrape
    scraper = FinalMultiSubsidiaryScraper()
    scraper.scrape_all_subsidiaries()