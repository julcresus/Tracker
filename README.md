# Eurovision 2026 fanSALE Ticket Monitor

Monitors fansale.at for Eurovision 2026 Grand Final tickets and sends a Telegram notification when they appear.

---

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** you receive (looks like `123456789:ABCdef...`)
4. Search for **@userinfobot** in Telegram and send `/start` to get your **chat ID**

---

### 2. Deploy to Railway

1. Fork or upload this folder to a new GitHub repository
2. Go to [railway.app](https://railway.app) and sign up (free)
3. Click **New Project → Deploy from GitHub repo**
4. Select your repository
5. Go to **Variables** and add:
   - `TELEGRAM_BOT_TOKEN` → your bot token
   - `TELEGRAM_CHAT_ID` → your chat ID
6. Railway will detect the `Procfile` and start the worker automatically

---

### 3. You're done!

You'll receive a Telegram message confirming the monitor is running.
When Grand Final tickets appear on fanSALE, you'll get an instant notification with a direct link.

---

## Notes

- Checks every **60 seconds**
- Only notifies on **new** listings (won't spam you)
- Sends a confirmation message on startup so you know it's working
- If fanSALE changes their page layout, the script may need updating

## Files

- `monitor.py` — main script
- `requirements.txt` — Python dependencies
- `Procfile` — tells Railway how to run the script
