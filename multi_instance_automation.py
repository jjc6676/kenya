#!/usr/bin/env python3
"""
Multi-Instance Selenium Poll Automation Script for MileSplit LA
Runs 3-5 concurrent browser instances to maximize voting efficiency.
"""

import time
import logging
import threading
import os
import tempfile
import shutil
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
## Using Selenium Manager built into Selenium instead of webdriver-manager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
)
logger = logging.getLogger(__name__)

class PollAutomationInstance:
    def __init__(self, instance_id, url):
        self.instance_id = instance_id
        self.driver = None
        self.url = url
        self.running = False
        
        # CSS selectors for the elements
        self.checkbox_selector = "input#PDI_answer71048920"  # Direct checkbox for Kenya Cummings
        self.vote_button_selector = "#pd-vote-button16156077"
        self.return_poll_selector = "a.pds-return-poll"
        
        # Target text for Kenya Cummings
        self.target_text = "David Thibodaux's Kenya Cummings"
        
        # Instance statistics
        self.vote_count = 0
        self.error_count = 0
        
    def _build_chrome_options(self) -> Options:
        """Create Windows-friendly Chrome options with isolated temp profiles per instance."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Isolated user-data-dir per instance in OS temp
        temp_root = tempfile.gettempdir()
        profile_dir = os.path.join(temp_root, f"chrome_poll_profile_{self.instance_id}")
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # Allow explicit override via environment variable
        env_binary = os.environ.get("CHROME_BINARY")
        if env_binary and os.path.isfile(env_binary):
            chrome_options.binary_location = env_binary
        else:
            system_name = platform.system().lower()
            if system_name.startswith("win"):
                potential_paths = [
                    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
                ]
                for p in potential_paths:
                    if p and os.path.isfile(p):
                        chrome_options.binary_location = p
                        break
            else:
                potential_paths = [
                    shutil.which("google-chrome"),
                    shutil.which("google-chrome-stable"),
                    shutil.which("chromium"),
                    shutil.which("chromium-browser"),
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser",
                    "/snap/bin/chromium",
                ]
                for p in potential_paths:
                    if p and os.path.isfile(p):
                        chrome_options.binary_location = p
                        break

        # Assign different remote debugging ports to reduce conflicts
        chrome_options.add_argument(f"--remote-debugging-port={9222 + self.instance_id}")
        return chrome_options

    def setup_driver(self):
        """Initialize Chrome WebDriver with automatic driver management."""
        try:
            logger.info(f"[Instance {self.instance_id}] Setting up Chrome WebDriver...")
            
            chrome_options = self._build_chrome_options()
            
            # On Linux servers, default to headless to reduce memory
            if platform.system().lower() != "windows":
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--disable-gpu")

            # Initialize driver using Selenium Manager (auto-downloads correct driver)
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"[Instance {self.instance_id}] Chrome WebDriver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Failed to setup Chrome WebDriver: {e}")
            return False
    
    def navigate_to_poll(self):
        """Navigate to the poll URL."""
        try:
            logger.info(f"[Instance {self.instance_id}] Navigating to poll...")
            self.driver.get(self.url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info(f"[Instance {self.instance_id}] Successfully loaded poll page")
            
            # Handle cookie consent banner if present
            self.handle_cookie_consent()
            
            # Handle any other pop-ups or overlays
            self.handle_popups()
            
            # Check if we're still on the poll page
            self.ensure_on_poll_page()
            
            return True
            
        except TimeoutException:
            logger.error(f"[Instance {self.instance_id}] Timeout waiting for page to load")
            return False
        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Failed to navigate to poll: {e}")
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
                        logger.info(f"[Instance {self.instance_id}] Cookie consent banner detected, looking for close button...")
                        
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
                                    logger.info(f"[Instance {self.instance_id}] Successfully dismissed cookie consent banner")
                                    time.sleep(2)
                                    return
                            except:
                                continue
                        
                        # If no close button found, try pressing Escape key
                        try:
                            from selenium.webdriver.common.keys import Keys
                            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                            logger.info(f"[Instance {self.instance_id}] Pressed Escape to dismiss cookie banner")
                            time.sleep(2)
                            return
                        except:
                            pass
                            
                except:
                    continue
                    
            logger.info(f"[Instance {self.instance_id}] No cookie consent banner found")
            
        except Exception as e:
            logger.warning(f"[Instance {self.instance_id}] Could not handle cookie consent banner: {e}")
    
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
                        logger.info(f"[Instance {self.instance_id}] Popup detected, attempting to close...")
                        
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
                                    logger.info(f"[Instance {self.instance_id}] Successfully closed popup")
                                    time.sleep(1)
                                    return
                            except:
                                continue
                        
                        # If no close button found, try pressing Escape
                        try:
                            from selenium.webdriver.common.keys import Keys
                            popup.send_keys(Keys.ESCAPE)
                            logger.info(f"[Instance {self.instance_id}] Pressed Escape to close popup")
                            time.sleep(1)
                            return
                        except:
                            pass
                            
                except:
                    continue
                    
            logger.info(f"[Instance {self.instance_id}] No blocking popups found")
            
        except Exception as e:
            logger.warning(f"[Instance {self.instance_id}] Could not handle popups: {e}")
    
    def ensure_on_poll_page(self):
        """Ensure we're on the correct poll page, navigate back if needed."""
        try:
            # Check if we can find the poll container
            poll_container = self.driver.find_element(By.CSS_SELECTOR, "div.CSS_Poll.PDS_Poll")
            
            if poll_container.is_displayed():
                logger.info(f"[Instance {self.instance_id}] Confirmed on poll page")
                return True
            else:
                logger.warning(f"[Instance {self.instance_id}] Poll container not visible, navigating back to poll")
                self.driver.get(self.url)
                time.sleep(3)
                return True
                
        except:
            # If poll container not found, we might have navigated away
            logger.warning(f"[Instance {self.instance_id}] Poll container not found, navigating back to poll page")
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
            
            logger.info(f"[Instance {self.instance_id}] Found Kenya Cummings checkbox")
            
            # Try multiple click methods if the first one fails
            click_success = False
            
            # Method 1: Regular click
            try:
                checkbox.click()
                click_success = True
                logger.info(f"[Instance {self.instance_id}] Successfully clicked checkbox with regular click")
            except Exception as e:
                logger.warning(f"[Instance {self.instance_id}] Regular click failed: {e}")
                
                # Method 2: JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    click_success = True
                    logger.info(f"[Instance {self.instance_id}] Successfully clicked checkbox with JavaScript click")
                except Exception as e2:
                    logger.warning(f"[Instance {self.instance_id}] JavaScript click failed: {e2}")
                    
                    # Method 3: Scroll into view and try again
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                        time.sleep(1)
                        checkbox.click()
                        click_success = True
                        logger.info(f"[Instance {self.instance_id}] Successfully clicked checkbox after scrolling")
                    except Exception as e3:
                        logger.warning(f"[Instance {self.instance_id}] Scroll and click failed: {e3}")
            
            if click_success:
                # Wait a moment for the checkbox state to register
                time.sleep(1)
                return True
            else:
                logger.error(f"[Instance {self.instance_id}] All click methods failed")
                return False
            
        except TimeoutException:
            logger.error(f"[Instance {self.instance_id}] Timeout waiting for checkbox to load")
            return False
        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Failed to click checkbox: {e}")
            return False
    
    def click_vote_button(self):
        """Click the vote button."""
        try:
            vote_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.vote_button_selector))
            )
            
            logger.info(f"[Instance {self.instance_id}] Clicking vote button...")
            vote_button.click()
            
            # Wait a moment for vote to process
            time.sleep(2)
            logger.info(f"[Instance {self.instance_id}] Vote button clicked successfully")
            return True
            
        except TimeoutException:
            logger.error(f"[Instance {self.instance_id}] Timeout waiting for vote button")
            return False
        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Failed to click vote button: {e}")
            return False
    
    def return_to_poll(self):
        """Click the 'Return To Poll' link."""
        try:
            return_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.return_poll_selector))
            )
            
            logger.info(f"[Instance {self.instance_id}] Clicking 'Return To Poll' link...")
            return_link.click()
            
            # Wait for page to load
            time.sleep(2)
            logger.info(f"[Instance {self.instance_id}] Successfully returned to poll")
            return True
            
        except TimeoutException:
            logger.error(f"[Instance {self.instance_id}] Timeout waiting for 'Return To Poll' link")
            return False
        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Failed to click 'Return To Poll' link: {e}")
            return False
    
    def run_voting_cycle(self):
        """Execute one complete voting cycle."""
        logger.info(f"[Instance {self.instance_id}] Starting voting cycle...")
        
        # Step 1: Click checkbox
        if not self.find_and_click_checkbox():
            self.error_count += 1
            return False
        
        # Step 2: Click vote button
        if not self.click_vote_button():
            self.error_count += 1
            return False
        
        # Step 3: Return to poll
        if not self.return_to_poll():
            self.error_count += 1
            return False
        
        self.vote_count += 1
        logger.info(f"[Instance {self.instance_id}] Voting cycle completed successfully (Total votes: {self.vote_count})")
        return True
    
    def run_automation(self):
        """Run the automation in an infinite loop for this instance."""
        try:
            # Setup driver
            if not self.setup_driver():
                return
            
            # Navigate to poll
            if not self.navigate_to_poll():
                return
            
            self.running = True
            
            logger.info(f"[Instance {self.instance_id}] Starting automation loop...")
            
            while self.running:
                if self.run_voting_cycle():
                    logger.info(f"[Instance {self.instance_id}] Waiting 1 second before next cycle...")
                    time.sleep(1)
                else:
                    logger.warning(f"[Instance {self.instance_id}] Voting cycle failed, waiting 5 seconds before retry...")
                    time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info(f"[Instance {self.instance_id}] Automation stopped by user")
        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Unexpected error in automation: {e}")
        finally:
            self.cleanup()
    
    def stop(self):
        """Stop this instance."""
        self.running = False
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            logger.info(f"[Instance {self.instance_id}] Closing browser...")
            self.driver.quit()
            logger.info(f"[Instance {self.instance_id}] Cleanup complete")

