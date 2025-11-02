#!/usr/bin/env python3
"""
Single-run version for GitHub Actions
"""
import os
import sys

# Check if running in GitHub Actions
if os.getenv('GITHUB_ACTIONS'):
    # Override config loading to use environment variables
    import json
    
    class GithubConfig:
        def __init__(self):
            self.config = {
                'url': 'https://www.sheinindia.in/c/sverse-5939-37961',
                'check_interval_seconds': 60,
                'storage_path': 'product_counts.json',
                'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
                'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
                'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM'),
                'twilio_whatsapp_to': os.getenv('TWILIO_WHATSAPP_TO')
            }
        
        def get(self, key, default=None):
            return self.config.get(key, default)
        
        def __getitem__(self, key):
            return self.config[key]
    
    # Monkey patch the monitor class
    from monitor import SheinMonitor
    original_load_config = SheinMonitor.load_config
    
    def load_config_from_env(self, config_path):
        return GithubConfig().config
    
    SheinMonitor.load_config = load_config_from_env

from monitor import SheinMonitor

if __name__ == '__main__':
    try:
        monitor = SheinMonitor()
        success = monitor.run_once()
        
        if monitor.driver:
            monitor.driver.quit()
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
