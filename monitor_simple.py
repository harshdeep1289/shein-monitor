#!/usr/bin/env python3
"""
Shein Product Count Monitor with WhatsApp Alerts (No Selenium)
Monitors product counts on Shein category page and sends alerts via Twilio WhatsApp
"""

import cloudscraper
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from twilio.rest import Client
import os
import re


class SheinMonitor:
    def __init__(self, config_path='config.json'):
        """Initialize the monitor with configuration"""
        self.config = self.load_config(config_path)
        self.storage_path = self.config.get('storage_path', 'product_counts.json')
        self.url = self.config.get('url', 'https://www.sheinindia.in/c/sverse-5939-37961')
        self.check_interval = self.config.get('check_interval_seconds', 300)
        
        # Twilio configuration
        self.twilio_client = Client(
            self.config['twilio_account_sid'],
            self.config['twilio_auth_token']
        )
        self.twilio_from = self.config['twilio_whatsapp_from']
        self.twilio_to = self.config['twilio_whatsapp_to']
        
        # Initialize cloudscraper (bypasses Cloudflare and bot detection)
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
    
    def load_config(self, config_path):
        """Load configuration from JSON file or environment variables"""
        # Try to load from file first
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Override with environment variables if present
        config['twilio_account_sid'] = os.environ.get('TWILIO_ACCOUNT_SID', config.get('twilio_account_sid'))
        config['twilio_auth_token'] = os.environ.get('TWILIO_AUTH_TOKEN', config.get('twilio_auth_token'))
        config['twilio_whatsapp_from'] = os.environ.get('TWILIO_WHATSAPP_FROM', config.get('twilio_whatsapp_from'))
        config['twilio_whatsapp_to'] = os.environ.get('TWILIO_WHATSAPP_TO', config.get('twilio_whatsapp_to'))
        
        return config
    
    def load_stored_counts(self):
        """Load previously stored counts from JSON file"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_counts(self, counts):
        """Save counts to JSON file"""
        data = {
            'counts': counts,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def fetch_page(self):
        """Fetch the Shein category page using cloudscraper"""
        try:
            response = self.scraper.get(self.url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"✗ Error fetching page: {e}")
            raise
    
    def extract_counts(self, html):
        """Extract product counts from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        counts = {}
        
        # Try multiple strategies to extract counts
        # Strategy 1: Look for total products count
        total_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:products|items)', html, re.IGNORECASE)
        if total_match:
            counts['total'] = int(total_match.group(1).replace(',', ''))
        
        # Strategy 2: Look for gender filters with counts
        # Search for patterns like "Women (2,914)" or "Men (7)"
        women_match = re.search(r'Women[^\d]*\((\d{1,3}(?:,\d{3})*)\)', html, re.IGNORECASE)
        men_match = re.search(r'Men[^\d]*\((\d{1,3}(?:,\d{3})*)\)', html, re.IGNORECASE)
        
        if women_match:
            counts['women'] = int(women_match.group(1).replace(',', ''))
        if men_match:
            counts['men'] = int(men_match.group(1).replace(',', ''))
        
        # Strategy 3: Parse structured data or JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Look for numberOfItems or similar fields
                if isinstance(data, dict) and 'numberOfItems' in data:
                    counts['total'] = int(data['numberOfItems'])
            except:
                pass
        
        # Strategy 4: Look for filter checkboxes or radio buttons with counts
        filters = soup.find_all(['label', 'div', 'span'], string=re.compile(r'(Women|Men)\s*\(\d+\)'))
        for filter_elem in filters:
            text = filter_elem.get_text()
            if 'Women' in text:
                match = re.search(r'\((\d{1,3}(?:,\d{3})*)\)', text)
                if match:
                    counts['women'] = int(match.group(1).replace(',', ''))
            elif 'Men' in text:
                match = re.search(r'\((\d{1,3}(?:,\d{3})*)\)', text)
                if match:
                    counts['men'] = int(match.group(1).replace(',', ''))
        
        # Strategy 5: Look for product grid and count items
        product_items = soup.find_all(['article', 'div'], class_=re.compile(r'product|item', re.IGNORECASE))
        if product_items and not counts.get('total'):
            counts['visible_products'] = len(product_items)
        
        return counts if counts else None
    
    def compare_counts(self, old_counts, new_counts):
        """Compare old and new counts, return changes"""
        changes = {}
        
        if old_counts is None:
            # First run, no comparison
            return None
        
        all_keys = set(old_counts.keys()) | set(new_counts.keys())
        has_changes = False
        
        for key in all_keys:
            old_val = old_counts.get(key, 0)
            new_val = new_counts.get(key, 0)
            
            if old_val != new_val:
                has_changes = True
                changes[key] = {
                    'old': old_val,
                    'new': new_val,
                    'diff': new_val - old_val
                }
        
        return changes if has_changes else None
    
    def format_whatsapp_message(self, counts, changes, timestamp):
        """Format the WhatsApp alert message"""
        message = "📊 *Shein Stock Update Alert*\n\n"
        
        # Format counts with changes
        for key in ['total', 'women', 'men', 'visible_products']:
            if key in counts:
                label = key.replace('_', ' ').capitalize()
                value = counts[key]
                
                if changes and key in changes:
                    diff = changes[key]['diff']
                    sign = '+' if diff > 0 else ''
                    message += f"{label}: {value:,} ({sign}{diff:,})\n"
                else:
                    message += f"{label}: {value:,}\n"
        
        message += f"\n🕐 Timestamp: {timestamp}\n"
        message += f"🔗 Source: {self.url}"
        
        return message
    
    def send_whatsapp_alert(self, message):
        """Send WhatsApp message via Twilio"""
        try:
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
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking Shein product counts...")
        
        try:
            # Fetch and parse page
            html = self.fetch_page()
            new_counts = self.extract_counts(html)
            
            if not new_counts:
                print("✗ Failed to extract product counts from page")
                return False
            
            print(f"✓ Current counts: {new_counts}")
            
            # Load previous counts
            stored_data = self.load_stored_counts()
            old_counts = stored_data['counts'] if stored_data else None
            
            # Compare counts
            changes = self.compare_counts(old_counts, new_counts)
            
            if changes:
                print(f"⚠ Changes detected: {changes}")
                timestamp = datetime.utcnow().isoformat() + 'Z'
                message = self.format_whatsapp_message(new_counts, changes, timestamp)
                print(f"\nWhatsApp message:\n{message}\n")
                self.send_whatsapp_alert(message)
            else:
                if old_counts:
                    print("✓ No changes detected")
                else:
                    print("✓ Initial counts stored")
            
            # Save new counts
            self.save_counts(new_counts)
            return True
            
        except Exception as e:
            print(f"✗ Error during monitoring: {e}")
            return False
    
    def run_continuous(self):
        """Run continuous monitoring loop"""
        print("🚀 Starting Shein Product Monitor...")
        print(f"📍 Monitoring: {self.url}")
        print(f"⏱ Check interval: {self.check_interval} seconds")
        print(f"📱 WhatsApp alerts to: {self.twilio_to}")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")


def main():
    """Main entry point"""
    monitor = SheinMonitor()
    monitor.run_once()


if __name__ == '__main__':
    main()
