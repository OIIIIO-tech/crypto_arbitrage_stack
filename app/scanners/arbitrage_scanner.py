import asyncio
import ccxt.async_support as ccxt  # Use the async version of ccxt
import logging
from app.config import EXCHANGES, TRADING_PAIRS, EXCHANGE_FEES
from app.config_env import get_api_credentials

# Configure logging if not already configured by a higher-level script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def fetch_ticker_for_exchange(exchange_name, symbol):
    """
    Asynchronously fetches ticker data for a given symbol from a single exchange.
    Returns a tuple of (exchange_name, ticker_data) or logs an error and returns None.
    """
    exchange = None
    try:
        # Initialize exchange configuration
        exchange_config = {
            'sandbox': False,
            'enableRateLimit': True,
            'newUpdates': False  # Recommended for fetch_ticker in async mode
        }
        
        # Add API credentials if available
        credentials = get_api_credentials(exchange_name)
        if credentials:
            exchange_config['apiKey'] = credentials['api_key']
            exchange_config['secret'] = credentials['api_secret']
        
        exchange = getattr(ccxt, exchange_name)(exchange_config)
        if not exchange.has.get('fetchTicker'):
            logging.warning(f"  {exchange_name} does not support fetchTicker. Skipping.")
            return None

        ticker = await exchange.fetch_ticker(symbol)
        
        if ticker.get('bid') and ticker.get('ask'):
            # Successfully fetched a valid ticker
            return exchange_name, {'bid': ticker['bid'], 'ask': ticker['ask']}
        else:
            logging.warning(f"  Ticker for {symbol} on {exchange_name} is missing bid/ask price.")
            return None

    except (ccxt.BaseError, AttributeError) as e:
        logging.error(f"  Could not fetch ticker for {symbol} from {exchange_name}: {e}")
        return None
    finally:
        if exchange:
            await exchange.close()  # Always close the connection to release resources


async def scan_for_arbitrage():
    """
    Scans for simple arbitrage opportunities by fetching live ticker data concurrently.
    """
    logging.info("Starting asynchronous arbitrage scan for live ticker data...")

    for symbol in TRADING_PAIRS:
        logging.info(f"--- Scanning for {symbol} ---")

        # Create a list of tasks to fetch tickers from all exchanges concurrently
        tasks = [fetch_ticker_for_exchange(exchange_name, symbol) for exchange_name in EXCHANGES]
        
        # Run all tasks and gather results
        results = await asyncio.gather(*tasks)

        # Filter out failed requests and build the tickers dictionary
        tickers = {exchange: data for exchange, data in results if exchange and data}
        for exchange_name, data in tickers.items():
            logging.info(f"  {exchange_name}: Bid: {data['bid']}, Ask: {data['ask']}")

        if len(tickers) < 2:
            logging.warning(f"Need at least two exchanges with valid tickers for {symbol} to find an opportunity. Skipping.")
            continue

        # Find the best (highest) bid and best (lowest) ask across all exchanges
        best_bid_exchange = max(tickers, key=lambda x: tickers[x]['bid'])
        best_ask_exchange = min(tickers, key=lambda x: tickers[x]['ask'])
        best_bid = tickers[best_bid_exchange]['bid']
        best_ask = tickers[best_ask_exchange]['ask']

        # --- Fee-Adjusted Profit Calculation ---
        # Get the taker fee for both exchanges, default to 0.0 if not in config
        buy_fee = EXCHANGE_FEES.get(best_ask_exchange, 0.0)
        sell_fee = EXCHANGE_FEES.get(best_bid_exchange, 0.0)

        # The price we actually pay to acquire the asset, including fees
        effective_buy_price = best_ask * (1 + buy_fee)
        # The revenue we actually receive after selling, minus fees
        effective_sell_price = best_bid * (1 - sell_fee)

        # The new arbitrage condition: Is there profit after fees?
        if effective_sell_price > effective_buy_price:
            gross_profit_percentage = ((best_bid - best_ask) / best_ask) * 100
            net_profit_percentage = ((effective_sell_price - effective_buy_price) / effective_buy_price) * 100
            print("\n" + "="*50)
            print(f"  !!! ARBITRAGE OPPORTUNITY DETECTED for {symbol} !!!")
            print(f"  Buy on  -> {best_ask_exchange.upper():<10} at ASK price: {best_ask}")
            print(f"  Sell on -> {best_bid_exchange.upper():<10} at BID price: {best_bid}")
            print("-" * 50)
            print(f"  Gross Profit (before fees): {gross_profit_percentage:.4f}%")
            print(f"  Net Profit (after fees):    {net_profit_percentage:.4f}%")
            print(f"  (Using fees: Buy {buy_fee*100:.3f}%, Sell {sell_fee*100:.3f}%)")
            print("="*50 + "\n")
        else:
            gross_spread = ((best_bid - best_ask) / best_ask) * 100
            logging.info(f"No profitable arbitrage opportunity found for {symbol} after fees.")
            logging.info(f"  Gross spread was {gross_spread:.4f}%. Best Bid: {best_bid} ({best_bid_exchange}), Best Ask: {best_ask} ({best_ask_exchange})")