from app.database.database import get_session
from app.models.market_data import MarketData

def view_market_data():
    """Queries and displays the content of the market_data table."""
    print("Querying database for market data...")
    with get_session() as session:
        # Query all data from the market_data table, ordered for readability
        data = session.query(MarketData).order_by(MarketData.exchange, MarketData.symbol, MarketData.timestamp).all()

        if not data:
            print("\n>>> The 'market_data' table is empty.")
            return

        # For better readability, use pandas to display the data in a table
        try:
            import pandas as pd
            df = pd.DataFrame([{
                'id': d.id, 'exchange': d.exchange, 'symbol': d.symbol,
                'timestamp': d.timestamp, 'open': d.open, 'high': d.high,
                'low': d.low, 'close': d.close, 'volume': d.volume
            } for d in data])
            print(f"\nFound {len(df)} records in 'market_data' table:")
            # Use to_string() to ensure all rows and columns are printed
            print(df.to_string())
        except ImportError:
            print("\nPandas library not found. Printing raw data instead:")
            for row in data:
                print(row)