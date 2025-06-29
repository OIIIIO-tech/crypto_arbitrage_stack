import unittest
import datetime
from unittest.mock import patch, MagicMock, ANY

# It's good practice to add the app path for test discovery
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.feed.market_data_feed import fetch_market_data
from app.models.market_data import MarketData

class TestMarketDataFeed(unittest.TestCase):

    # Patch the dependencies: the database session and the ccxt library
    @patch('app.feed.market_data_feed.get_session')
    @patch('app.feed.market_data_feed.ccxt')
    @patch('app.feed.market_data_feed.EXCHANGES', ['test_exchange'])
    @patch('app.feed.market_data_feed.TRADING_PAIRS', ['BTC/USD'])
    def test_fetch_market_data_initial_run(self, mock_ccxt, mock_get_session):
        """
        Test fetching data when the database is empty.
        """
        # --- Arrange ---
        # Mock the database session
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock the ccxt exchange
        mock_exchange_instance = MagicMock()
        mock_exchange_instance.has = {'fetchOHLCV': True}
        # Simulate the API returning two candles
        mock_exchange_instance.fetch_ohlcv.return_value = [
            [1672531200000, 60000, 60100, 59900, 60050, 100], # 2023-01-01 00:00:00
            [1672531260000, 60050, 60150, 59950, 60100, 110], # 2023-01-01 00:01:00
        ]
        mock_ccxt.test_exchange.return_value = mock_exchange_instance

        # --- Act ---
        fetch_market_data()

        # --- Assert ---
        # Verify we tried to connect to the exchange
        mock_ccxt.test_exchange.assert_called_once()
        # Verify we asked for data since the beginning of time (since=None)
        mock_exchange_instance.fetch_ohlcv.assert_called_once_with('BTC/USD', '1m', since=None)
        # Verify that we added 2 new data points to the session
        self.assertEqual(mock_session.add_all.call_count, 1)
        added_data = mock_session.add_all.call_args[0][0]
        self.assertEqual(len(added_data), 2)
        self.assertIsInstance(added_data[0], MarketData)
        self.assertEqual(added_data[0].close, 60050)
        # Verify the transaction was committed
        mock_session.commit.assert_called_once()

    @patch('app.feed.market_data_feed.get_session')
    @patch('app.feed.market_data_feed.ccxt')
    @patch('app.feed.market_data_feed.EXCHANGES', ['test_exchange'])
    @patch('app.feed.market_data_feed.TRADING_PAIRS', ['BTC/USD'])
    def test_fetch_market_data_incremental_update(self, mock_ccxt, mock_get_session):
        """
        Test fetching data incrementally when the database already has some records.
        """
        # --- Arrange ---
        # Mock the database session to return a "latest" record
        mock_session = MagicMock()
        latest_timestamp = datetime.datetime(2023, 1, 1, 0, 1, 0)
        latest_record = MagicMock()
        latest_record.timestamp = latest_timestamp
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = latest_record
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock the ccxt exchange
        mock_exchange_instance = MagicMock()
        mock_exchange_instance.has = {'fetchOHLCV': True}
        # Simulate the API returning only one *new* candle
        mock_exchange_instance.fetch_ohlcv.return_value = [
            [1672531320000, 60100, 60200, 60000, 60150, 120], # 2023-01-01 00:02:00
        ]
        mock_ccxt.test_exchange.return_value = mock_exchange_instance

        # --- Act ---
        fetch_market_data()

        # --- Assert ---
        # Verify we asked for data since the last record's timestamp
        expected_since_timestamp = int(latest_timestamp.timestamp() * 1000) + 1
        mock_exchange_instance.fetch_ohlcv.assert_called_once_with('BTC/USD', '1m', since=expected_since_timestamp)
        # Verify that we only added the 1 new data point
        self.assertEqual(mock_session.add_all.call_count, 1)
        self.assertEqual(len(mock_session.add_all.call_args[0][0]), 1)
        mock_session.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()