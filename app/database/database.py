from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_PATH

engine = create_engine(DATABASE_PATH)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()