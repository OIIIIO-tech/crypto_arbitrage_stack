import asyncio
import ccxt.async_support as ccxt  # Use the async version of ccxt
import logging
import json
import os
import sys
from datetime import datetime
from app.config import EXCHANGES, TRADING_PAIRS, EXCHANGE_FEES, EXCHANGE_TRADING_PAIRS
from app.config_env import get_api_credentials

# Configure logging if not already configured by a higher-level script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File to save profitable opportunities
OPPORTUNITIES_FILE = 'arbitrage_opportunities.jsonl'
# File to save scanner output logs
SCANNER_LOG_FILE = 'scanner_output.log'

# Global variable to track if we're in continuous mode
_log_file_handle = None

def save_opportunity_to_file(opportunity_data):
    """
    Save a profitable arbitrage opportunity to a JSON Lines file.
    """
    try:
        with open(OPPORTUNITIES_FILE, 'a') as f:
            f.write(json.dumps(opportunity_data) + '\n')
    except Exception as e:
        logging.error(f"Failed to save opportunity to file: {e}")

def log_print(*args, **kwargs):
    """
    Custom print function that outputs to both console and log file.
    """
    global _log_file_handle
    
    # Print to console
    print(*args, **kwargs)
    
    # Also write to log file if in continuous mode
    if _log_file_handle:
        try:
            # Convert args to string and write to file with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = ' '.join(str(arg) for arg in args)
            _log_file_handle.write(f"[{timestamp}] {message}\n")
            _log_file_handle.flush()  # Ensure immediate write
        except Exception as e:
            print(f"Warning: Failed to write to log file: {e}")

