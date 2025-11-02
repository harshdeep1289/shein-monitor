# Shein Product Monitor - Local Setup Guide

## ⚠️ Important: GitHub Actions Not Supported

Shein has strong bot protection that blocks GitHub Actions and cloud servers. **This monitor must run locally on your computer.**

## Quick Local Setup

### 1. Install Dependencies
```bash
cd ~/shein_monitor
pip3 install -r requirements.txt
```

### 2. Get Twilio Credentials

1. Sign up at https://www.twilio.com/try-twilio (free trial)
2. Go to Twilio Console Dashboard
3. Copy your **Account SID** and **Auth Token**
4. Join WhatsApp Sandbox:
   - Go to https://www.twilio.com/console/sms/whatsapp/sandbox
   - Send the join code (e.g., "join [word]-[word]") to **+1 415 523 8886** on WhatsApp

### 3. Configure
```bash
cp config.json.example config.json
nano config.json  # or use any text editor
```

Update with your details:
```json
{
  "url": "https://www.sheinindia.in/c/sverse-5939-37961",
  "check_interval_seconds": 300,
  "storage_path": "product_counts.json",
  "twilio_account_sid": "YOUR_ACCOUNT_SID_HERE",
  "twilio_auth_token": "YOUR_AUTH_TOKEN_HERE",
  "twilio_whatsapp_from": "whatsapp:+14155238886",
  "twilio_whatsapp_to": "whatsapp:+919956644505"
}
```

### 4. Test WhatsApp
```bash
python3 test_whatsapp.py
```

You should receive a test message on WhatsApp!

### 5. Run the Monitor

**Single check:**
```bash
python3 monitor_api.py
```

**Continuous monitoring (keep running):**
```bash
python3 monitor.py
```

**Run in background:**
```bash
nohup python3 monitor.py > monitor.log 2>&1 &
```

**Auto-start on system boot (Mac/Linux):**
```bash
crontab -e
# Add this line:
@reboot cd /Users/harshdeepsingh/shein_monitor && python3 monitor.py >> monitor.log 2>&1
```

## How It Works

1. Checks the Shein page every 5 minutes (configurable)
2. Extracts product counts for Women/Men/Total
3. Compares with previous counts
4. Sends WhatsApp alert if anything changed

## WhatsApp Alert Example

```
📊 *Shein Stock Update Alert*

Total: 2,921 (+7)
Women: 2,914 (+5)
Men: 7 (+2)

🕐 Timestamp: 2025-11-03T03:10:00Z
🔗 Source: https://www.sheinindia.in/...
```

## Troubleshooting

### Not receiving WhatsApp messages?
- Make sure you joined the Twilio sandbox
- Check credentials in config.json
- Run `python3 test_whatsapp.py` to test

### Script crashes or errors?
- Check monitor.log file
- Verify Python 3.7+ is installed
- Reinstall dependencies: `pip3 install -r requirements.txt --upgrade`

### Bot protection / 403 errors?
- This is why it must run locally
- Running from your home network works better
- GitHub Actions / cloud servers get blocked

## Files

- `monitor.py` - Main continuous monitor (Selenium-based, most reliable)
- `monitor_api.py` - Lighter version without Selenium
- `config.json` - Your configuration (keep private!)
- `product_counts.json` - Stored counts
- `monitor.log` - Log file

## Cost

- **Twilio Free Trial**: $15 credit (enough for ~1000 WhatsApp messages)
- **After trial**: ~$0.005 per WhatsApp message
- **This script**: Free and open source

## Support

For issues, check the main README.md or create an issue on GitHub.
