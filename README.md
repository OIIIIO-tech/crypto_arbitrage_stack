# Crypto Arbitrage Stack

A comprehensive cryptocurrency arbitrage detection and backtesting system built with Python.

## Features

- **Market Data Fetching**: Real-time data collection from multiple exchanges (Binance, Bybit)
- **Arbitrage Scanning**: Live detection of arbitrage opportunities between exchanges
- **Backtesting**: Historical strategy testing with Backtrader integration
- **Database Storage**: SQLite database for market data persistence
- **Plotting**: Matplotlib integration for visualizing backtest results
- **Automated Scheduling**: Continuous monitoring with configurable intervals

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto_arbitrage_stack
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the database:
```bash
python main.py setup
```

## Usage

### Fetch Market Data
```bash
python main.py feed
```

### Scan for Arbitrage Opportunities
```bash
python main.py scan
```

### Run Backtests
```bash
# Basic backtest
python main.py backtest

# Backtest with plotting
python main.py backtest --plot
```

### View Database Contents
```bash
python main.py view
```

### Automated Scheduling
Run continuous monitoring with automated scheduling:
```bash
python scheduler.py
```

The scheduler runs:
- **Market data fetching**: Every 1 minute
- **Arbitrage scanning**: Every 15 seconds

Press `Ctrl+C` to stop the scheduler.

## Project Structure

```
crypto_arbitrage_stack/
├── app/
│   ├── database/          # Database connection and setup
│   ├── feed/              # Market data fetching
│   ├── models/            # SQLAlchemy models
│   ├── scanners/          # Arbitrage scanning logic
│   ├── simulators/        # Backtesting with Backtrader
│   └── utils/             # Utility functions
├── tests/                 # Unit tests
├── main.py               # Main application entry point
├── scheduler.py          # Automated scheduling for continuous monitoring
└── requirements.txt      # Python dependencies
```

## Dependencies

- **ccxt**: Cryptocurrency exchange integration
- **backtrader**: Backtesting framework
- **pandas**: Data manipulation
- **SQLAlchemy**: Database ORM
- **matplotlib**: Plotting and visualization
- **schedule**: Task scheduling for automated monitoring

## Configuration

The application supports the following trading pairs:
- BTC/USDT
- ETH/USDT

Supported exchanges:
- Binance
- Bybit
- Bitstamp

## Features in Detail

### Market Data Feed
- Fetches 1-minute OHLCV data
- Incremental updates to avoid duplicate data
- Automatic error handling and retry logic

### Arbitrage Scanner
- Real-time price comparison across exchanges
- Calculates potential profit percentages
- Identifies buy/sell opportunities

### Backtesting
- Uses Backtrader framework
- Tests arbitrage strategies on historical data
- Generates performance reports and plots

## License

This project is for educational purposes only. Please ensure compliance with exchange terms of service and local regulations when trading cryptocurrencies.
