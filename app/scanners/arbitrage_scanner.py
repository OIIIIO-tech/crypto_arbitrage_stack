import ccxt
import logging
from app.config import EXCHANGES, TRADING_PAIRS
from app.config_env import get_api_credentials

# Configure logging if not already configured by a higher-level script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scan_for_arbitrage():
    """
    Scans for simple arbitrage opportunities using live ticker data.

    The core logic flaw in many simple scanners is using historical data (like
    the OHLCV data in the database). Real arbitrage requires live bid/ask prices.
    This function fetches live tickers to find opportunities where the highest bid
    price on one exchange is greater than the lowest ask price on another.
    """
    logging.info("Starting arbitrage scan for live ticker data...")

    for symbol in TRADING_PAIRS:
        logging.info(f"--- Scanning for {symbol} ---")

        tickers = {}
        for exchange_name in EXCHANGES:
            try:
                # Initialize exchange configuration
                exchange_config = {
                    'sandbox': False,
                    'enableRateLimit': True
                }
                
                # Add API credentials if available (for potentially better rate limits)
                credentials = get_api_credentials(exchange_name)
                if credentials:
                    exchange_config['apiKey'] = credentials['api_key']
                    exchange_config['secret'] = credentials['api_secret']
                
                exchange = getattr(ccxt, exchange_name)(exchange_config)
                if not exchange.has['fetchTicker']:
                    logging.warning(f"  {exchange_name} does not support fetchTicker. Skipping.")
                    continue

                ticker = exchange.fetch_ticker(symbol)
                # We need both bid (price to sell at) and ask (price to buy at)
                if ticker.get('bid') and ticker.get('ask'):
                    tickers[exchange_name] = {'bid': ticker['bid'], 'ask': ticker['ask']}
                    logging.info(f"  {exchange_name}: Bid: {ticker['bid']}, Ask: {ticker['ask']}")
                else:
                    logging.warning(f"  Ticker for {symbol} on {exchange_name} is missing bid/ask price.")

            except (ccxt.BaseError, AttributeError) as e:
                logging.error(f"  Could not fetch ticker for {symbol} from {exchange_name}: {e}")
                continue

        if len(tickers) < 2:
            logging.warning(f"Need at least two exchanges with valid tickers for {symbol} to find an opportunity. Skipping.")
            continue

        # Find the best (highest) bid and best (lowest) ask across all exchanges
        best_bid_exchange = max(tickers, key=lambda x: tickers[x]['bid'])
        best_ask_exchange = min(tickers, key=lambda x: tickers[x]['ask'])

        best_bid = tickers[best_bid_exchange]['bid']
        best_ask = tickers[best_ask_exchange]['ask']

        # The core arbitrage condition: Can we sell for more than we can buy?
        if best_bid > best_ask:
            profit_percentage = ((best_bid - best_ask) / best_ask) * 100
            print("\n" + "="*40)
            print(f"  !!! ARBITRAGE OPPORTUNITY DETECTED for {symbol} !!!")
            print(f"  Buy on {best_ask_exchange} at ASK price: {best_ask}")
            print(f"  Sell on {best_bid_exchange} at BID price: {best_bid}")
            print(f"  Potential Profit (before fees): {profit_percentage:.4f}%")
            print("="*40 + "\n")
        else:
            logging.info(f"No arbitrage opportunity found for {symbol}. Best Bid: {best_bid} ({best_bid_exchange}), Best Ask: {best_ask} ({best_ask_exchange})")