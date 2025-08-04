#!/usr/bin/env python3
"""
Web scraper for OffeneVergaben.at - ÖBB Business Competence Center GmbH
Scrapes all pages of procurement data and exports to Excel

Requirements:
pip install selenium beautifulsoup4 pandas openpyxl webdriver-manager
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OffeneVergabenScraper:
    def __init__(self, base_url="https://offenevergaben.at/auftraggeber/8550"):
        self.base_url = base_url
        self.driver = None
        self.all_data = []
        self.headers = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Run headless for faster scraping
        chrome_options.add_argument("--headless")
        
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
    
    def extract_table_data(self):
        """Extract data from the current page's table"""
        try:
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find the main data table
            table = soup.find('table')
            if not table:
                logger.error("No table found on the current page")
                return False
            
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
                    # Only add rows that match the expected number of columns
                    if len(row_data) == len(self.headers):
                        page_data.append(row_data)
            
            self.all_data.extend(page_data)
            logger.info(f"Extracted {len(page_data)} rows from current page. Total rows: {len(self.all_data)}")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}")
            return False
    
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
                logger.info("No next button found or next button is disabled")
                return False
                
        except Exception as e:
            logger.error(f"Error clicking next page: {str(e)}")
            return False
    
    def scrape_all_pages(self, max_pages=107):
        """Main scraping function to go through all pages"""
        try:
            self.setup_driver()
            
            # Navigate to the starting page
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            
            if not self.wait_for_page_load():
                raise Exception("Failed to load initial page")
            
            current_page = 1
            
            while current_page <= max_pages:
                logger.info(f"Scraping page {current_page} of {max_pages}")
                
                # Extract data from current page
                if not self.extract_table_data():
                    logger.warning(f"Failed to extract data from page {current_page}")
                
                # Check if we're on the last page or reached max pages
                if current_page >= max_pages:
                    break
                
                # Try to go to next page
                if not self.click_next_page():
                    logger.info(f"No more pages available or failed to navigate. Stopped at page {current_page}")
                    break
                
                current_page += 1
                
                # Add a small delay between requests to be respectful
                time.sleep(2)
            
            logger.info(f"Scraping completed. Total pages scraped: {current_page}")
            logger.info(f"Total rows extracted: {len(self.all_data)}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_csv(self, filename="offenevergaben_data.csv"):
        """Save the scraped data to CSV file"""
        try:
            if not self.all_data:
                logger.warning("No data to save")
                return False
            
            # Create DataFrame
            df = pd.DataFrame(self.all_data, columns=self.headers if self.headers else None)
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Data saved to {filename}")
            logger.info(f"Total rows saved: {len(df)}")
            logger.info(f"Columns: {list(df.columns)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return False

def main():
    """Main function to run the scraper"""
    scraper = OffeneVergabenScraper()
    
    try:
        # Start scraping
        scraper.scrape_all_pages(max_pages=107)
        
        # Save data to CSV in data directory
        scraper.save_to_csv("../data/single_subsidiary_data.csv")
        
        print("\n" + "="*50)
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"Total records extracted: {len(scraper.all_data)}")
        print("Data saved to: ../data/single_subsidiary_data.csv")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()