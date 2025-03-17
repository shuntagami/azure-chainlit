import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, Integer, ForeignKey, ARRAY, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database connection
DB_HOST = os.getenv("APP_DATABASE_HOST", "db")
DB_USERNAME = os.getenv("APP_DATABASE_USERNAME", "postgres")
DB_PASSWORD = os.getenv("APP_DATABASE_PASSWORD", "postgres")
DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/chainlit"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
