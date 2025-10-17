#!/usr/bin/env python3
"""
Selenium Poll Automation Script for MileSplit LA
Automates voting for Kenya Cummings in the poll, running in an infinite loop.
"""

import time
import logging
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PollAutomation:
    def __init__(self):
        self.driver = None
        self.url = "https://la.milesplit.com/articles/391971/poll-milesplit-la-girls-performer-of-the-week?utm_source=Iterable&utm_medium=email&utm_campaign=campaign_14740707&utm_content=ad_sales_running_warehouse&utm_term=ad_sales_running_warehouse"
        
        # CSS selectors for the elements
        self.checkbox_selector = "input#PDI_answer71048920"  # Direct checkbox for Kenya Cummings
        self.vote_button_selector = "#pd-vote-button16156077"
        self.return_poll_selector = "a.pds-return-poll"
        
        # Target text for Kenya Cummings
        self.target_text = "David Thibodaux's Kenya Cummings"
        
        # Instance id for profile separation (single script uses 1)
        self.instance_id = 1
        
    def _build_chrome_options(self, instance_id: int) -> Options:
        """Create Windows-friendly Chrome options with isolated temp profiles."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Isolated user-data-dir per instance in OS temp
        temp_root = tempfile.gettempdir()
        profile_dir = os.path.join(temp_root, f"chrome_poll_profile_{instance_id}")
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Try to use installed Chrome if present (PyInstaller friendly)
        potential_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for p in potential_paths:
            if p and os.path.isfile(p):
                chrome_options.binary_location = p
                break
        return chrome_options

    def setup_driver(self):
        """Initialize Chrome WebDriver with automatic driver management."""
        try:
            logger.info("Setting up Chrome WebDriver...")
            
            chrome_options = self._build_chrome_options(self.instance_id)
            
            # Initialize driver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
    
    def navigate_to_poll(self):
        """Navigate to the poll URL."""
        try:
            logger.info(f"Navigating to: {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Successfully loaded poll page")
            
            # Handle cookie consent banner if present
            self.handle_cookie_consent()
            
            # Handle any other pop-ups or overlays
            self.handle_popups()
            
            # Check if we're still on the poll page
            self.ensure_on_poll_page()
            
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to poll: {e}")
            return False
    
    def handle_cookie_consent(self):
        """Handle cookie consent banner if it appears."""
        try:
            # Wait a moment for banner to appear
            time.sleep(2)
            
            # Look for the specific Osano cookie banner
            cookie_selectors = [
                "div[role='dialog'][aria-label*='Cookie']",
                ".osano-cm-dialog",
                "div.osano-cm-window__dialog"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_banner = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if cookie_banner.is_displayed():
                        logger.info("Cookie consent banner detected, looking for close button...")
                        
                        # Look for the X close button specifically
                        close_buttons = [
                            "button.osano-cm-close",
                            "button[aria-label*='close']",
                            "button[aria-label*='Close']",
                            ".osano-cm-close",
                            "button:contains('×')",
                            "button:contains('✕')"
                        ]
                        
                        for button_selector in close_buttons:
                            try:
                                close_button = cookie_banner.find_element(By.CSS_SELECTOR, button_selector)
                                if close_button.is_displayed() and close_button.is_enabled():
                                    close_button.click()
                                    logger.info("Successfully dismissed cookie consent banner with close button")
                                    time.sleep(2)  # Wait for banner to disappear
                                    return
                            except:
                                continue
                        
                        # If no close button found, try pressing Escape key
                        try:
                            from selenium.webdriver.common.keys import Keys
                            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                            logger.info("Pressed Escape to dismiss cookie banner")
                            time.sleep(2)
                            return
                        except:
                            pass
                            
                except:
                    continue
                    
            logger.info("No cookie consent banner found or already dismissed")
            
        except Exception as e:
            logger.warning(f"Could not handle cookie consent banner: {e}")
    
    def handle_popups(self):
        """Handle any pop-ups or overlays that might block interactions."""
        try:
            # Common pop-up selectors
            popup_selectors = [
                "[role='dialog']:not([aria-label*='Cookie'])",
                ".modal",
                ".popup",
                ".overlay",
                "[data-modal]",
                ".lightbox"
            ]
            
            for selector in popup_selectors:
                try:
                    popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if popup.is_displayed():
                        logger.info("Popup detected, attempting to close...")
                        
                        # Look for close buttons
                        close_selectors = [
                            "button[aria-label*='close']",
                            "button[aria-label*='Close']",
                            ".close",
                            ".close-button",
                            "[data-dismiss]",
                            "button:contains('×')",
                            "button:contains('Close')"
                        ]
                        
                        for close_selector in close_selectors:
                            try:
                                close_button = popup.find_element(By.CSS_SELECTOR, close_selector)
                                if close_button.is_displayed() and close_button.is_enabled():
                                    close_button.click()
                                    logger.info("Successfully closed popup")
                                    time.sleep(1)
                                    return
                            except:
                                continue
                        
                        # If no close button found, try pressing Escape
                        try:
                            from selenium.webdriver.common.keys import Keys
                            popup.send_keys(Keys.ESCAPE)
                            logger.info("Pressed Escape to close popup")
                            time.sleep(1)
                            return
                        except:
                            pass
                            
                except:
                    continue
                    
            logger.info("No blocking popups found")
            
        except Exception as e:
            logger.warning(f"Could not handle popups: {e}")
    
    def ensure_on_poll_page(self):
        """Ensure we're on the correct poll page, navigate back if needed."""
        try:
            # Check if we can find the poll container
            poll_container = self.driver.find_element(By.CSS_SELECTOR, "div.CSS_Poll.PDS_Poll")
            
            if poll_container.is_displayed():
                logger.info("Confirmed on poll page")
                return True
            else:
                logger.warning("Poll container not visible, navigating back to poll")
                self.driver.get(self.url)
                time.sleep(3)
                return True
                
        except:
            # If poll container not found, we might have navigated away
            logger.warning("Poll container not found, navigating back to poll page")
            self.driver.get(self.url)
            time.sleep(3)
            
            # Handle cookie consent again after navigation
            self.handle_cookie_consent()
            self.handle_popups()
            
            return True
    
    def find_and_click_checkbox(self):
        """Find and click the checkbox for Kenya Cummings."""
        try:
            # Wait for the specific checkbox to be present and clickable
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.checkbox_selector))
            )
            
            logger.info("Found Kenya Cummings checkbox")
            
            # Try multiple click methods if the first one fails
            click_success = False
            
            # Method 1: Regular click
            try:
                checkbox.click()
                click_success = True
                logger.info("Successfully clicked checkbox with regular click")
            except Exception as e:
                logger.warning(f"Regular click failed: {e}")
                
                # Method 2: JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    click_success = True
                    logger.info("Successfully clicked checkbox with JavaScript click")
                except Exception as e2:
                    logger.warning(f"JavaScript click failed: {e2}")
                    
                    # Method 3: Scroll into view and try again
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                        time.sleep(1)
                        checkbox.click()
                        click_success = True
                        logger.info("Successfully clicked checkbox after scrolling")
                    except Exception as e3:
                        logger.warning(f"Scroll and click failed: {e3}")
            
            if click_success:
                # Wait a moment for the checkbox state to register
                time.sleep(1)
                return True
            else:
                logger.error("All click methods failed")
                return False
            
        except TimeoutException:
            logger.error("Timeout waiting for checkbox to load")
            return False
        except Exception as e:
            logger.error(f"Failed to click checkbox: {e}")
            return False
    
    def click_vote_button(self):
        """Click the vote button."""
        try:
            vote_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.vote_button_selector))
            )
            
            logger.info("Clicking vote button...")
            vote_button.click()
            
            # Wait a moment for vote to process
            time.sleep(2)
            logger.info("Vote button clicked successfully")
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for vote button")
            return False
        except Exception as e:
            logger.error(f"Failed to click vote button: {e}")
            return False
    
    def return_to_poll(self):
        """Click the 'Return To Poll' link."""
        try:
            return_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.return_poll_selector))
            )
            
            logger.info("Clicking 'Return To Poll' link...")
            return_link.click()
            
            # Wait for page to load
            time.sleep(2)
            logger.info("Successfully returned to poll")
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for 'Return To Poll' link")
            return False
        except Exception as e:
            logger.error(f"Failed to click 'Return To Poll' link: {e}")
            return False
    
    def run_voting_cycle(self):
        """Execute one complete voting cycle."""
        logger.info("Starting voting cycle...")
        
        # Step 1: Click checkbox
        if not self.find_and_click_checkbox():
            return False
        
        # Step 2: Click vote button
        if not self.click_vote_button():
            return False
        
        # Step 3: Return to poll
        if not self.return_to_poll():
            return False
        
        logger.info("Voting cycle completed successfully")
        return True
    
    def run_automation(self):
        """Run the automation in an infinite loop."""
        try:
            # Setup driver
            if not self.setup_driver():
                return
            
            # Navigate to poll
            if not self.navigate_to_poll():
                return
            
            cycle_count = 0
            
            logger.info("Starting automation loop... Press Ctrl+C to stop")
            
            while True:
                cycle_count += 1
                logger.info(f"=== Voting Cycle #{cycle_count} ===")
                
                if self.run_voting_cycle():
                    logger.info("Waiting 1 second before next cycle...")
                    time.sleep(1)
                else:
                    logger.warning("Voting cycle failed, waiting 5 seconds before retry...")
                    time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Automation stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in automation: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            logger.info("Closing browser...")
            self.driver.quit()
            logger.info("Cleanup complete")

def main():
    """Main function to run the automation."""
    automation = PollAutomation()
    automation.run_automation()

if __name__ == "__main__":
    main()
