import os
import pytz
from dotenv import load_dotenv

load_dotenv()

# API
API_KEY = os.getenv("KITE_API_KEY")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Market
SYMBOL_SPOT = "NIFTY 50"
TOKEN_SPOT = 256265
TIMEFRAME = "5minute"
EXPIRY_TAG = "26106"
STRIKE_STEP = 50

# Risk
OPTION_SL_PCT = 0.06
RR = 1.2

# Strategy
MIN_DATA_ROWS = 80
EMA_DIVERGENCE_PCT = 0.10
FIB_PROXIMITY_PCT = 0.15
COMPRESSION_THRESHOLD = 0.85
MIN_COMPRESSED_CANDLES = 2

IST = pytz.timezone("Asia/Kolkata")
