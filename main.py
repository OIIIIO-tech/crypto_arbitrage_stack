import argparse
import sys
import os

import asyncio
# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.feed.market_data_feed import fetch_market_data, setup_database
from app.scanners.arbitrage_scanner import scan_for_arbitrage, scan_continuously
from app.simulators.backtrader_simulator import run_backtest
from app.utils.view_db import view_market_data

def main():
    parser = argparse.ArgumentParser(description='Crypto Arbitrage Stack')
    parser.add_argument('action', choices=['setup', 'feed', 'scan', 'scan-continuous', 'backtest', 'view'], help='Action to perform')
    parser.add_argument('--plot', action='store_true', help='Generate a plot for the backtest results (used with "backtest" action)')
    parser.add_argument('--interval', type=int, default=15, help='Scan interval in seconds for continuous mode (default: 15)')

    args = parser.parse_args()

    if args.action == 'setup':
        print("Setting up database...")
        setup_database()
        print("Database setup completed successfully.")
    elif args.action == 'feed':
        print("Fetching market data...")
        fetch_market_data()
        print("Market data fetched successfully.")
    elif args.action == 'scan':
        print("Scanning for arbitrage opportunities...")
        asyncio.run(scan_for_arbitrage())
    elif args.action == 'scan-continuous':
        print(f"Starting continuous arbitrage scanning (interval: {args.interval}s)...")
        asyncio.run(scan_continuously(scan_interval=args.interval))
    elif args.action == 'backtest':
        run_backtest(plot=args.plot)
    elif args.action == 'view':
        view_market_data()

if __name__ == '__main__':
    main()