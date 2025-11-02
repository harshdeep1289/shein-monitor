# Shein Product Count Monitor with WhatsApp Alerts

A Python script that continuously monitors product counts on Shein category pages and sends WhatsApp alerts via Twilio when changes are detected.

## Features

- 🔍 Monitors total product count and gender-specific counts (Women/Men)
- 📱 Sends WhatsApp alerts via Twilio when counts change
- 💾 Persistent storage to track historical data
- ➕➖ Shows increase/decrease indicators in alerts
- 🔄 Continuous monitoring with configurable intervals
- 🛡️ Multiple extraction strategies for robust data collection

## Prerequisites

1. **Python 3.7+**
2. **Twilio Account** with WhatsApp messaging enabled
   - Sign up at https://www.twilio.com/
   - Enable WhatsApp sandbox or get approved WhatsApp number
   - Get your Account SID and Auth Token

## Installation

1. **Navigate to the project directory:**
   ```bash
   cd ~/shein_monitor
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure the script:**
   ```bash
   cp config.json.example config.json
   ```

4. **Edit `config.json` with your credentials:**
   ```json
   {
     "url": "https://www.sheinindia.in/c/sverse-5939-37961",
     "check_interval_seconds": 300,
     "storage_path": "product_counts.json",
     "twilio_account_sid": "YOUR_TWILIO_ACCOUNT_SID",
     "twilio_auth_token": "YOUR_TWILIO_AUTH_TOKEN",
     "twilio_whatsapp_from": "whatsapp:+14155238886",
     "twilio_whatsapp_to": "whatsapp:+1234567890"
   }
   ```

   **Configuration parameters:**
   - `url`: Shein category page URL to monitor
   - `check_interval_seconds`: Time between checks (default: 300 = 5 minutes)
   - `storage_path`: File to store product counts
   - `twilio_account_sid`: Your Twilio Account SID
   - `twilio_auth_token`: Your Twilio Auth Token
   - `twilio_whatsapp_from`: Twilio WhatsApp number (sandbox: whatsapp:+14155238886)
   - `twilio_whatsapp_to`: Your WhatsApp number in format whatsapp:+1234567890

## Twilio WhatsApp Setup

### Option 1: Twilio WhatsApp Sandbox (Quick Testing)

1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Send the join code from your WhatsApp to the sandbox number
3. Use `whatsapp:+14155238886` as `twilio_whatsapp_from`
4. Use your number as `whatsapp:+YOUR_PHONE_NUMBER` for `twilio_whatsapp_to`

### Option 2: Approved WhatsApp Business Number (Production)

1. Request WhatsApp Business API access from Twilio
2. Complete the approval process
3. Use your approved WhatsApp number

## Usage

### Run the monitor:
```bash
python3 monitor.py
```

### Run in the background (macOS/Linux):
```bash
nohup python3 monitor.py > monitor.log 2>&1 &
```

### Stop background process:
```bash
# Find the process ID
ps aux | grep monitor.py

# Kill the process
kill <PID>
```

### Run as a scheduled task (cron):
```bash
# Edit crontab
crontab -e

# Add this line to run on system startup
@reboot cd /Users/harshdeepsingh/shein_monitor && python3 monitor.py >> monitor.log 2>&1
```

## Output Example

**Console Output:**
```
🚀 Starting Shein Product Monitor...
📍 Monitoring: https://www.sheinindia.in/c/sverse-5939-37961
⏱ Check interval: 300 seconds
📱 WhatsApp alerts to: whatsapp:+1234567890

Press Ctrl+C to stop

[2025-11-03 03:10:00] Checking Shein product counts...
✓ Current counts: {'total': 2921, 'women': 2914, 'men': 7}
⚠ Changes detected: {'total': {'old': 2914, 'new': 2921, 'diff': 7}, ...}

WhatsApp message:
📊 *Shein Stock Update Alert*

Total: 2,921 (+7)
Women: 2,914 (+5)
Men: 7 (+2)

🕐 Timestamp: 2025-11-03T03:10:00Z
🔗 Source: https://www.sheinindia.in/c/sverse-5939-37961

✓ WhatsApp alert sent successfully (SID: SM...)
```

## Files Generated

- `product_counts.json` - Stores the latest counts and timestamp
- `monitor.log` - Log file (if running in background)

## Troubleshooting

### Issue: "Failed to extract product counts"
- The website structure may have changed
- Check if the page loads correctly in a browser
- You may need to update the extraction patterns in `extract_counts()`

### Issue: "Failed to send WhatsApp alert"
- Verify Twilio credentials are correct
- Check if WhatsApp sandbox is still active
- Ensure your phone number is in the correct format

### Issue: Rate limiting or blocking
- Increase `check_interval_seconds` to check less frequently
- The script uses a browser User-Agent to appear as a normal browser

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit `config.json` with real credentials to version control
- Keep your Twilio credentials secure
- Use environment variables for production deployments

## Customization

### Change monitoring interval:
Edit `check_interval_seconds` in `config.json` (value in seconds)

### Monitor different page:
Change `url` in `config.json`

### Add more metrics:
Modify the `extract_counts()` method in `monitor.py` to parse additional data

## License

MIT License - Feel free to modify and use as needed.
