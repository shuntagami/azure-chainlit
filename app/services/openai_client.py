from openai import AsyncAzureOpenAI
from app.config import config

def get_openai_client() -> AsyncAzureOpenAI:
    """
    Creates and returns a configured AsyncAzureOpenAI client.
    
    Returns:
        AsyncAzureOpenAI: Configured OpenAI client for Azure
    """
    return AsyncAzureOpenAI(
        api_key=config.OPENAI_API_KEY,
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        api_version=config.OPENAI_API_VERSION,
    )