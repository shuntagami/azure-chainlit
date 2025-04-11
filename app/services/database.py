from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import config

# Initialize database engine and session
engine = create_engine(config.DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Database session dependency for synchronous database operations.
    Yields a database session that is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()