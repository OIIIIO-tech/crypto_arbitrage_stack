import os

# --- Database Configuration ---
# Build an absolute path to the database file in the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_PATH = f"sqlite:///{os.path.join(project_root, 'market_data.db')}"

# --- Trading Configuration ---
# List of exchanges to use for data fetching, scanning, and backtesting.
# Ensure that ccxt supports these exchanges.
EXCHANGES = ['bybit', 'bitstamp']

# Exchange-specific trading pairs configuration
# Bybit uses perpetual futures contracts, Bitstamp uses spot pairs
EXCHANGE_TRADING_PAIRS = {
    'bybit': [
        'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT',
        'ADA/USDT:USDT', 'DOT/USDT:USDT', 'UNI/USDT:USDT', 'AAVE/USDT:USDT',
        'LINK/USDT:USDT', 'XLM/USDT:USDT', 'SHIB/USDT'
    ],  # Perpetual futures (except SHIB which is spot)
    'bitstamp': [
        'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD',
        'ADA/USD', 'DOT/USD', 'UNI/USD', 'AAVE/USD',
        'LINK/USD', 'XLM/USD', 'SHIB/USD'
    ]  # Spot pairs
}

# Legacy support - all unique trading pairs for backward compatibility
TRADING_PAIRS = [
    # Futures pairs
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT',
    'ADA/USDT:USDT', 'DOT/USDT:USDT', 'UNI/USDT:USDT', 'AAVE/USDT:USDT',
    'LINK/USDT:USDT', 'XLM/USDT:USDT',
    # Spot pairs
    'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD',
    'ADA/USD', 'DOT/USD', 'UNI/USD', 'AAVE/USD',
    'LINK/USD', 'XLM/USD', 'SHIB/USD', 'SHIB/USDT'
]

# --- Fee Configuration ---
# Estimated taker fees for each exchange. These are used by the scanner
# to calculate net profit. Taker fees are used because an arbitrage trade
# needs to execute immediately.
# Futures and spot fees can differ - these are estimates and can vary.
EXCHANGE_FEES = {
    'binance': 0.0004,   # 0.04% (futures taker fee)
    'bybit': 0.0006,     # 0.06% (futures taker fee)
    'bitstamp': 0.0004,   # 0.04%% (spot taker fee)
}
