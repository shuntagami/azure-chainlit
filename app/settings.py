import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
class Config:
    # Database settings
    DB_HOST = os.getenv("APP_DATABASE_HOST")
    DB_USERNAME = os.getenv("APP_DATABASE_USERNAME")
    DB_PASSWORD = os.getenv("APP_DATABASE_PASSWORD")
    DB_NAME = os.getenv("APP_DATABASE_NAME")
    DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

    # Azure Storage settings
    AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT")
    AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")
    BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")

# Initialize database engine and session
engine = create_engine(Config.DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
