import sys
import os

# Add the project root to the Python path to allow running this script directly.
# This ensures that the 'app' module can be found.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import ccxt
import datetime
import logging
from app.database.database import get_session
from app.models.market_data import MarketData, Base
from app.config import EXCHANGES, TRADING_PAIRS, EXCHANGE_TRADING_PAIRS
from app.database.database import engine
from app.config_env import get_api_credentials, has_api_credentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_database():
    """Ensures database and tables are created."""
    logging.info("Setting up database tables if they don't exist...")
    Base.metadata.create_all(engine)
    logging.info("Database setup complete.")

def fetch_market_data():
    """Fetches OHLCV data from exchanges and stores it in the database."""
    with get_session() as session:
        new_market_data_points = []
        for exchange_name in EXCHANGES:
            try:
                # Initialize exchange configuration
                exchange_config = {
                    'sandbox': False,  # Use production endpoints
                    'enableRateLimit': True,  # Enable rate limiting
                }
                
                # Set market type for futures exchanges  
                # Note: We'll handle SHIB as spot during the symbol loop
                
                # Add API credentials if available
                credentials = get_api_credentials(exchange_name)
                if credentials:
                    exchange_config['apiKey'] = credentials['api_key']
                    exchange_config['secret'] = credentials['api_secret']
                    logging.info(f"Using API credentials for {exchange_name}")
                else:
                    logging.info(f"No API credentials found for {exchange_name}, using public endpoints only")

                exchange = getattr(ccxt, exchange_name)(exchange_config)
                if not exchange.has['fetchOHLCV']:
                    logging.warning(f"Exchange '{exchange_name}' does not support fetchOHLCV. Skipping.")
                    continue
            except (ccxt.BaseError, AttributeError) as e:
                logging.error(f"Failed to initialize exchange '{exchange_name}': {e}")
                continue

            # Use exchange-specific trading pairs if available, fallback to global list
            symbols_to_fetch = EXCHANGE_TRADING_PAIRS.get(exchange_name, TRADING_PAIRS)
            for symbol in symbols_to_fetch:
                try:
                    # Set market type for Bybit based on symbol
                    if exchange_name == 'bybit':
                        if symbol == 'SHIB/USDT':
                            exchange.options['defaultType'] = 'spot'  # SHIB is spot
                        else:
                            exchange.options['defaultType'] = 'future'  # Others are futures
                    # Find the timestamp of the last entry to fetch only new data
                    latest_record = session.query(MarketData.timestamp).filter_by(
                        exchange=exchange_name, symbol=symbol
                    ).order_by(MarketData.timestamp.desc()).first()

                    since = None
                    if latest_record:
                        # ccxt uses millisecond timestamps, add 1ms to avoid fetching the same candle
                        since = int(latest_record.timestamp.timestamp() * 1000) + 1
                        logging.info(f"Fetching 1m OHLCV for {symbol} from {exchange_name} since {latest_record.timestamp}...")
                    else:
                        logging.info(f"No existing data. Fetching 1m OHLCV for {symbol} from {exchange_name}...")

                    ohlcv = exchange.fetch_ohlcv(symbol, '1m', since=since)

                    if not ohlcv:
                        logging.warning(f"No OHLCV data returned for {symbol} from {exchange_name}.")
                        continue

                    for c in ohlcv:
                        new_market_data_points.append(MarketData(
                            exchange=exchange_name, symbol=symbol, timestamp=datetime.datetime.fromtimestamp(c[0] / 1000),
                            open=c[1], high=c[2], low=c[3], close=c[4], volume=c[5]
                        ))
                except ccxt.BaseError as e:
                    logging.error(f"Error fetching {symbol} from {exchange_name}: {e}")
        if new_market_data_points:
            session.add_all(new_market_data_points)
            session.commit()
            logging.info(f"Successfully committed {len(new_market_data_points)} new data points to the database.")
        else:
            logging.info("No new market data to commit.")

if __name__ == '__main__':
    # setup_database() # Uncomment to run once during initial setup
    fetch_market_data()