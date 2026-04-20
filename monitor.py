import os
import time
import logging
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# fanSALE URL for Eurovision 2026 Grand Final
FANSALE_URL = "https://www.fansale.at/fansale/tickets/musik/eurovision-song-contest/"

# How often to check (in seconds)
CHECK_INTERVAL = 60  # every minute

# Keywords to look for in listings (case-insensitive)
KEYWORDS = ["grand final", "finale", "16. mai", "16 mai", "16 may"]

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# --- State ---
last_listings = set()


def send_telegram(message: str):
    """Send a Telegram notification."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram credentials not set — skipping notification.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("Telegram notification sent.")
    except Exception as e:
        log.error(f"Failed to send Telegram message: {e}")


def fetch_listings() -> set:
    """Fetch current ticket listings from fanSALE."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ),
        "Accept-Language": "en-GB,en;q=0.9",
    }
    try:
        resp = requests.get(FANSALE_URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Failed to fetch fanSALE page: {e}")
        return set()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Look for listing items — fanSALE uses <li> or <div> elements with ticket info
    listings = set()
    for tag in soup.find_all(["li", "div", "a"], string=True):
        text = tag.get_text(strip=True).lower()
        if any(kw in text for kw in KEYWORDS):
            listings.add(text[:200])  # store first 200 chars as identifier

    return listings


def check():
    """Check for new listings and notify if found."""
    global last_listings
    log.info(f"Checking fanSALE: {FANSALE_URL}")
    current = fetch_listings()

    if not current:
        log.info("No matching listings found (or page structure changed).")
        # Also notify if the page itself mentions availability keywords
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(FANSALE_URL, headers=headers, timeout=15)
            page_text = resp.text.lower()
            if any(kw in page_text for kw in KEYWORDS):
                new_msg = (
                    "🎟 <b>Eurovision 2026 Grand Final</b>\n\n"
                    "Something matching 'Grand Final' appeared on fanSALE!\n\n"
                    f"👉 <a href='{FANSALE_URL}'>Check fanSALE now</a>"
                )
                send_telegram(new_msg)
        except Exception as e:
            log.error(f"Secondary check failed: {e}")
        return

    new_listings = current - last_listings
    if new_listings:
        log.info(f"🎉 {len(new_listings)} new listing(s) found!")
        message = (
            f"🎟 <b>Eurovision 2026 Grand Final tickets on fanSALE!</b>\n\n"
            f"Found <b>{len(new_listings)}</b> new listing(s):\n\n"
        )
        for item in list(new_listings)[:5]:  # show up to 5
            message += f"• {item[:100]}\n"
        message += f"\n👉 <a href='{FANSALE_URL}'>Check fanSALE now</a>"
        send_telegram(message)
    else:
        log.info("No new listings since last check.")

    last_listings = current


def main():
    log.info("🚀 fanSALE Eurovision ticket monitor started.")
    send_telegram(
        "✅ <b>Eurovision fanSALE monitor is running!</b>\n"
        "You'll be notified here when Grand Final tickets appear.\n\n"
        f"Checking every {CHECK_INTERVAL // 60} minute(s)."
    )
    while True:
        try:
            check()
        except Exception as e:
            log.error(f"Unexpected error during check: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
