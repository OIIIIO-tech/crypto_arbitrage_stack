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
# Single scan
python main.py scan

# Continuous scanning (runs until stopped with Ctrl+C)
python main.py scan-continuous

# Continuous scanning with custom interval (default: 15 seconds)
python main.py scan-continuous --interval 30
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

The application supports the following cryptocurrencies:
- BTC (Bitcoin)
- ETH (Ethereum)
- SOL (Solana)
- XRP (Ripple)
- ADA (Cardano)
- DOT (Polkadot)
- UNI (Uniswap)
- AAVE (Aave)
- LINK (Chainlink)
- XLM (Stellar)
- SHIB (Shiba Inu)

Supported exchanges:
- Bybit (perpetual futures)
- Bitstamp (spot pairs)

Trading fees for each exchange can be configured in `app/config.py`. The scanner uses these fees to calculate net profit.

## Output Files

The scanner generates two types of output files:

### 1. Arbitrage Opportunities (`arbitrage_opportunities.jsonl`)
JSON Lines format file containing all profitable opportunities found:
```json
{
  "timestamp": "2025-07-05T11:19:29.123456",
  "base_currency": "BTC",
  "buy_exchange": "bitstamp",
  "sell_exchange": "binance",
  "net_profit_usd": 3.95,
  "net_profit_percent": 0.395
}
```

### 2. Scanner Output Log (`scanner_output.log`)
Complete log of all scanner activity in continuous mode, including:
- Scan results and timestamps
- Opportunity details
- Market spreads and prices
- Session start/stop times

## Features in Detail

### Market Data Feed
- Fetches 1-minute OHLCV data
- Incremental updates to avoid duplicate data
- Automatic error handling and retry logic

### Arbitrage Scanner
- Real-time price comparison across exchanges
- Single scan and continuous monitoring modes
- Comprehensive net profit simulation with actual dollar amounts
- Automatic saving of profitable opportunities to `arbitrage_opportunities.jsonl`
- Complete output logging to `scanner_output.log` in continuous mode
- Cross-market arbitrage detection (futures vs spot)
- Identifies buy/sell opportunities with detailed trade breakdowns

### Backtesting
- Uses Backtrader framework
- Tests arbitrage strategies on historical data
- Generates performance reports and plots

## License

This project is for educational purposes only. Please ensure compliance with exchange terms of service and local regulations when trading cryptocurrencies.
