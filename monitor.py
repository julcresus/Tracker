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

# ScraperAPI key — sign up free at https://www.scraperapi.com
# Add as SCRAPER_API_KEY environment variable in Railway
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")

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


def fetch_page(url: str) -> str | None:
    """Fetch a page via ScraperAPI if available, otherwise direct."""
    # Try ScraperAPI first (bypasses blocking)
    if SCRAPER_API_KEY:
        scraper_url = (
            f"http://api.scraperapi.com"
            f"?api_key={SCRAPER_API_KEY}"
            f"&url={requests.utils.quote(url, safe='')}"
            f"&render=false"
        )
        try:
            resp = requests.get(scraper_url, timeout=60)
            resp.raise_for_status()
            log.info("Fetched via ScraperAPI successfully.")
            return resp.text
        except Exception as e:
            log.warning(f"ScraperAPI fetch failed: {e}. Falling back to direct.")

    # Direct fetch fallback
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9,de;q=0.8",
        "Connection": "keep-alive",
    }
    for attempt in range(1, 3):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            log.info(f"Fetched directly (attempt {attempt}).")
            return resp.text
        except requests.exceptions.Timeout:
            log.warning(f"Timeout on attempt {attempt}. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            log.error(f"Fetch error on attempt {attempt}: {e}")
            time.sleep(10)

    log.error("All fetch attempts failed.")
    return None


def check():
    """Check for new listings and notify if found."""
    global last_listings
    log.info(f"Checking fanSALE: {FANSALE_URL}")

    html = fetch_page(FANSALE_URL)
    if html is None:
        log.warning("Could not reach fanSALE — will try again next cycle.")
        return

    page_text = html.lower()
    found_keywords = [kw for kw in KEYWORDS if kw in page_text]
    if found_keywords:
        log.info(f"Keywords found in page: {found_keywords}")

    soup = BeautifulSoup(html, "lxml")
    current = set()
    for tag in soup.find_all(["li", "div", "a", "span"]):
        text = tag.get_text(strip=True).lower()
        if len(text) > 5 and any(kw in text for kw in KEYWORDS):
            current.add(text[:200])

    if not current:
        log.info("No matching listings found this cycle.")
        last_listings = current
        return

    new_listings = current - last_listings
    if new_listings:
        log.info(f"🎉 {len(new_listings)} new listing(s) found!")
        message = (
            f"🎟 <b>Eurovision 2026 Grand Final tickets on fanSALE!</b>\n\n"
            f"Found <b>{len(new_listings)}</b> new listing(s):\n\n"
        )
        for item in list(new_listings)[:5]:
            message += f"• {item[:100]}\n"
        message += f"\n👉 <a href='{FANSALE_URL}'>Check fanSALE now</a>"
        send_telegram(message)
    else:
        log.info("No new listings since last check.")

    last_listings = current


def main():
    log.info("🚀 fanSALE Eurovision ticket monitor started.")
    if SCRAPER_API_KEY:
        log.info("ScraperAPI key detected — will use proxy for fetching.")
    else:
        log.warning("No SCRAPER_API_KEY set — fetching directly (may be blocked).")
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
