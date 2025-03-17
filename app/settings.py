import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database connection
DB_HOST = os.getenv("APP_DATABASE_HOST", "db")
DB_USERNAME = os.getenv("APP_DATABASE_USERNAME")
DB_PASSWORD = os.getenv("APP_DATABASE_PASSWORD")
DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/chainlit"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
