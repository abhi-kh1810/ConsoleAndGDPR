import json
import os
import time
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright
from pathlib import Path

class ConsoleErrorScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.console_errors = []
        self.site_url = None
        self.gdpr_present = False
        
    def load_env_file(self):
        """Load environment variables from .env file"""
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if not os.path.exists(env_path):
            raise FileNotFoundError("No .env file found. Please create a .env file with SITE_URL=<your_site_url>")
        
        with open(env_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'SITE_URL':
                        self.site_url = value.strip()
                        break
        
        if not self.site_url:
            raise ValueError("SITE_URL not found in .env file")
        
        # Add protocol if missing
        if not self.site_url.startswith(('http://', 'https://')):
            self.site_url = 'https://' + self.site_url
            print(f"Added https:// protocol to URL")
        
        print(f"Loaded site URL: {self.site_url}")
    
    def setup_browser(self):
        """Setup Playwright browser with console logging"""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        
        # Launch browser
        self.browser = self.playwright.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=[
                "--no-first-run",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        # Create new context
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Create new page
        self.page = context.new_page()
        
        # Set up console error listener
        self.page.on("console", self.handle_console_message)
        self.page.on("pageerror", self.handle_page_error)
        
        print("Browser setup complete")
    
    def handle_console_message(self, msg):
        """Handle console messages and filter for errors"""
        if msg.type in ['error', 'warning']:
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'type': msg.type,
                'text': msg.text,
                'location': msg.location,
                'url': self.page.url if self.page else None
            }
            self.console_errors.append(error_data)
            print(f"Console {msg.type}: {msg.text}")
    
    def handle_page_error(self, error):
        """Handle JavaScript page errors"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'page_error',
            'text': str(error),
            'location': None,
            'url': self.page.url if self.page else None
        }
        self.console_errors.append(error_data)
        print(f"Page error: {error}")
    
    def find_and_click_accept_button(self):
        """Find and click the 'Accept All' cookie button"""
        # Common selectors for cookie accept buttons
        accept_selectors = [
            # Generic accept all buttons
            "button:has-text('Accept All')",
            "button:has-text('Accept all')",
            "button:has-text('ACCEPT ALL')",
            "button:has-text('Accept All Cookies')",
            "button:has-text('Accept all cookies')",
            
            # Common ID and class patterns
            "#accept-all",
            "#acceptAll",
            "#accept_all",
            ".accept-all",
            ".acceptAll",
            ".accept_all",
            
            # Common button text variations
            "button:has-text('I Accept')",
            "button:has-text('I Agree')",
            "button:has-text('OK')",
            "button:has-text('Got it')",
            "button:has-text('Agree')",
            "button:has-text('Continue')",
            
            # ARIA labels
            "button[aria-label*='Accept']",
            "button[aria-label*='accept']",
            
            # Data attributes
            "button[data-testid*='accept']",
            "button[data-cy*='accept']",
            
            # Common cookie banner frameworks
            "[id*='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']",
            ".cc-allow-all",
            ".cookie-accept",
            ".gdpr-accept",
            
            # Generic patterns with contains text
            "//*[contains(text(), 'Accept') and (self::button or self::a)]",
            "//*[contains(text(), 'I agree') and (self::button or self::a)]",
            "//*[contains(text(), 'Continue') and (self::button or self::a)]"
        ]
        
        print("Looking for 'Accept All' cookie button...")
        
        for selector in accept_selectors:
            try:
                # Wait a short time for the element to appear
                if selector.startswith("//"):
                    # XPath selector
                    element = self.page.locator(f"xpath={selector}").first
                else:
                    # CSS selector
                    element = self.page.locator(selector).first
                
                if element.is_visible(timeout=2000):
                    print(f"Found accept button with selector: {selector}")
                    element.click(timeout=5000)
                    print("Successfully clicked 'Accept All' button")
                    self.gdpr_present = True  # Set GDPR flag to True when button is found and clicked
                    time.sleep(2)  # Wait for any animations/updates
                    return True
            except Exception as e:
                # Continue to next selector if this one fails
                continue
        
        print("No 'Accept All' button found or unable to click")
        return False
    
    def navigate_and_capture_errors(self):
        """Navigate to the site and capture console errors"""
        try:
            print(f"Navigating to: {self.site_url}")
            
            # Navigate to the site
            self.page.goto(self.site_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait a moment for initial page load
            time.sleep(3)
            
            # Try to find and click accept button
            self.find_and_click_accept_button()
            
            # Wait for the page to fully load and any additional scripts to run
            print("Waiting for page to fully load...")
            self.page.wait_for_load_state('networkidle', timeout=30000)
            
            # Additional wait to capture any delayed console errors
            time.sleep(5)
            
            # Scroll down the page to trigger any lazy-loaded content
            print("Scrolling page to trigger additional content...")
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            
            # Scroll back to top
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)
            
            print(f"Captured {len(self.console_errors)} console errors/warnings")
            
        except Exception as e:
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'type': 'navigation_error',
                'text': f"Navigation error: {str(e)}",
                'location': None,
                'url': self.site_url
            }
            self.console_errors.append(error_data)
            print(f"Navigation error: {e}")
    
    def save_errors_to_json(self):
        """Save captured errors to JSON file in the specified directory structure"""
        if not self.console_errors:
            print("No console errors captured")
            return
        
        # Parse the URL to get the domain
        try:
            parsed_url = urlparse(self.site_url)
            domain = parsed_url.netloc.replace('www.', '').replace(':', '_')
            if not domain:  # Fallback if parsing fails
                domain = self.site_url.replace('https://', '').replace('http://', '').replace('www.', '').replace('/', '_').replace(':', '_')
        except Exception:
            # Fallback domain extraction
            domain = self.site_url.replace('https://', '').replace('http://', '').replace('www.', '').replace('/', '_').replace(':', '_')
        
        # Create directory structure: console_error/site_url/<domain>.json
        output_dir = Path("console_error/site_url")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the JSON file path
        json_filename = f"{domain}.json"
        json_filepath = output_dir / json_filename
        
        # Prepare the data to save
        output_data = {
            'site_url': self.site_url,
            'domain': domain,
            'scraped_at': datetime.now().isoformat(),
            'GDPR_PRESENT': "TRUE" if self.gdpr_present else "FALSE",
            'total_errors': len(self.console_errors),
            'errors': self.console_errors
        }
        
        # Save to JSON file
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Console errors saved to: {json_filepath}")
        print(f"Total errors captured: {len(self.console_errors)}")
        print(f"GDPR/Cookie consent detected: {'YES' if self.gdpr_present else 'NO'}")
        
        # Print summary of error types
        error_types = {}
        for error in self.console_errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        print("Error summary:")
        for error_type, count in error_types.items():
            print(f"  - {error_type}: {count}")
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("Browser cleanup complete")
    
    def run(self):
        """Main execution method"""
        try:
            print("Starting console error scraper...")
            
            # Load environment variables
            self.load_env_file()
            
            # Setup browser
            self.setup_browser()
            
            # Navigate and capture errors
            self.navigate_and_capture_errors()
            
            # Save results
            self.save_errors_to_json()
            
        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            # Always cleanup
            self.cleanup()

def main():
    """Main function to run the scraper"""
    scraper = ConsoleErrorScraper()
    scraper.run()

if __name__ == "__main__":
    main()
