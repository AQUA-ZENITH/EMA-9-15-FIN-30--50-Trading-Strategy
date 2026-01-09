import requests
from bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from bot.logger import get_logger

logger = get_logger(__name__)

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error("Telegram error: %s", e)
