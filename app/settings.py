import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection
DB_HOST = os.getenv("APP_DATABASE_HOST")
DB_USERNAME = os.getenv("APP_DATABASE_USERNAME")
DB_PASSWORD = os.getenv("APP_DATABASE_PASSWORD")
DB_NAME = os.getenv("APP_DATABASE_NAME")
DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
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
