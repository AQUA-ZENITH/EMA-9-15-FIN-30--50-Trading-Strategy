# EMA-9-15-FIN-30--50-Trading-Strategy

A modular, rule-based options trading bot built using the Zerodha Kite Connect API. The bot scans NIFTY spot data on a 5-minute timeframe and sends option trade alerts via Telegram based on EMA structure, volatility compression, and Fibonacci levels.

> **DISCLAIMER:** This project is for **educational and research purposes only**. It does **NOT** place trades automatically. Always verify signals manually before trading. The author is not responsible for any financial losses.

INSTALLATION
----------------------------------------------------------------

1. Clone the repository
<pre>
   git clone https://github.com/your-username/option-bot.git
   cd option-bot
</pre>
2. Create and activate a virtual environment
<pre>
   python -m venv venv
   source venv/bin/activate
   (Windows: venv\Scripts\activate)
</pre>
3. Install dependencies
<pre>
   pip install -r requirements.txt
</pre>

ENVIRONMENT SETUP
----------------------------------------------------------------

Create a .env file in the project root.

Example (.env):
<pre>
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
</pre>
IMPORTANT:
- Do NOT commit .env to GitHub
- Access tokens expire daily


ACCESS TOKEN GENERATOR (DAILY REQUIRED)
----------------------------------------------------------------

Zerodha access tokens expire every trading day.
You MUST generate a new token before running the bot.

**File: tools/generate_access_token.py**

Run Command:
<pre>
python tools/generate_access_token.py
</pre>

----------------------------------------------------------------
INSTRUMENT TOKEN FINDER (STOCKS / F&O)
----------------------------------------------------------------

This Streamlit tool helps you find:
- Stock instrument tokens
- Index tokens
- Futures and Options tokens
- Lot sizes and contract details

**File: tools/instrument_finder.py**

Run Command:
<pre>
streamlit run tools/instrument_finder.py
</pre>

----------------------------------------------------------------
DAILY BOT RUN PROCEDURE
----------------------------------------------------------------

EVERY TRADING DAY:

1. Generate a new access token
<pre>
   python tools/generate_access_token.py
</pre>

   Update the .env file with the new token.

2. (Optional) Verify instrument tokens
<pre>
   streamlit run tools/instrument_finder.py
</pre>

   - Confirm NIFTY spot token
   - Check option expiry symbols

3. Start the bot
<pre>
   python main.py
</pre>

----------------------------------------------------------------
BOT BEHAVIOR
----------------------------------------------------------------

- Waits for market open (09:15 IST)
- Syncs with 5-minute candle closes
- Scans NIFTY spot
- Evaluates:
  - EMA divergence
  - Volatility compression
  - Fibonacci proximity
- Sends Telegram alerts for CE / PE signals
- Stops automatically after market close


----------------------------------------------------------------
IMPORTANT NOTES
----------------------------------------------------------------

- The bot does NOT place trades
- Zerodha API rate limits apply
- Access tokens expire daily
- Run only one instance at a time
- Always cross-check signals manually


----------------------------------------------------------------
FUTURE ENHANCEMENTS
----------------------------------------------------------------

- Paper trading mode
- Daily CSV logging
- Order execution module

----------------------------------------------------------------
LICENSE
----------------------------------------------------------------

MIT License

Use responsibly. Trade carefully.

