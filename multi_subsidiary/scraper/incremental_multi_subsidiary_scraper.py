#!/usr/bin/env python3
"""
Incremental Multi-Subsidiary Web Scraper for OffeneVergaben.at
Enhanced version with page tracking and incremental updates

Features:
- Tracks last scraped page per subsidiary
- Only scrapes new pages since last run
- Appends new data to existing files
- Maintains data integrity through robust tracking

Requirements:
pip install selenium beautifulsoup4 pandas webdriver-manager
"""

import time
import csv
import os
import json
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

class IncrementalMultiSubsidiaryScraperConfig:
    """Configuration class for incremental multi-subsidiary scraper"""

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
    OUTPUT_DIR = "../data"
    TRACKING_FILE = "../data/scraper_tracking.json"

class IncrementalMultiSubsidiaryScraper:
    """Enhanced multi-subsidiary scraper with incremental functionality"""

    def __init__(self, mode="incremental"):
        self.config = IncrementalMultiSubsidiaryScraperConfig()
        self.driver = None
        self.mode = mode  # "incremental" or "full"
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

    def load_tracking_data(self):
        """Load tracking data from JSON file"""
        if os.path.exists(self.config.TRACKING_FILE):
            try:
                with open(self.config.TRACKING_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading tracking data: {str(e)}")
                return {}
        return {}

    def save_tracking_data(self, tracking_data):
        """Save tracking data to JSON file"""
        try:
            with open(self.config.TRACKING_FILE, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            logger.info("Tracking data saved successfully")
        except Exception as e:
            logger.error(f"Error saving tracking data: {str(e)}")

    def get_last_scraped_page(self, subsidiary_key):
        """Get the last scraped page for a subsidiary"""
        tracking_data = self.load_tracking_data()
        subsidiary_info = tracking_data.get("subsidiaries", {}).get(subsidiary_key, {})
        last_page = subsidiary_info.get("last_scraped_page", 0)

        if last_page > 0:
            logger.info(f"Last scraped page for {subsidiary_key}: {last_page}")
        else:
            logger.info(f"No previous data for {subsidiary_key}, starting fresh")

        return last_page

    def update_tracking_data(self, subsidiary_key, last_page, total_new_records):
        """Update tracking data for a subsidiary"""
        tracking_data = self.load_tracking_data()

        # Initialize structure if needed
        if "tracking_info" not in tracking_data:
            tracking_data["tracking_info"] = {
                "last_update": datetime.now().isoformat(),
                "scraper_version": "incremental_v1.0"
            }

        if "subsidiaries" not in tracking_data:
            tracking_data["subsidiaries"] = {}

        # Update subsidiary data
        tracking_data["subsidiaries"][subsidiary_key] = {
            "last_scraped_page": last_page,
            "last_scrape_date": datetime.now().isoformat(),
            "total_new_records_this_run": total_new_records
        }

        tracking_data["tracking_info"]["last_update"] = datetime.now().isoformat()

        self.save_tracking_data(tracking_data)

    def validate_page_content(self, page_url):
        """Validate if page has content - using existing robust logic"""
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

    def get_csv_file_path(self, subsidiary_key):
        """Get the path for the subsidiary's CSV file"""
        filename = f"{subsidiary_key}_data.csv"
        return os.path.join(self.config.OUTPUT_DIR, filename)

    def append_data_to_csv(self, subsidiary_info, headers, new_data, csv_path):
        """Append new data to existing CSV or create new file"""
        try:
            file_exists = os.path.exists(csv_path)
            write_headers = not file_exists
            mode = 'a' if file_exists else 'w'

            with open(csv_path, mode, newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                if write_headers:
                    enhanced_headers = ['subsidiary_name', 'subsidiary_id'] + headers
                    writer.writerow(enhanced_headers)
                    logger.info(f"Created new CSV file: {csv_path}")

                # Write new data with subsidiary info
                for row in new_data:
                    enhanced_row = [subsidiary_info['name'], subsidiary_info['id']] + row
                    writer.writerow(enhanced_row)

            logger.info(f"Appended {len(new_data)} rows to {csv_path}")

        except Exception as e:
            logger.error(f"Error appending data to CSV: {str(e)}")

    def incremental_scrape_subsidiary(self, subsidiary_key, subsidiary_info):
        """Scrape only new pages for a subsidiary (incremental mode)"""
        logger.info(f"🔄 INCREMENTAL: Starting incremental scrape for {subsidiary_info['name']}")

        # Get last scraped page
        last_page = self.get_last_scraped_page(subsidiary_key)
        start_page = last_page + 1

        if last_page == 0:
            logger.info(f"🆕 No previous data - starting full scrape for {subsidiary_info['name']}")
            return self.full_scrape_subsidiary(subsidiary_key, subsidiary_info)
        else:
            logger.info(f"🔍 Starting from page {start_page} (last page was {last_page})")

        # Setup output file
        csv_path = self.get_csv_file_path(subsidiary_key)

        page = start_page
        headers = []
        total_new_rows = 0

        while True:
            page_url = f"{subsidiary_info['url']}?page={page}&sort=item_lastmod"
            logger.info(f"🔍 Checking page {page} for new content")

            # Validate page content
            has_content, row_count = self.validate_page_content(page_url)

            if not has_content:
                logger.info(f"🛑 Empty page found at page {page}. Incremental scrape complete!")
                final_page = page - 1  # Last page with content
                break

            logger.info(f"✅ Page {page} has {row_count} rows - scraping...")

            # Extract data
            page_headers, page_data = self.extract_page_data()

            # Set headers from first page
            if not headers and page_headers:
                headers = page_headers

            if page_data:
                self.append_data_to_csv(subsidiary_info, headers, page_data, csv_path)
                total_new_rows += len(page_data)
                logger.info(f"📝 Appended {len(page_data)} rows from page {page}")

            page += 1
            final_page = page - 1  # Track the last successfully scraped page
            time.sleep(1)  # Be respectful

        # Update tracking data
        if total_new_rows > 0:
            self.update_tracking_data(subsidiary_key, final_page, total_new_rows)
            logger.info(f"📊 INCREMENTAL COMPLETE: {total_new_rows} new records from pages {start_page} to {final_page}")
        else:
            # No new data, but still update timestamp
            self.update_tracking_data(subsidiary_key, last_page, 0)
            logger.info(f"📊 INCREMENTAL COMPLETE: No new data found")

        return total_new_rows

    def full_scrape_subsidiary(self, subsidiary_key, subsidiary_info):
        """Full scrape for a subsidiary (full mode or first-time)"""
        logger.info(f"🔄 FULL: Starting full scrape for {subsidiary_info['name']}")

        csv_path = self.get_csv_file_path(subsidiary_key)

        page = 1
        headers = []
        total_rows = 0

        while True:
            page_url = f"{subsidiary_info['url']}?page={page}&sort=item_lastmod"
            logger.info(f"🔍 Scraping page {page}")

            # Validate page content
            has_content, row_count = self.validate_page_content(page_url)

            if not has_content:
                logger.info(f"🛑 Empty page found at page {page}. Full scrape complete!")
                final_page = page - 1
                break

            # Extract data
            page_headers, page_data = self.extract_page_data()

            # Set headers from first page
            if not headers and page_headers:
                headers = page_headers

            if page_data:
                # For full scrape, overwrite file on first page, append on subsequent
                if page == 1:
                    # Remove existing file for fresh start
                    if os.path.exists(csv_path):
                        os.remove(csv_path)

                self.append_data_to_csv(subsidiary_info, headers, page_data, csv_path)
                total_rows += len(page_data)
                logger.info(f"📝 Added {len(page_data)} rows from page {page}")

            page += 1
            final_page = page - 1
            time.sleep(1)  # Be respectful

        # Update tracking data
        self.update_tracking_data(subsidiary_key, final_page, total_rows)
        logger.info(f"📊 FULL COMPLETE: {total_rows} total records from pages 1 to {final_page}")

        return total_rows

    def scrape_all_subsidiaries(self):
        """Scrape all subsidiaries using chosen mode"""
        try:
            self.setup_driver()
            total_subsidiaries = len(self.config.SUBSIDIARIES)
            grand_total_new_rows = 0

            logger.info(f"🚀 STARTING {self.mode.upper()} SCRAPE")
            logger.info(f"📊 Processing {total_subsidiaries} subsidiaries")

            for i, (subsidiary_key, subsidiary_info) in enumerate(self.config.SUBSIDIARIES.items(), 1):
                logger.info(f"🏢 Processing subsidiary {i}/{total_subsidiaries}: {subsidiary_info['name']}")

                try:
                    if self.mode == "incremental":
                        rows_scraped = self.incremental_scrape_subsidiary(subsidiary_key, subsidiary_info)
                    else:
                        rows_scraped = self.full_scrape_subsidiary(subsidiary_key, subsidiary_info)

                    grand_total_new_rows += rows_scraped
                    logger.info(f"✅ Completed {subsidiary_info['name']}: {rows_scraped} rows")

                except Exception as e:
                    logger.error(f"❌ Failed to scrape {subsidiary_info['name']}: {str(e)}")
                    continue

            logger.info(f"🎯 {self.mode.upper()} SCRAPE COMPLETED")
            logger.info(f"📊 Total new records across all subsidiaries: {grand_total_new_rows}")

        except Exception as e:
            logger.error(f"❌ Error during multi-subsidiary scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function with mode selection"""
    import argparse

    parser = argparse.ArgumentParser(description='ÖBB Multi-Subsidiary Procurement Scraper')
    parser.add_argument('--mode', choices=['incremental', 'full'], default='incremental',
                       help='Scraping mode: incremental (default) or full')

    args = parser.parse_args()

    scraper = IncrementalMultiSubsidiaryScraper(mode=args.mode)
    scraper.scrape_all_subsidiaries()

if __name__ == "__main__":
    main()