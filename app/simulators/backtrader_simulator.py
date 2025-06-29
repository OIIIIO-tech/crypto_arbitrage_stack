import backtrader as bt
import pandas as pd
import logging
from app.database.database import get_session
from app.models.market_data import MarketData
from app.config import EXCHANGES, TRADING_PAIRS

# --- 1. The Arbitrage Strategy ---
class ArbitrageStrategy(bt.Strategy):
    params = (
        # Minimum profit percentage required to enter a trade, after fees
        ('profit_target', 0.002), # 0.2%
        # How many bars to wait before exiting if prices don't converge
        ('exit_after_bars', 10),
    )

    def __init__(self):
        # Keep a dictionary of close prices for each data feed, keyed by the data feed's name
        self.prices = {d._name: d.close for d in self.datas}
        
        # Order tracking
        self.buy_order = None
        self.sell_order = None

        # State for the open arbitrage position
        self.long_on_exchange = None
        self.short_on_exchange = None

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")} - {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # An order has been submitted/accepted - nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED on {order.data._name} at {order.executed.price:.2f}')
                self.buy_order = None
            elif order.issell():
                self.log(f'SELL EXECUTED on {order.data._name} at {order.executed.price:.2f}')
                self.sell_order = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.getstatusname()}')
            # Reset the relevant order reference
            if order.isbuy(): self.buy_order = None
            else: self.sell_order = None

    def next(self):
        # If an order is pending, do not send another
        if self.buy_order or self.sell_order:
            return

        # Check if we are already in a position on any exchange
        in_position = any(self.getposition(data=d).size for d in self.datas)

        if not in_position:
            # Find the best ask (lowest price to buy) and best bid (highest price to sell)
            ask_exchange = min(self.prices, key=self.prices.get)
            bid_exchange = max(self.prices, key=self.prices.get)

            ask_price = self.prices[ask_exchange][0]
            bid_price = self.prices[bid_exchange][0]

            # Arbitrage condition: can we sell for more than we buy, considering the profit target?
            if bid_price > ask_price * (1 + self.p.profit_target):
                self.log(f'!!! ARBITRAGE DETECTED !!!')
                self.log(f'BUY on {ask_exchange} @ {ask_price:.2f}')
                self.log(f'SELL on {bid_exchange} @ {bid_price:.2f}')

                # Place BUY order on the cheaper exchange
                self.buy_order = self.buy(data=self.getdatabyname(ask_exchange))
                # Place SELL order on the more expensive exchange
                self.sell_order = self.sell(data=self.getdatabyname(bid_exchange))

                # Record our position state
                self.long_on_exchange = ask_exchange
                self.short_on_exchange = bid_exchange
                self.entry_bar = len(self)
        else:
            # --- ADVANCED CLOSING LOGIC ---
            # We are in a position, so we check for exit conditions.
            price_on_long_leg = self.prices[self.long_on_exchange][0]
            price_on_short_leg = self.prices[self.short_on_exchange][0]

            # 1. Price Convergence Exit: Close when the spread disappears or reverses
            if price_on_long_leg >= price_on_short_leg:
                self.log(f'Price convergence detected. Closing positions.')
                self.close(data=self.getdatabyname(self.long_on_exchange))
                self.close(data=self.getdatabyname(self.short_on_exchange))
            # 2. Time-Based Exit: Close if the position has been open for too long
            elif len(self) >= self.entry_bar + self.p.exit_after_bars:
                self.log(f'Time-based exit after {self.p.exit_after_bars} bars. Closing positions.')
                self.close(data=self.getdatabyname(self.long_on_exchange))
                self.close(data=self.getdatabyname(self.short_on_exchange))

# --- 2. The Backtest Runner ---
def run_backtest(plot=False):
    cerebro = bt.Cerebro()

    # --- Configure Broker ---
    cerebro.broker.setcash(100000.0)
    # Add a realistic commission (e.g., 0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)

    # --- Load and Synchronize Data ---
    session = get_session()
    symbol_to_test = TRADING_PAIRS[0] # Test the first pair in the config
    logging.info(f"Loading data for {symbol_to_test} from all exchanges...")

    all_data_df = {}
    for exchange in EXCHANGES:
        query = session.query(MarketData).filter(MarketData.exchange == exchange, MarketData.symbol == symbol_to_test).statement
        df = pd.read_sql(query, session.bind, index_col='timestamp', parse_dates=['timestamp'])
        if not df.empty:
            all_data_df[exchange] = df['close'] # We only need the close price
            logging.info(f"Loaded {len(df)} data points for {exchange}")

    if len(all_data_df) < 2:
        logging.error("Need data from at least two exchanges to run an arbitrage backtest. Aborting.")
        return

    # Combine all data into a single DataFrame, aligning them by timestamp
    combined_df = pd.concat(all_data_df, axis=1)
    combined_df.dropna(inplace=True) # Drop rows where any exchange is missing data
    logging.info(f"Combined data has {len(combined_df)} synchronized data points.")

    # --- Add Data Feeds to Cerebro ---
    for exchange_name in combined_df.columns:
        # Backtrader needs a DataFrame with specific column names
        feed_df = pd.DataFrame({'open': combined_df[exchange_name], 'high': combined_df[exchange_name], 'low': combined_df[exchange_name], 'close': combined_df[exchange_name], 'volume': 0})
        data_feed = bt.feeds.PandasData(dataname=feed_df, name=exchange_name)
        cerebro.adddata(data_feed)

    # --- Add Strategy and Run ---
    cerebro.addstrategy(ArbitrageStrategy)
    initial_portfolio_value = cerebro.broker.getvalue()
    print("Running backtest...")
    cerebro.run()
    final_portfolio_value = cerebro.broker.getvalue()
    
    print("\n" + "="*40 + "\nBACKTEST RESULTS\n" + "="*40)
    print(f"Initial Portfolio Value: {initial_portfolio_value:,.2f}")
    print(f"Final Portfolio Value:   {final_portfolio_value:,.2f}")
    pnl = final_portfolio_value - initial_portfolio_value
    print(f"Profit/Loss:             {pnl:,.2f}")
    print("="*40)

    if plot:
        print("\nGenerating plot... (Close the plot window to exit)")
        # Use a style that works well with multiple data feeds
        cerebro.plot(style='line', iplot=False)

if __name__ == '__main__':
    run_backtest()