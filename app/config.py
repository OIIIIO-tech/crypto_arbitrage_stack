import os

# --- Database Configuration ---
# Build an absolute path to the database file in the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_PATH = f"sqlite:///{os.path.join(project_root, 'market_data.db')}"

# --- Trading Configuration ---
# List of exchanges to use for data fetching, scanning, and backtesting.
# Ensure that ccxt supports these exchanges.
EXCHANGES = ['binance', 'bybit', 'bitstamp']

# List of trading pairs to monitor.
# Ensure these pairs are available on all configured exchanges.
TRADING_PAIRS = ['BTC/USDT', 'ETH/USDT']