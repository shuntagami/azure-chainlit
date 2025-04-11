import os
from typing import Optional

class Config:
    # Database settings
    DB_HOST: str = os.getenv("APP_DATABASE_HOST", "db")
    DB_USERNAME: str = os.getenv("APP_DATABASE_USERNAME", "postgres")
    DB_PASSWORD: str = os.getenv("APP_DATABASE_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("APP_DATABASE_NAME", "chainlit")
    DATABASE_URL: str = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    ASYNC_DATABASE_URL: str = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2024-02-01")
    OPENAI_ASSISTANT_ID: Optional[str] = os.getenv("OPENAI_ASSISTANT_ID")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    
    # Azure Storage settings
    AZURE_STORAGE_ACCOUNT: str = os.getenv("AZURE_STORAGE_ACCOUNT", "")
    AZURE_STORAGE_KEY: str = os.getenv("AZURE_STORAGE_KEY", "")
    BLOB_CONTAINER_NAME: str = os.getenv("BLOB_CONTAINER_NAME", "chainlit")

    # Auth settings
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "shuntagami23@gmail.com")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "password123")

    # File settings
    SUPPORTED_TEXT_MIME_TYPES = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "application/pdf",
        "text/plain",
    ]

config = Config()