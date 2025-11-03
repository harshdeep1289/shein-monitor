#!/usr/bin/env python3
"""
Shein Product Monitor with Product Links
Tracks individual products and sends WhatsApp alerts with links for new men's items
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from twilio.rest import Client
import os
import re


class SheinProductMonitor:
    def __init__(self, config_path='config.json'):
        """Initialize the monitor with configuration"""
        self.config = self.load_config(config_path)
        self.storage_path = 'tracked_products.json'
        self.url = self.config.get('url', 'https://www.sheinindia.in/c/sverse-5939-37961')
        self.check_interval = self.config.get('check_interval_seconds', 300)
        
        # Twilio configuration
        self.twilio_client = Client(
            self.config['twilio_account_sid'],
            self.config['twilio_auth_token']
        )
        self.twilio_from = self.config['twilio_whatsapp_from']
        self.twilio_to = self.config['twilio_whatsapp_to']
        
        # Initialize browser driver
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Set up Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            print("✓ Chrome driver initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Chrome driver: {e}")
            raise
    
    def load_config(self, config_path):
        """Load configuration from JSON file or environment variables"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        config['twilio_account_sid'] = os.environ.get('TWILIO_ACCOUNT_SID', config.get('twilio_account_sid'))
        config['twilio_auth_token'] = os.environ.get('TWILIO_AUTH_TOKEN', config.get('twilio_auth_token'))
        config['twilio_whatsapp_from'] = os.environ.get('TWILIO_WHATSAPP_FROM', config.get('twilio_whatsapp_from'))
        config['twilio_whatsapp_to'] = os.environ.get('TWILIO_WHATSAPP_TO', config.get('twilio_whatsapp_to'))
        
        return config
    
    def load_tracked_products(self):
        """Load previously tracked products from JSON file"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {'men': [], 'women': [], 'timestamp': None}
    
    def save_tracked_products(self, products):
        """Save tracked products to JSON file"""
        data = {
            'men': products.get('men', []),
            'women': products.get('women', []),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def fetch_page(self):
        """Fetch the Shein category page using Selenium"""
        try:
            self.driver.get(self.url)
            time.sleep(5)
            
            # Scroll to load more products
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            return self.driver.page_source
        except Exception as e:
            print(f"✗ Error fetching page: {e}")
            raise
    
    def extract_products(self, html):
        """Extract product details from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        products = {'men': [], 'women': []}
        
        # Try to find product cards/items
        # Common Shein selectors (may need adjustment)
        product_elements = soup.find_all(['article', 'div'], class_=re.compile(r'product|goods-item|S-product', re.IGNORECASE))
        
        print(f"Found {len(product_elements)} potential product elements")
        
        for elem in product_elements:
            try:
                # Extract product link
                link_tag = elem.find('a', href=True)
                if not link_tag:
                    continue
                
                product_url = link_tag['href']
                if not product_url.startswith('http'):
                    product_url = 'https://www.sheinindia.in' + product_url
                
                # Extract product ID from URL
                product_id_match = re.search(r'-p-(\d+)', product_url)
                if not product_id_match:
                    continue
                product_id = product_id_match.group(1)
                
                # Extract product name
                title_tag = elem.find(['h2', 'h3', 'div'], class_=re.compile(r'title|name', re.IGNORECASE))
                product_name = title_tag.get_text(strip=True) if title_tag else 'Unknown Product'
                
                # Extract price
                price_tag = elem.find(['span', 'div'], class_=re.compile(r'price', re.IGNORECASE))
                price = price_tag.get_text(strip=True) if price_tag else 'N/A'
                
                # Try to determine gender from product name or attributes
                product_text = elem.get_text().lower()
                is_men = any(keyword in product_text for keyword in ['men', 'man', 'mens', "men's", 'male', 'boy'])
                
                product_info = {
                    'id': product_id,
                    'name': product_name[:100],  # Limit length
                    'url': product_url,
                    'price': price,
                    'detected_at': datetime.utcnow().isoformat() + 'Z'
                }
                
                if is_men:
                    products['men'].append(product_info)
                else:
                    products['women'].append(product_info)
                    
            except Exception as e:
                print(f"Error parsing product element: {e}")
                continue
        
        print(f"✓ Extracted {len(products['men'])} men's products, {len(products['women'])} women's products")
        return products
    
    def find_new_products(self, old_products, new_products, category='men'):
        """Find new products in a category"""
        old_ids = set(p['id'] for p in old_products.get(category, []))
        new_items = []
        
        for product in new_products.get(category, []):
            if product['id'] not in old_ids:
                new_items.append(product)
        
        return new_items
    
    def format_whatsapp_message(self, new_products):
        """Format the WhatsApp alert message for new products"""
        message = "🆕 *New Men's Products on Shein!*\n\n"
        
        for i, product in enumerate(new_products[:5], 1):  # Limit to 5 products per message
            message += f"{i}. {product['name']}\n"
            message += f"   💰 {product['price']}\n"
            message += f"   🔗 {product['url']}\n\n"
        
        if len(new_products) > 5:
            message += f"... and {len(new_products) - 5} more new products!\n\n"
        
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def send_whatsapp_alert(self, message):
        """Send WhatsApp message via Twilio"""
        try:
            # Split message if too long (WhatsApp limit ~1600 chars)
            if len(message) > 1500:
                # Send first part
                msg1 = self.twilio_client.messages.create(
                    body=message[:1500] + "...",
                    from_=self.twilio_from,
                    to=self.twilio_to
                )
                print(f"✓ WhatsApp alert (part 1) sent (SID: {msg1.sid})")
            else:
                msg = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_from,
                    to=self.twilio_to
                )
                print(f"✓ WhatsApp alert sent successfully (SID: {msg.sid})")
            return True
        except Exception as e:
            print(f"✗ Failed to send WhatsApp alert: {e}")
            return False
    
    def run_once(self):
        """Run a single monitoring check"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new products...")
        
        try:
            # Fetch and parse page
            html = self.fetch_page()
            new_products = self.extract_products(html)
            
            if not new_products['men'] and not new_products['women']:
                print("✗ Failed to extract products from page")
                return False
            
            # Load previous products
            old_products = self.load_tracked_products()
            
            # Find new men's products
            new_mens_products = self.find_new_products(old_products, new_products, 'men')
            
            if new_mens_products:
                print(f"🎉 Found {len(new_mens_products)} new men's products!")
                for product in new_mens_products:
                    print(f"  - {product['name']} ({product['price']})")
                
                message = self.format_whatsapp_message(new_mens_products)
                print(f"\nWhatsApp message:\n{message}\n")
                self.send_whatsapp_alert(message)
            else:
                if old_products['timestamp']:
                    print("✓ No new men's products detected")
                else:
                    print("✓ Initial product list stored")
            
            # Save current products
            self.save_tracked_products(new_products)
            return True
            
        except Exception as e:
            print(f"✗ Error during monitoring: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_continuous(self):
        """Run continuous monitoring loop"""
        print("🚀 Starting Shein Product Monitor (Product Tracking)...")
        print(f"📍 Monitoring: {self.url}")
        print(f"⏱ Check interval: {self.check_interval} seconds")
        print(f"📱 WhatsApp alerts to: {self.twilio_to}")
        print("🎯 Tracking: New men's products only")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                print(f"\nNext check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
        finally:
            if self.driver:
                self.driver.quit()
                print("✓ Browser closed")


def main():
    """Main entry point"""
    monitor = SheinProductMonitor()
    monitor.run_continuous()


if __name__ == '__main__':
    main()
