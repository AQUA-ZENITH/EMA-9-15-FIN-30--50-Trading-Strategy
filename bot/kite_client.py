from kiteconnect import KiteConnect
from bot.config import API_KEY, ACCESS_TOKEN
from bot.logger import get_logger

logger = get_logger(__name__)

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

instrument_map = {}

def load_nfo_instruments():
    global instrument_map
    instruments = kite.instruments("NFO")
    instrument_map = {
        i["tradingsymbol"]: i["instrument_token"]
        for i in instruments
    }
    logger.info("Loaded %d NFO instruments", len(instrument_map))
