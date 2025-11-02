# Deploy to GitHub Actions (Free Cloud Monitoring)

Run this monitor every minute in the cloud without keeping your computer on!

## Steps:

### 1. Create GitHub Repository

```bash
cd ~/shein_monitor
git init
git add .
git commit -m "Initial commit - Shein product monitor"
```

Go to https://github.com/new and create a new repository (e.g., `shein-monitor`)

```bash
git remote add origin https://github.com/YOUR_USERNAME/shein-monitor.git
git branch -M main
git push -u origin main
```

### 2. Add GitHub Secrets

Go to your repository on GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Secret Name | Value |
|-------------|-------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` (Twilio sandbox) |
| `TWILIO_WHATSAPP_TO` | Your WhatsApp number (format: `whatsapp:+1234567890`) |

### 3. Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Click "I understand my workflows, go ahead and enable them"
3. The workflow will run automatically every minute!

### 4. Manual Trigger (Optional)

You can also manually run the workflow:
- Go to **Actions** tab
- Click on "Shein Product Monitor"
- Click "Run workflow"

## How it Works

- ✅ Runs every minute automatically
- ✅ Stores product counts in the repository
- ✅ Sends WhatsApp alerts when counts change
- ✅ Completely free (GitHub Actions free tier: 2,000 minutes/month)
- ✅ No need to keep your computer on

## Monitor Status

Check if it's working:
- Go to **Actions** tab in your GitHub repository
- You'll see green checkmarks ✅ if running successfully
- Click on any run to see logs

## Stop Monitoring

To stop the monitor:
- Go to `.github/workflows/monitor.yml`
- Click "Edit" → Delete the file or disable the workflow
- Or change the cron schedule

## Troubleshooting

### Workflow not running?
- Make sure you've enabled GitHub Actions in repository settings
- Check that all 4 secrets are added correctly

### Not receiving WhatsApp alerts?
- Ensure you've joined the Twilio sandbox (send "join code" to +14155238886)
- Test locally with: `python3 test_whatsapp.py`

### Rate limiting?
- GitHub Actions free tier: 2,000 minutes/month
- Running every minute = ~43,200 minutes/month (paid required)
- **Recommendation**: Change to every 5 minutes in `.github/workflows/monitor.yml`
  ```yaml
  - cron: '*/5 * * * *'  # Every 5 minutes
  ```