def start_logging():
    """
    Start logging output to file.
    """
    global _log_file_handle
    try:
        _log_file_handle = open(SCANNER_LOG_FILE, 'a', encoding='utf-8')
        log_print(f"\n{'='*60}")
        log_print(f"Scanner session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_print(f"{'='*60}")
    except Exception as e:
        print(f"Warning: Could not open log file {SCANNER_LOG_FILE}: {e}")
        _log_file_handle = None

def stop_logging():
    """
    Stop logging output to file.
    """
    global _log_file_handle
    if _log_file_handle:
        try:
            log_print(f"\n{'='*60}")
            log_print(f"Scanner session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log_print(f"{'='*60}\n")
            _log_file_handle.close()
            _log_file_handle = None
        except Exception as e:
            print(f"Warning: Error closing log file: {e}")

def clear_screen():
    """
    Clear the terminal screen for better real-time display.
    """
    os.system('clear' if os.name == 'posix' else 'cls')


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
        
        # Set market type based on exchange and symbol
        if exchange_name == 'bybit':
            # Use spot for SHIB, futures for all others
            if symbol == 'SHIB/USDT':
                exchange_config['options'] = {'defaultType': 'spot'}  # Use spot market for SHIB
            else:
                exchange_config['options'] = {'defaultType': 'future'}  # Use futures market for others
        
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
    Scans for arbitrage opportunities by fetching live ticker data concurrently.
    Groups by base currency to compare across different quote currencies (USDT vs USD).
    """
    logging.info("Starting asynchronous arbitrage scan for live ticker data...")

    # Group trading pairs by base currency
    base_currencies = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'UNI', 'AAVE', 'LINK', 'XLM', 'SHIB']
    
    for base_currency in base_currencies:
        logging.info(f"--- Scanning for {base_currency} ---")
        
        # Create tasks to fetch tickers for this base currency from all exchanges
        tasks = []
        for exchange_name in EXCHANGES:
            if exchange_name in EXCHANGE_TRADING_PAIRS:
                # Find the appropriate trading pair for this exchange
                exchange_pairs = EXCHANGE_TRADING_PAIRS[exchange_name]
                matching_pair = next((pair for pair in exchange_pairs if pair.startswith(f"{base_currency}/")), None)
                if matching_pair:
                    tasks.append(fetch_ticker_for_exchange(exchange_name, matching_pair))
        
        # Run all tasks and gather results
        results = await asyncio.gather(*tasks)

        # Filter out failed requests and build the tickers dictionary
        tickers = {}
        for result in results:
            if result and len(result) == 2:
                exchange, data = result
                tickers[exchange] = data
                # Get the trading pair for logging
                exchange_pairs = EXCHANGE_TRADING_PAIRS.get(exchange, [])
                matching_pair = next((pair for pair in exchange_pairs if pair.startswith(f"{base_currency}/")), "Unknown")
                logging.info(f"  {exchange} ({matching_pair}): Bid: {data['bid']}, Ask: {data['ask']}")

        if len(tickers) < 2:
            logging.warning(f"Need at least two exchanges with valid tickers for {base_currency} to find an opportunity. Skipping.")
            continue

        # Find the best (highest) bid and best (lowest) ask across all exchanges
        best_bid_exchange = max(tickers, key=lambda x: tickers[x]['bid'])
        best_ask_exchange = min(tickers, key=lambda x: tickers[x]['ask'])
        best_bid = tickers[best_bid_exchange]['bid']
        best_ask = tickers[best_ask_exchange]['ask']

        # --- Comprehensive Net Profit Simulation ---
        # Simulate a real arbitrage trade with actual dollar amounts
        trade_amount_usd = 10000  # Simulate with $10,000 investment
        
        # Get the taker fee for both exchanges, default to 0.0 if not in config
        buy_fee = EXCHANGE_FEES.get(best_ask_exchange, 0.0)
        sell_fee = EXCHANGE_FEES.get(best_bid_exchange, 0.0)

        # Calculate the actual trade execution
        # 1. Buy on the cheaper exchange (pay ask price + fees)
        effective_buy_price = best_ask * (1 + buy_fee)
        crypto_units_bought = trade_amount_usd / effective_buy_price
        total_buy_cost = crypto_units_bought * effective_buy_price
        buy_fee_amount = crypto_units_bought * best_ask * buy_fee
        
        # 2. Sell on the more expensive exchange (receive bid price - fees)
        gross_sell_revenue = crypto_units_bought * best_bid
        sell_fee_amount = gross_sell_revenue * sell_fee
        net_sell_revenue = gross_sell_revenue - sell_fee_amount
        
        # 3. Calculate net profit
        net_profit_usd = net_sell_revenue - total_buy_cost
        net_profit_percentage = (net_profit_usd / trade_amount_usd) * 100
        
        # 4. Calculate gross spread for comparison
        gross_spread_percentage = ((best_bid - best_ask) / best_ask) * 100

        # Check if arbitrage opportunity exists (positive net profit)
        if net_profit_usd > 0:
            # Get the trading pairs for display
            buy_pair = next((pair for pair in EXCHANGE_TRADING_PAIRS.get(best_ask_exchange, []) if pair.startswith(f"{base_currency}/")), "Unknown")
            sell_pair = next((pair for pair in EXCHANGE_TRADING_PAIRS.get(best_bid_exchange, []) if pair.startswith(f"{base_currency}/")), "Unknown")
            
            print("\n" + "="*70)
            print(f"  !!! ARBITRAGE OPPORTUNITY DETECTED for {base_currency} !!!")
            print("="*70)
            print(f"  TRADE SIMULATION (${trade_amount_usd:,.0f} investment):")
            print("-" * 70)
            print(f"  BUY:  {crypto_units_bought:.6f} {base_currency} on {best_ask_exchange.upper():<10} ({buy_pair})")
            print(f"        Price: ${best_ask:,.2f} + {buy_fee*100:.2f}% fee = ${effective_buy_price:,.2f}")
            print(f"        Cost:  ${total_buy_cost:,.2f} (including ${buy_fee_amount:,.2f} fee)")
            print()
            print(f"  SELL: {crypto_units_bought:.6f} {base_currency} on {best_bid_exchange.upper():<10} ({sell_pair})")
            print(f"        Price: ${best_bid:,.2f} - {sell_fee*100:.2f}% fee = ${best_bid*(1-sell_fee):,.2f}")
            print(f"        Revenue: ${net_sell_revenue:,.2f} (after ${sell_fee_amount:,.2f} fee)")
            print("-" * 70)
            print(f"  PROFIT ANALYSIS:")
            print(f"  Gross Spread:     {gross_spread_percentage:+.4f}%")
            print(f"  Net Profit:       ${net_profit_usd:+.2f} ({net_profit_percentage:+.4f}%)")
            print(f"  Total Fees Paid:  ${buy_fee_amount + sell_fee_amount:.2f}")
            print(f"  Break-even at:    {((buy_fee + sell_fee) * 100):.3f}% spread")
            print("="*70 + "\n")
        else:
            # Calculate how much spread would be needed for profitability
            required_spread = (buy_fee + sell_fee) * 100
            spread_deficit = required_spread - gross_spread_percentage
            
            logging.info(f"No profitable arbitrage opportunity found for {base_currency}.")
            logging.info(f"  Current spread: {gross_spread_percentage:.4f}% | Required: {required_spread:.3f}% | Deficit: {spread_deficit:.3f}%")
            logging.info(f"  Best Bid: ${best_bid:.2f} ({best_bid_exchange}) | Best Ask: ${best_ask:.2f} ({best_ask_exchange})")
            logging.info(f"  Simulated loss: ${net_profit_usd:.2f} on ${trade_amount_usd} investment")

async def scan_continuously(scan_interval=15):
    """
    Run the arbitrage scanner continuously until manually stopped.
    
    Args:
        scan_interval (int): Time in seconds between scans (default: 15)
    """
    scan_count = 0
    opportunities_found = 0
    
    # Start logging to file
    start_logging()
    
    log_print("\n" + "="*80)
    log_print("🚀 CRYPTO ARBITRAGE SCANNER - CONTINUOUS MODE")
    log_print("="*80)
    log_print(f"📊 Monitoring: 11 cryptocurrencies across {len(EXCHANGES)} exchanges")
    log_print(f"💰 Pairs: BTC, ETH, SOL, XRP, ADA, DOT, UNI, AAVE, LINK, XLM, SHIB")
    log_print(f"⏱️  Scan interval: {scan_interval} seconds")
    log_print(f"💾 Saving opportunities to: {OPPORTUNITIES_FILE}")
    log_print(f"📝 Saving output log to: {SCANNER_LOG_FILE}")
    log_print(f"🛑 Press Ctrl+C to stop")
    log_print("="*80 + "\n")
    
    try:
        while True:
            scan_count += 1
            current_time = datetime.now()
            
            # Display scan header
            log_print(f"\n🔍 SCAN #{scan_count} - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            log_print("-" * 60)
            
            # Track opportunities in this scan
            scan_opportunities = 0
            
            # Run the arbitrage scan
            for base_currency in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'UNI', 'AAVE', 'LINK', 'XLM', 'SHIB']:
                # Create tasks to fetch tickers for this base currency from all exchanges
                tasks = []
                for exchange_name in EXCHANGES:
                    if exchange_name in EXCHANGE_TRADING_PAIRS:
                        # Find the appropriate trading pair for this exchange
                        exchange_pairs = EXCHANGE_TRADING_PAIRS[exchange_name]
                        matching_pair = next((pair for pair in exchange_pairs if pair.startswith(f"{base_currency}/")), None)
                        if matching_pair:
                            tasks.append(fetch_ticker_for_exchange(exchange_name, matching_pair))
                
                # Run all tasks and gather results
                results = await asyncio.gather(*tasks)

                # Filter out failed requests and build the tickers dictionary
                tickers = {}
                for result in results:
                    if result and len(result) == 2:
                        exchange, data = result
                        tickers[exchange] = data

                if len(tickers) < 2:
                    log_print(f"⚠️  {base_currency}: Insufficient data (need 2+ exchanges)")
                    continue

                # Find the best (highest) bid and best (lowest) ask across all exchanges
                best_bid_exchange = max(tickers, key=lambda x: tickers[x]['bid'])
                best_ask_exchange = min(tickers, key=lambda x: tickers[x]['ask'])
                best_bid = tickers[best_bid_exchange]['bid']
                best_ask = tickers[best_ask_exchange]['ask']

                # Calculate net profit simulation
                trade_amount_usd = 10000
                buy_fee = EXCHANGE_FEES.get(best_ask_exchange, 0.0)
                sell_fee = EXCHANGE_FEES.get(best_bid_exchange, 0.0)
                
                effective_buy_price = best_ask * (1 + buy_fee)
                crypto_units_bought = trade_amount_usd / effective_buy_price
                total_buy_cost = crypto_units_bought * effective_buy_price
                buy_fee_amount = crypto_units_bought * best_ask * buy_fee
                
                gross_sell_revenue = crypto_units_bought * best_bid
                sell_fee_amount = gross_sell_revenue * sell_fee
                net_sell_revenue = gross_sell_revenue - sell_fee_amount
                
                net_profit_usd = net_sell_revenue - total_buy_cost
                net_profit_percentage = (net_profit_usd / trade_amount_usd) * 100
                gross_spread_percentage = ((best_bid - best_ask) / best_ask) * 100

                if net_profit_usd > 0:
                    # Profitable opportunity found!
                    scan_opportunities += 1
                    opportunities_found += 1
                    
                    buy_pair = next((pair for pair in EXCHANGE_TRADING_PAIRS.get(best_ask_exchange, []) if pair.startswith(f"{base_currency}/")), "Unknown")
                    sell_pair = next((pair for pair in EXCHANGE_TRADING_PAIRS.get(best_bid_exchange, []) if pair.startswith(f"{base_currency}/")), "Unknown")
                    
                    # Create opportunity data for saving
                    opportunity_data = {
                        'timestamp': current_time.isoformat(),
                        'scan_number': scan_count,
                        'base_currency': base_currency,
                        'buy_exchange': best_ask_exchange,
                        'sell_exchange': best_bid_exchange,
                        'buy_pair': buy_pair,
                        'sell_pair': sell_pair,
                        'buy_price': best_ask,
                        'sell_price': best_bid,
                        'buy_fee_percent': buy_fee * 100,
                        'sell_fee_percent': sell_fee * 100,
                        'gross_spread_percent': gross_spread_percentage,
                        'net_profit_usd': net_profit_usd,
                        'net_profit_percent': net_profit_percentage,
                        'trade_amount_usd': trade_amount_usd,
                        'crypto_units': crypto_units_bought,
                        'total_fees_usd': buy_fee_amount + sell_fee_amount
                    }
                    
                    # Save to file
                    save_opportunity_to_file(opportunity_data)
                    
                    # Display opportunity
                    log_print(f"\n💰 OPPORTUNITY #{opportunities_found}: {base_currency}")
                    log_print(f"   Buy:  ${best_ask:,.2f} on {best_ask_exchange.upper()} ({buy_pair})")
                    log_print(f"   Sell: ${best_bid:,.2f} on {best_bid_exchange.upper()} ({sell_pair})")
                    log_print(f"   Profit: ${net_profit_usd:+.2f} ({net_profit_percentage:+.3f}%) on ${trade_amount_usd}")
                    log_print(f"   Spread: {gross_spread_percentage:.3f}% | Fees: ${buy_fee_amount + sell_fee_amount:.2f}")
                else:
                    # No opportunity
                    required_spread = (buy_fee + sell_fee) * 100
                    log_print(f"📊 {base_currency}: ${best_ask:.0f}-${best_bid:.0f} | Spread: {gross_spread_percentage:.3f}% (need {required_spread:.3f}%)")
            
            # Scan summary
            if scan_opportunities > 0:
                log_print(f"\n✅ Found {scan_opportunities} opportunities in this scan!")
            else:
                log_print(f"\n❌ No opportunities found in scan #{scan_count}")
            
            log_print(f"📈 Total opportunities found: {opportunities_found}")
            log_print(f"⏰ Next scan in {scan_interval} seconds...\n")
            
            # Wait for next scan
            await asyncio.sleep(scan_interval)
            
    except KeyboardInterrupt:
        log_print("\n\n🛑 Scanner stopped by user")
        log_print(f"📊 Final Stats:")
        log_print(f"   Total scans: {scan_count}")
        log_print(f"   Opportunities found: {opportunities_found}")
        log_print(f"   Opportunities saved to: {OPPORTUNITIES_FILE}")
        log_print(f"   Output log saved to: {SCANNER_LOG_FILE}")
        log_print("\nThank you for using the Crypto Arbitrage Scanner! 🚀\n")
        
        # Stop logging to file
        stop_logging()
