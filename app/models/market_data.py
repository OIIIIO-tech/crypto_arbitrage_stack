from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint

Base = declarative_base()

class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True)
    exchange = Column(String)
    symbol = Column(String)
    timestamp = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    __table_args__ = (UniqueConstraint('exchange', 'symbol', 'timestamp', name='_exchange_symbol_timestamp_uc'),)

    def __repr__(self):
        return f'<MarketData(exchange={self.exchange}, symbol={self.symbol}, timestamp={self.timestamp})>'