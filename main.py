import logging
import time
import requests
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta, time as dt_time
from kiteconnect import KiteConnect

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# 🔴 SECURITY: Replace with your NEW keys (Do not share these!)
API_KEY = "lmp4evau4gt3bxyu"
API_SECRET = "ptec3upsinlzyi9lbuzdqonfonoo2s84"
ACCESS_TOKEN = "x7uAU1Fq4rf3XSJBaWGqFFHLz4BMInJ9"

TELEGRAM_BOT_TOKEN = "7954759891:AAHLAnvDjGuZKDYo3Jkd-pvXW3oi3Cr3MVQ"
TELEGRAM_CHAT_ID = "6419533879"

# 🟢 INSTRUMENT SETTINGS
# Note: For Spot charts, Zerodha usually uses "NIFTY 50" (without NSE: prefix in historical API)
SYMBOL_SPOT = "NIFTY 50"
TOKEN_SPOT = 256265  # Token for Nifty 50 Spot
TIMEFRAME = "5minute"

# 🗓️ OPTION SETTINGS
# Example: "24JAN" for Monthly, or "24125" for Weekly (Year-Month-Day)
# Check your Kite watch list for the exact format.
EXPIRY_TAG = "26106"
STRIKE_STEP = 50

# 🛡️ RISK SETTINGS
OPTION_SL_PCT = 0.06  # 6% Stop Loss
RR = 1.2              # 1:1.2 Risk Reward

# 📊 STRATEGY PARAMETERS
MIN_DATA_ROWS = 80
EMA_DIVERGENCE_PCT = 0.10
FIB_PROXIMITY_PCT = 0.15
COMPRESSION_THRESHOLD = 0.85
MIN_COMPRESSED_CANDLES = 2

# Timezone
IST = pytz.timezone('Asia/Kolkata')

# ==========================================
# 📡 KITE & SETUP
# ==========================================
kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

instrument_map = {}

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_instruments():
    """Fetches all NFO instruments to map Symbols -> Tokens."""
    logger.info("⏳ Loading NFO instruments...")
    try:
        instruments = kite.instruments("NFO")
        global instrument_map
        instrument_map = {i['tradingsymbol']: i['instrument_token'] for i in instruments}
        logger.info(f"✅ Instruments loaded: {len(instrument_map)} contracts")
    except Exception as e:
        logger.error(f"❌ Failed to load instruments: {e}")
        raise

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"❌ Telegram Failed: {e}")

# ==========================================
# 🧮 HELPER FUNCTIONS
# ==========================================
def check_market_status():
    """Checks if the Indian market is currently open."""
    now = datetime.now(IST)

    # 1. Check Weekend (5=Saturday, 6=Sunday)
    if now.weekday() >= 5:
        return False, "Market Closed (Weekend)"

    # 2. Check Time (09:15 to 15:30)
    current_time = now.time()
    market_open_time = dt_time(9, 15)
    market_close_time = dt_time(15, 30)

    if market_open_time <= current_time <= market_close_time:
        return True, "Market Open"

    if current_time < market_open_time:
        return False, f"Market Closed (Pre-Market: {current_time.strftime('%H:%M')})"

    return False, f"Market Closed (Post-Market: {current_time.strftime('%H:%M')})"

