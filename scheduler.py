import schedule
import time
import logging
import sys
import os
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.feed.market_data_feed import fetch_market_data
from app.scanners.arbitrage_scanner import scan_for_arbitrage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_feed_job():
    """Wrapper function for the data feed job to add logging and error handling."""
    logging.info("--- SCHEDULER: Running data feed job ---")
    try:
        fetch_market_data()
    except Exception as e:
        logging.error(f"An error occurred in the data feed job: {e}", exc_info=True)
    logging.info("--- SCHEDULER: Data feed job finished ---")

def run_scan_job():
    """Wrapper function for the arbitrage scan job to add logging and error handling."""
    logging.info("--- SCHEDULER: Running arbitrage scan job ---")
    try:
        asyncio.run(scan_for_arbitrage())
    except Exception as e:
        logging.error(f"An error occurred in the arbitrage scan job: {e}", exc_info=True)
    logging.info("--- SCHEDULER: Arbitrage scan job finished ---")


if __name__ == "__main__":
    logging.info("Starting scheduler...")

    # Schedule the data feed to run every minute.
    schedule.every(1).minutes.do(run_feed_job)

    # Schedule the arbitrage scanner to run more frequently (e.g., every 15 seconds).
    schedule.every(15).seconds.do(run_scan_job)

    logging.info("Scheduler started. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)