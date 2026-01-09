from bot.kite_client import load_nfo_instruments
from bot.helpers import market_open, sleep_to_next_candle
from bot.strategy import run
from bot.telegram import send_alert
from bot.logger import get_logger

logger = get_logger(__name__)

def main():
    load_nfo_instruments()
    send_alert("Bot started")

    while True:
        if not market_open():
            sleep_to_next_candle()
            continue

        symbol = run()
        if symbol:
            send_alert(f"Signal generated: `{symbol}`")

        sleep_to_next_candle()

if __name__ == "__main__":
    main()