def sleep_until_next_candle():
    """Sleeps exactly until the next 5-minute mark + 2 seconds."""
    now = datetime.now(IST)
    next_minute = (now.minute // 5 + 1) * 5
    next_run = now.replace(minute=0, second=2, microsecond=0) + timedelta(minutes=next_minute)

    if next_minute >= 60: # Handle hour rollover
        next_run = now.replace(hour=now.hour+1, minute=0, second=2, microsecond=0) if now.hour < 23 else now + timedelta(minutes=5)

    wait_seconds = (next_run - now).total_seconds()

    if wait_seconds > 0:
        logger.info(f"⏳ Waiting {int(wait_seconds)}s for candle close ({next_run.strftime('%H:%M:%S')})...")
        time.sleep(wait_seconds)

def get_atm_strike(spot_price):
    return round(spot_price / STRIKE_STEP) * STRIKE_STEP

def get_option_ltp(tradingsymbol):
    try:
        if tradingsymbol not in instrument_map:
            logger.warning(f"⚠️ Symbol {tradingsymbol} not found in NFO map.")
            return 0.0

        quote_symbol = f"NFO:{tradingsymbol}"
        quote = kite.quote(quote_symbol)

        if quote_symbol in quote:
            return quote[quote_symbol]['last_price']
        return 0.0
    except Exception as e:
        logger.error(f"❌ Error fetching LTP for {tradingsymbol}: {e}")
        return 0.0

def calculate_indicators(df):
    """Calculates EMA, Swing High/Low, Fibs, and Compression."""
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema15'] = df['close'].ewm(span=15, adjust=False).mean()

    df['swing_high'] = df['high'].rolling(window=15, min_periods=15).max()
    df['swing_low'] = df['low'].rolling(window=15, min_periods=15).min()

    swing_range = df['swing_high'] - df['swing_low']
    swing_range = swing_range.replace(0, np.nan)

    df['fib30'] = df['swing_low'] + 0.3 * swing_range
    df['fib50'] = df['swing_low'] + 0.5 * swing_range
    df['fib70'] = df['swing_low'] + 0.7 * swing_range

    df['range'] = df['high'] - df['low']
    df['avg_range'] = df['range'].rolling(window=8, min_periods=8).mean()
    df['compression'] = df['range'] < (df['avg_range'] * COMPRESSION_THRESHOLD)

    return df

def get_score(row, curr_price):
    """Calculates setup quality score (0-3)."""
    score = 0

    # 1. EMA Divergence
    if curr_price > 0:
        ema_diff_pct = abs(row['ema9'] - row['ema15']) / curr_price * 100
        if ema_diff_pct > EMA_DIVERGENCE_PCT:
            score += 1

    # 2. Compression
    if row['compression']:
        score += 1

    # 3. Fibonacci Proximity
    swing_len = row['swing_high'] - row['swing_low']
    if swing_len > 0 and not pd.isna(swing_len):
        fib_tolerance = swing_len * FIB_PROXIMITY_PCT
        if abs(curr_price - row['fib30']) < fib_tolerance or abs(curr_price - row['fib50']) < fib_tolerance:
            score += 1

    return score

def check_candle_strength(row):
    """Checks if candle body is strong compared to wicks."""
    body = abs(row['close'] - row['open'])
    upper_wick = row['high'] - max(row['open'], row['close'])
    lower_wick = min(row['open'], row['close']) - row['low']
    total_wicks = upper_wick + lower_wick

    if body < 5: # Doji
        candle_range = row['high'] - row['low']
        return candle_range > 0 and total_wicks < (candle_range * 0.7)

    return total_wicks <= (body * 1.2)

# ==========================================
# 🚀 STRATEGY ENGINE
# ==========================================
def run_strategy():
    logger.info(f"🔎 Scanning {SYMBOL_SPOT}...")

    # Fetch Data (5 days to ensure EMA calculation is accurate)
    to_date = datetime.now(IST)
    from_date = to_date - timedelta(days=5)

    try:
        data = kite.historical_data(TOKEN_SPOT, from_date, to_date, TIMEFRAME)
        df = pd.DataFrame(data)
    except Exception as e:
        logger.error(f"❌ API Error fetching historical data: {e}")
        return

    if df.empty or len(df) < MIN_DATA_ROWS:
        logger.warning("⚠️ Insufficient data from API")
        return

    # Process Indicators
    df = calculate_indicators(df)

    # 🔥 CRITICAL: Analyze the LAST COMPLETED candle (iloc[-2])
    # iloc[-1] is the currently forming candle (which changes/repaints)
    curr = df.iloc[-2]
    prev_day = df.iloc[-80] # Approx prev day for gap check

    candle_time = curr['date'].astimezone(IST)
    timestamp_str = candle_time.strftime('%Y-%m-%d %H:%M')

    # Time Check (Strict trading hours)
    curr_time = candle_time.time()
    if not (dt_time(9, 15) <= curr_time <= dt_time(15, 30)):
        logger.info(f"[{timestamp_str}] 💤 Outside trading window")
        return

    # Gap Check (> 1% Gap is risky)
    gap_pct = abs(curr['open'] - prev_day['close']) / prev_day['close'] * 100
    if gap_pct > 1.0:
        logger.info(f"[{timestamp_str}] ❌ Gap too large: {gap_pct:.2f}%")
        return

    # Score Check
    score = get_score(curr, curr['close'])
    if score < 2:
        logger.info(f"[{timestamp_str}] ❌ Score low: {score}/3")
        return

    # Compression Check (Look back 5 candles excluding current)
    recent_compression = df['compression'].iloc[-7:-2].sum()
    if recent_compression < MIN_COMPRESSED_CANDLES:
        logger.info(f"[{timestamp_str}] ❌ Low compression")
        return

    if not check_candle_strength(curr):
        logger.info(f"[{timestamp_str}] ❌ Weak candle")
        return

    # Directional Checks
    signals_found = []
    atm_strike = get_atm_strike(curr['close'])

    # LONG Trigger (Price above Fib 30 support + EMA bullish)
    if (curr['close'] > curr['open'] and
        curr['ema9'] > curr['ema15'] and
        curr['close'] >= curr['fib30']):

        ce_symbol = f"NIFTY{EXPIRY_TAG}{atm_strike}CE"
        signals_found.append({"type": "CALL (CE)", "symbol": ce_symbol, "direction": "BULLISH"})

    # SHORT Trigger (Price below Fib 70 resistance + EMA bearish)
    if (curr['open'] > curr['close'] and
        curr['ema9'] < curr['ema15'] and
        curr['close'] <= curr['fib70']):

        pe_symbol = f"NIFTY{EXPIRY_TAG}{atm_strike}PE"
        signals_found.append({"type": "PUT (PE)", "symbol": pe_symbol, "direction": "BEARISH"})

    if not signals_found:
        return

    # Send Alerts
    for sig in signals_found:
        ltp = get_option_ltp(sig['symbol'])

        if ltp > 0:
            sl_price = ltp * (1 - OPTION_SL_PCT)
            target_price = ltp * (1 + (OPTION_SL_PCT * RR))

            msg = (
                f"🚨 *OPTION BUY ALERT*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Direction: *{sig['direction']}*\n"
                f"Symbol: `{sig['symbol']}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 *Entry:* ₹{ltp:.2f}\n"
                f"🛑 *SL:* ₹{sl_price:.2f} (-6%)\n"
                f"🎯 *TGT:* ₹{target_price:.2f}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Spot: {curr['close']:.2f}\n"
                f"⚡ Score: {score}/3\n"
                f"🕒 Time: {timestamp_str}"
            )
            logger.info(f"🚀 SIGNAL: {sig['type']} @ ₹{ltp:.2f}")
            send_telegram_alert(msg)
        else:
            logger.warning(f"⚠️ Signal generated but LTP is 0 for {sig['symbol']}. Check Expiry Tag.")

# ==========================================
# 🏁 MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    try:
        logger.info("🤖 Initializing Option Trading Bot...")
        load_instruments()

        # --- 🛑 MARKET STATUS CHECK ---
        is_open, status_msg = check_market_status()

        if not is_open:
            logger.warning(f"🛑 {status_msg}")
            send_telegram_alert(f"🛑 *Bot Paused*: {status_msg}\n⏳ Waiting for market to open...")

            # Smart Wait Loop (Sleeps until Market Opens)
            while not is_open:
                time.sleep(60)  # Check every 1 minute
                is_open, status_msg = check_market_status()
                if datetime.now(IST).minute == 0: # Log every hour
                     logger.info(f"💤 Bot waiting... ({status_msg})")

            send_telegram_alert("🔔 *Market is OPEN!* 🚀 Bot starting scans now...")
        else:
            send_telegram_alert(f"🤖 *Option Bot Started* \n✅ {status_msg}")

        # --- 🚀 ENTER STRATEGY LOOP ---
        while True:
            # Sync with next candle close (e.g., waits for 10:05:02)
            sleep_until_next_candle()

            # Double check market didn't close while running
            is_open, _ = check_market_status()
            if not is_open:
                logger.info("🛑 Market closed during session. Stopping bot.")
                send_telegram_alert("🛑 Market Closed. Bot stopping for the day.")
                break

            try:
                run_strategy()
            except Exception as e:
                logger.error(f"❌ Strategy Error: {e}", exc_info=True)
                send_telegram_alert(f"⚠️ Strategy Error: {str(e)[:50]}")

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        send_telegram_alert("🛑 Bot stopped manually")
    except Exception as e:
        logger.critical(f"💥 Fatal error: {e}", exc_info=True)
        send_telegram_alert(f"💥 Bot Crashed: {str(e)[:100]}")