class MultiInstancePollAutomation:
    def __init__(self, num_instances=3):
        self.num_instances = num_instances
        self.url = "https://la.milesplit.com/articles/391971/poll-milesplit-la-girls-performer-of-the-week?utm_source=Iterable&utm_medium=email&utm_campaign=campaign_14740707&utm_content=ad_sales_running_warehouse&utm_term=ad_sales_running_warehouse"
        self.instances = []
        self.executor = None
        
    def create_instances(self):
        """Create the specified number of automation instances."""
        for i in range(1, self.num_instances + 1):
            instance = PollAutomationInstance(i, self.url)
            self.instances.append(instance)
        
        logger.info(f"Created {self.num_instances} automation instances")
    
    def run_all_instances(self):
        """Run all instances concurrently."""
        try:
            self.create_instances()
            
            logger.info(f"Starting {self.num_instances} concurrent automation instances...")
            logger.info("Press Ctrl+C to stop all instances")
            
            # Use ThreadPoolExecutor to run all instances concurrently
            with ThreadPoolExecutor(max_workers=self.num_instances, thread_name_prefix="PollInstance") as executor:
                self.executor = executor
                
                # Submit all instances
                futures = []
                for instance in self.instances:
                    future = executor.submit(instance.run_automation)
                    futures.append(future)
                
                # Wait for all instances to complete or be interrupted
                try:
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Instance failed: {e}")
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, stopping all instances...")
                    
                    # Stop all instances
                    for instance in self.instances:
                        instance.stop()
                    
                    # Wait a moment for graceful shutdown
                    time.sleep(2)
                    
                    logger.info("All instances stopped")
                    
        except Exception as e:
            logger.error(f"Error in multi-instance automation: {e}")
        finally:
            self.cleanup_all()
    
    def cleanup_all(self):
        """Clean up all instances."""
        logger.info("Cleaning up all instances...")
        for instance in self.instances:
            instance.cleanup()
        
        # Print final statistics
        total_votes = sum(instance.vote_count for instance in self.instances)
        total_errors = sum(instance.error_count for instance in self.instances)
        
        logger.info(f"=== Final Statistics ===")
        logger.info(f"Total votes across all instances: {total_votes}")
        logger.info(f"Total errors across all instances: {total_errors}")
        
        for i, instance in enumerate(self.instances, 1):
            logger.info(f"Instance {i}: {instance.vote_count} votes, {instance.error_count} errors")

def main():
    """Main function to run the multi-instance automation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Instance Poll Automation')
    parser.add_argument('--instances', type=int, default=3, 
                       help='Number of concurrent instances to run (default: 3, max: 8)')
    
    args = parser.parse_args()
    
    # Limit to 8 instances maximum
    num_instances = min(max(1, args.instances), 8)
    
    logger.info(f"Starting Multi-Instance Poll Automation with {num_instances} instances")
    
    automation = MultiInstancePollAutomation(num_instances)
    automation.run_all_instances()

if __name__ == "__main__":
    main()
