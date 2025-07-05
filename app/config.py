import os

# --- Database Configuration ---
# Build an absolute path to the database file in the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_PATH = f"sqlite:///{os.path.join(project_root, 'market_data.db')}"

# --- Trading Configuration ---
# List of exchanges to use for data fetching, scanning, and backtesting.
# Ensure that ccxt supports these exchanges.
EXCHANGES = ['binance', 'bybit', 'bitstamp']

# Exchange-specific trading pairs configuration
# Binance and Bybit use perpetual futures contracts, Bitstamp uses spot pairs
EXCHANGE_TRADING_PAIRS = {
    'binance': ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT'],  # Perpetual futures
    'bybit': ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT'],    # Perpetual futures
    'bitstamp': ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD']  # Spot pairs
}

# Legacy support - all unique trading pairs for backward compatibility
TRADING_PAIRS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT',  # Futures
    'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD'  # Spot
]

# --- Fee Configuration ---
# Estimated taker fees for each exchange. These are used by the scanner
# to calculate net profit. Taker fees are used because an arbitrage trade
# needs to execute immediately.
# Futures and spot fees can differ - these are estimates and can vary.
EXCHANGE_FEES = {
    'binance': 0.0004,   # 0.04% (futures taker fee)
    'bybit': 0.0006,     # 0.06% (futures taker fee)
    'bitstamp': 0.004,   # 0.4% (spot taker fee)
}
