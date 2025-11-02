#!/usr/bin/env python3
"""
Test WhatsApp alert functionality
"""
from twilio.rest import Client
import json
from datetime import datetime

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

print("Testing Twilio WhatsApp connection...\n")
print(f"Account SID: {config['twilio_account_sid']}")
print(f"From: {config['twilio_whatsapp_from']}")
print(f"To: {config['twilio_whatsapp_to']}\n")

# Create test message
test_message = f"""📊 *Shein Monitor Test*

This is a test alert from your Shein monitor.

If you receive this, WhatsApp alerts are working! ✅

Timestamp: {datetime.utcnow().isoformat()}Z"""

try:
    client = Client(config['twilio_account_sid'], config['twilio_auth_token'])
    
    message = client.messages.create(
        body=test_message,
        from_=config['twilio_whatsapp_from'],
        to=config['twilio_whatsapp_to']
    )
    
    print(f"✅ SUCCESS! Message sent!")
    print(f"Message SID: {message.sid}")
    print(f"Status: {message.status}")
    print(f"\nCheck your WhatsApp at: {config['twilio_whatsapp_to']}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nPossible issues:")
    print("1. Have you joined the Twilio WhatsApp sandbox?")
    print("   - Send 'join <code>' to +1 415 523 8886")
    print("2. Check your Twilio credentials are correct")
    print("3. Verify your phone number format: whatsapp:+919956644505")
