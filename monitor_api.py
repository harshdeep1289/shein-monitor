#!/usr/bin/env python3
"""
Shein Product Count Monitor with WhatsApp Alerts (API-based)
Monitors product counts using Shein's API and sends alerts via Twilio WhatsApp
"""

import cloudscraper
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
        
        # Extract category ID from URL
        self.category_id = self.extract_category_id(self.url)
        
        # Twilio configuration
        self.twilio_client = Client(
            self.config['twilio_account_sid'],
            self.config['twilio_auth_token']
        )
        self.twilio_from = self.config['twilio_whatsapp_from']
        self.twilio_to = self.config['twilio_whatsapp_to']
        
        # Initialize cloudscraper
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
    
    def extract_category_id(self, url):
        """Extract category ID from Shein URL"""
        # URL format: https://www.sheinindia.in/c/sverse-5939-37961
        match = re.search(r'/c/[^/]+-(\d+)-(\d+)', url)
        if match:
            return match.group(2)  # Return the last number
        return None
    
    def load_config(self, config_path):
        """Load configuration from JSON file or environment variables"""
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
        """Fetch the Shein page and try to extract data from JavaScript"""
        try:
            # Try to get the HTML page first
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.sheinindia.in/',
            }
            response = self.scraper.get(self.url, headers=headers, timeout=30, allow_redirects=True)
            
            # Try without raising for status first to see what we get
            if response.status_code == 403:
                print(f"✗ Still getting 403. Response headers: {dict(response.headers)}")
                # Try a more stealthy approach - just fetch homepage first
                print("Trying to establish session by visiting homepage first...")
                self.scraper.get('https://www.sheinindia.in/', headers=headers, timeout=30)
                time.sleep(2)
                response = self.scraper.get(self.url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"✗ Error fetching page: {e}")
            # Return None instead of raising to allow graceful handling
            return None
    
    def extract_counts(self, html):
        """Extract product counts from HTML or return dummy data"""
        if not html:
            print("⚠ No HTML content, using fallback method...")
            # Return a basic count to test the notification system
            return {'status': 'unavailable', 'note': 'Could not fetch data due to bot protection'}
        
        counts = {}
        
        # Try to find JSON data in script tags
        json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', html, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                # Try to extract product count from the data
                if 'products' in data:
                    counts['total'] = len(data['products'])
            except:
                pass
        
        # Try regex patterns
        total_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:products|items)', html, re.IGNORECASE)
        if total_match:
            counts['total'] = int(total_match.group(1).replace(',', ''))
        
        women_match = re.search(r'Women[^\d]*\((\d{1,3}(?:,\d{3})*)\)', html, re.IGNORECASE)
        men_match = re.search(r'Men[^\d]*\((\d{1,3}(?:,\d{3})*)\)', html, re.IGNORECASE)
        
        if women_match:
            counts['women'] = int(women_match.group(1).replace(',', ''))
        if men_match:
            counts['men'] = int(men_match.group(1).replace(',', ''))
        
        return counts if counts else None
    
    def compare_counts(self, old_counts, new_counts):
        """Compare old and new counts, return changes"""
        changes = {}
        
        if old_counts is None:
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
        
        if 'status' in counts:
            message += f"⚠️ Status: {counts['status']}\n"
            if 'note' in counts:
                message += f"{counts['note']}\n"
        else:
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
                # Use a placeholder to indicate the check ran but couldn't get data
                new_counts = {'status': 'check_failed', 'timestamp': datetime.utcnow().isoformat()}
            
            print(f"✓ Current counts: {new_counts}")
            
            # Load previous counts
            stored_data = self.load_stored_counts()
            old_counts = stored_data['counts'] if stored_data else None
            
            # Compare counts (skip comparison if status check)
            if 'status' not in new_counts:
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
            import traceback
            traceback.print_exc()
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
