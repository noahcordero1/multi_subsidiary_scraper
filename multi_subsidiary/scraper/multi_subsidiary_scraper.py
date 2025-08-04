#!/usr/bin/env python3
"""
Multi-Subsidiary ÖBB Procurement Scraper
Scrapes all ÖBB subsidiaries and combines data into comprehensive dataset

Requirements:
pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager

Run with: python multi_subsidiary_scraper.py
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ÖBB Subsidiaries Configuration
OBB_SUBSIDIARIES = {
    "ÖBB-Business Competence Center": "https://offenevergaben.at/auftraggeber/8550",
    "ÖBB-Infrastruktur AG": "https://offenevergaben.at/auftraggeber/8538",
    "ÖBB-Technische Services Gesellschaft": "https://offenevergaben.at/auftraggeber/11068",
    "ÖBB Holding AG mit allen verbundenen Unternehmen": "https://offenevergaben.at/auftraggeber/11074",
    "ÖBB-Personenverkehr AG": "https://offenevergaben.at/auftraggeber/8547",
    "ÖBB-Produktion": "https://offenevergaben.at/auftraggeber/8545",
    "ÖBB-Postbus": "https://offenevergaben.at/auftraggeber/8581",
    "ÖBB-Holding AG": "https://offenevergaben.at/auftraggeber/11217",
    "ÖBB-Immobilienmanagement": "https://offenevergaben.at/auftraggeber/11090",
    "ÖBB-Werbung": "https://offenevergaben.at/auftraggeber/11224",
    "ÖBB Rail Tours Austria": "https://offenevergaben.at/auftraggeber/11446",
    "ÖBB-Infrastruktur Aktiengesellschaft": "https://offenevergaben.at/auftraggeber/28842",
    "ÖBB-Infrastruktur AG GB Projekt": "https://offenevergaben.at/auftraggeber/24814",
    "ÖBB Infrastruktur AG (2)": "https://offenevergaben.at/auftraggeber/36280",
    "ÖBB Personenverkehr AG (2)": "https://offenevergaben.at/auftraggeber/19826",
    "ÖBB-Immobilienmanagement (2)": "https://offenevergaben.at/auftraggeber/33422",
    "ÖBB-Technische Services-Gesellschaft (2)": "https://offenevergaben.at/auftraggeber/37657",
    "ÖBB-Personenverkehr AG (3)": "https://offenevergaben.at/auftraggeber/24566",
    "ÖBB Personenverkehr AG (4)": "https://offenevergaben.at/auftraggeber/29519",
    "ÖBB Personenverkehr AG (5)": "https://offenevergaben.at/auftraggeber/28047",
    "ÖBB-Business Competence Center (2)": "https://offenevergaben.at/auftraggeber/37203",
    "ÖBB-Business Competence Center (3)": "https://offenevergaben.at/auftraggeber/37202"
}

class MultiSubsidiaryOBBScraper:
    def __init__(self, subsidiaries=None, headless=True):
        self.subsidiaries = subsidiaries or OBB_SUBSIDIARIES
        self.headless = headless
        self.driver = None
        self.all_data = []
        self.headers = []
        self.scraping_stats = {}
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enable headless mode for faster scraping
        if self.headless:
            chrome_options.add_argument("--headless")
            logger.info("Running in headless mode for faster scraping")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome WebDriver initialized successfully")
        
    def wait_for_page_load(self, timeout=10):
        """Wait for the page to fully load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            time.sleep(2)  # Additional wait for dynamic content
            return True
        except TimeoutException:
            logger.warning(f"Page load timeout after {timeout} seconds")
            return False
    
    def extract_table_data(self, subsidiary_name):
        """Extract data from the current page's table"""
        try:
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find the main data table
            table = soup.find('table')
            if not table:
                logger.error(f"No table found on {subsidiary_name} page")
                return False, 0
            
            # Extract headers if not already done
            if not self.headers:
                header_row = table.find('thead')
                if header_row:
                    self.headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                else:
                    # If no thead, try to get headers from first row
                    first_row = table.find('tr')
                    if first_row:
                        self.headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
                
                # Add subsidiary column to headers
                if 'Subsidiary' not in self.headers:
                    self.headers.append('Subsidiary')
                
                logger.info(f"Extracted headers: {self.headers}")
            
            # Extract data rows
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # If no tbody, get all rows except the header
                rows = table.find_all('tr')[1:] if self.headers else table.find_all('tr')
            
            page_data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    # Only add rows that match the expected number of columns (minus subsidiary column)
                    if len(row_data) == len(self.headers) - 1:
                        row_data.append(subsidiary_name)  # Add subsidiary name
                        page_data.append(row_data)
            
            self.all_data.extend(page_data)
            return True, len(page_data)
            
        except Exception as e:
            logger.error(f"Error extracting table data from {subsidiary_name}: {str(e)}")
            return False, 0
    
    def find_next_button(self):
        """Find and return the next page button"""
        try:
            # Common selectors for next buttons
            next_button_selectors = [
                "//a[contains(@class, 'next')]",
                "//button[contains(@class, 'next')]",
                "//a[contains(text(), '»')]",
                "//a[contains(text(), '>')]",
                "//a[contains(@aria-label, 'next')]",
                "//a[contains(@aria-label, 'Next')]",
                "//a[@rel='next']",
                "//li[contains(@class, 'next')]/a",
                "//a[contains(@class, 'page-link') and contains(text(), '»')]",
                "//*[contains(@class, 'pagination')]//a[last()]"
            ]
            
            for selector in next_button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_enabled() and element.is_displayed():
                            return element
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding next button: {str(e)}")
            return None
    
    def click_next_page(self):
        """Click the next page button"""
        try:
            next_button = self.find_next_button()
            if next_button:
                # Scroll to the button to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(1)
                
                # Try clicking the button
                next_button.click()
                time.sleep(3)  # Wait for page to load
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error clicking next page: {str(e)}")
            return False
    
    def scrape_subsidiary(self, subsidiary_name, base_url, max_pages=None):
        """Scrape a single subsidiary with improved pagination handling"""
        logger.info(f"Starting to scrape {subsidiary_name}")
        
        try:
            # Navigate to the subsidiary page
            logger.info(f"Navigating to {base_url}")
            self.driver.get(base_url)
            
            # Wait for page to load
            time.sleep(3)
            
            if not self.wait_for_page_load():
                logger.error(f"Failed to load {subsidiary_name} page properly")
                return {"pages": 0, "contracts": 0, "status": "failed", "message": "Page load timeout"}
            
            # Check if page has data
            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find('table')
                if not table:
                    logger.warning(f"No table found on {subsidiary_name} page")
                    return {"pages": 0, "contracts": 0, "status": "no_data", "message": "No table found"}
                
                rows = table.find_all('tr')
                if len(rows) <= 1:  # Only header or no data rows
                    logger.info(f"No contract data found for {subsidiary_name}")
                    return {"pages": 1, "contracts": 0, "status": "empty", "message": "No contract data"}
                
            except Exception as check_error:
                logger.error(f"Error checking page content for {subsidiary_name}: {str(check_error)}")
                return {"pages": 0, "contracts": 0, "status": "error", "error": str(check_error)}
            
            current_page = 1
            total_contracts = 0
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            while True:
                logger.info(f"Scraping {subsidiary_name} - Page {current_page}")
                
                # Extract data from current page
                success, contracts_count = self.extract_table_data(subsidiary_name)
                if success and contracts_count > 0:
                    total_contracts += contracts_count
                    consecutive_failures = 0  # Reset failure counter
                    logger.info(f"Extracted {contracts_count} contracts from {subsidiary_name} page {current_page}")
                else:
                    consecutive_failures += 1
                    logger.warning(f"Failed to extract data from {subsidiary_name} page {current_page} (failure {consecutive_failures})")
                    
                    # If we can't extract data from first page, likely no data available
                    if current_page == 1:
                        return {"pages": 1, "contracts": 0, "status": "no_data", "message": "No extractable data"}
                    
                    # If too many consecutive failures, stop
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(f"Too many consecutive failures for {subsidiary_name}, stopping")
                        break
                
                # Check if we should continue
                if max_pages and current_page >= max_pages:
                    logger.info(f"Reached max pages ({max_pages}) for {subsidiary_name}")
                    break
                
                # Try to go to next page
                if not self.click_next_page():
                    logger.info(f"No more pages available for {subsidiary_name} or failed to navigate")
                    break
                
                current_page += 1
                
                # Add a small delay between requests to be respectful
                time.sleep(1)
            
            stats = {
                "pages": current_page,
                "contracts": total_contracts,
                "status": "completed" if total_contracts > 0 else "empty"
            }
            
            logger.info(f"Completed scraping {subsidiary_name}: {current_page} pages, {total_contracts} contracts")
            return stats
            
        except Exception as e:
            logger.error(f"Error scraping {subsidiary_name}: {str(e)}")
            return {"pages": 0, "contracts": 0, "status": "error", "error": str(e)}
    
    def scrape_all_subsidiaries(self, max_pages_per_subsidiary=None):
        """Scrape all subsidiaries with improved session management"""
        total_subsidiaries = len(self.subsidiaries)
        logger.info(f"Starting to scrape {total_subsidiaries} ÖBB subsidiaries")
        
        for i, (subsidiary_name, url) in enumerate(self.subsidiaries.items(), 1):
            logger.info(f"Processing subsidiary {i}/{total_subsidiaries}: {subsidiary_name}")
            
            # Setup fresh driver for each subsidiary to avoid session issues
            try:
                self.setup_driver()
                
                stats = self.scrape_subsidiary(subsidiary_name, url, max_pages_per_subsidiary)
                self.scraping_stats[subsidiary_name] = stats
                
                # Log progress
                total_contracts_so_far = sum(s.get("contracts", 0) for s in self.scraping_stats.values())
                logger.info(f"Progress: {i}/{total_subsidiaries} subsidiaries completed. Total contracts: {total_contracts_so_far}")
                
            except Exception as e:
                logger.error(f"Error scraping {subsidiary_name}: {str(e)}")
                self.scraping_stats[subsidiary_name] = {
                    "pages": 0, 
                    "contracts": 0, 
                    "status": "error", 
                    "error": str(e)
                }
            finally:
                # Clean up driver after each subsidiary
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
            
            # Small delay between subsidiaries
            if i < total_subsidiaries:
                time.sleep(2)
        
        logger.info(f"Scraping completed for all subsidiaries")
        logger.info(f"Total contracts extracted: {len(self.all_data)}")
    
    def save_to_csv(self, filename="obb_all_subsidiaries_data.csv"):
        """Save the scraped data to CSV file with separate summary file"""
        try:
            if not self.all_data:
                logger.warning("No data to save")
                return False
            
            # Create main DataFrame
            df = pd.DataFrame(self.all_data, columns=self.headers if self.headers else None)
            
            # Save main data to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            # Create and save summary DataFrame
            summary_data = []
            for subsidiary, stats in self.scraping_stats.items():
                summary_data.append({
                    'Subsidiary': subsidiary,
                    'Pages Scraped': stats.get('pages', 0),
                    'Contracts Found': stats.get('contracts', 0),
                    'Status': stats.get('status', 'unknown'),
                    'Error': stats.get('error', '')
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_filename = filename.replace('.csv', '_summary.csv')
            summary_df.to_csv(summary_filename, index=False, encoding='utf-8')
            
            logger.info(f"Data saved to {filename}")
            logger.info(f"Summary saved to {summary_filename}")
            logger.info(f"Total rows saved: {len(df)}")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Print summary
            print("\n" + "="*70)
            print("MULTI-SUBSIDIARY SCRAPING COMPLETED!")
            print("="*70)
            print(f"Total subsidiaries scraped: {len(self.subsidiaries)}")
            print(f"Total contracts extracted: {len(df)}")
            print(f"Data saved to: {filename}")
            print(f"Summary saved to: {summary_filename}")
            print("\nScraping Summary:")
            print("-" * 70)
            for subsidiary, stats in self.scraping_stats.items():
                status = stats.get('status', 'unknown')
                contracts = stats.get('contracts', 0)
                pages = stats.get('pages', 0)
                print(f"{subsidiary[:40]:<40} | {contracts:>6} contracts | {pages:>3} pages | {status}")
            print("="*70)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return False

def test_subsidiaries():
    """Test each subsidiary to see which ones have data"""
    print("🔍 Testing ÖBB Subsidiaries for Data Availability")
    print("=" * 60)
    
    scraper = MultiSubsidiaryOBBScraper(headless=False)  # Use visible browser for testing
    scraper.setup_driver()
    
    try:
        for i, (name, url) in enumerate(OBB_SUBSIDIARIES.items(), 1):
            print(f"\n{i:2d}. Testing {name}")
            print(f"    URL: {url}")
            
            try:
                scraper.driver.get(url)
                time.sleep(3)
                
                # Check for tables
                tables = scraper.driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    soup = BeautifulSoup(scraper.driver.page_source, 'html.parser')
                    table = soup.find('table')
                    if table:
                        rows = table.find_all('tr')
                        if len(rows) > 1:
                            print(f"    ✅ HAS DATA: {len(rows)-1} potential contracts found")
                        else:
                            print(f"    ⚠️  TABLE EMPTY: Only header row found")
                    else:
                        print(f"    ❌ NO PARSEABLE TABLE")
                else:
                    print(f"    ❌ NO TABLES FOUND")
                    
            except Exception as e:
                print(f"    ❌ ERROR: {str(e)}")
                
    finally:
        scraper.driver.quit()
    
    print("\n" + "=" * 60)
    print("Test completed. Run main() to scrape subsidiaries with data.")

def main():
    """Main function to run the multi-subsidiary scraper with periodic saves"""
    
    print("🚀 Starting Multi-Subsidiary ÖBB Procurement Scraper")
    print(f"📊 Will scrape {len(OBB_SUBSIDIARIES)} ÖBB subsidiaries")
    print("⚡ Running in headless mode for maximum speed")
    print("💾 Will save intermediate results every 5 subsidiaries")
    print("")
    
    scraper = MultiSubsidiaryOBBScraper(headless=True)
    
    try:
        # Scrape subsidiaries in batches with intermediate saves
        subsidiary_items = list(OBB_SUBSIDIARIES.items())
        batch_size = 5
        
        for batch_start in range(0, len(subsidiary_items), batch_size):
            batch_end = min(batch_start + batch_size, len(subsidiary_items))
            batch_subsidiaries = dict(subsidiary_items[batch_start:batch_end])
            
            print(f"\n📦 Processing batch {batch_start//batch_size + 1}: subsidiaries {batch_start+1}-{batch_end}")
            
            # Create new scraper instance for this batch
            batch_scraper = MultiSubsidiaryOBBScraper(subsidiaries=batch_subsidiaries, headless=True)
            batch_scraper.all_data = scraper.all_data.copy()  # Keep accumulated data
            batch_scraper.headers = scraper.headers.copy() if scraper.headers else []
            batch_scraper.scraping_stats = scraper.scraping_stats.copy()
            
            # Scrape this batch
            batch_scraper.scrape_all_subsidiaries(max_pages_per_subsidiary=None)
            
            # Update main scraper with batch results
            scraper.all_data = batch_scraper.all_data
            scraper.headers = batch_scraper.headers
            scraper.scraping_stats.update(batch_scraper.scraping_stats)
            
            # Save intermediate results
            intermediate_filename = f"extended_final_batch_{batch_start//batch_size + 1}.csv"
            scraper.save_to_csv(intermediate_filename)
            
            current_total = len(scraper.all_data)
            print(f"✅ Batch {batch_start//batch_size + 1} completed. Total contracts so far: {current_total}")
        
        # Final save with complete dataset
        scraper.save_to_csv("../data/multi_subsidiary_data.csv")
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        # Still try to save whatever data we have
        if scraper.all_data:
            scraper.save_to_csv("extended_final_partial.csv")
            print(f"💾 Saved partial data with {len(scraper.all_data)} contracts")

if __name__ == "__main__":
    print("All subsidiaries confirmed to have data. Starting batched full scrape...")
    main()