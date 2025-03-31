import asyncio
from typing import Optional
from pathlib import Path
import os

from openai import AsyncAzureOpenAI
from openai.types.beta.assistants import Assistant

from app.config import config
from app.services.openai_client import get_openai_client

_assistant: Optional[Assistant] = None

async def get_assistant() -> Assistant:
    """
    Retrieves the assistant, initializing it if necessary.
    
    Returns:
        Assistant: The OpenAI Assistant object
    """
    global _assistant
    
    if _assistant is None:
        client = get_openai_client()
        if config.OPENAI_ASSISTANT_ID:
            _assistant = await client.beta.assistants.retrieve(
                assistant_id=config.OPENAI_ASSISTANT_ID
            )
        else:
            # Create a new assistant if ID not provided
            _assistant = await create_assistant()
    
    return _assistant

async def create_assistant() -> Assistant:
    """
    Creates a new OpenAI assistant with data analysis capabilities.
    
    Returns:
        Assistant: The newly created OpenAI Assistant object
    """
    client = get_openai_client()
    
    instructions = """You are an assistant running data analysis on CSV files.

    You will use code interpreter to run the analysis.

    However, instead of rendering the charts as images, you will generate a plotly figure and turn it into json.
    You will create a file for each json that I can download through annotations.
    """

    tools = [{"type": "code_interpreter"}, {"type": "file_search"}]
    
    # Check if sample file exists and upload it
    tesla_file_path = Path("tesla-stock-price.csv")
    file_ids = []
    
    if tesla_file_path.exists():
        file = await client.files.create(
            file=open(tesla_file_path, "rb"), 
            purpose="assistants"
        )
        file_ids.append(file.id)
    
    # Create the assistant
    assistant = await client.beta.assistants.create(
        model="gpt-35-turbo",
        name="Data Analysis Assistant",
        instructions=instructions,
        temperature=0.1,
        tools=tools,
        tool_resources={"code_interpreter": {"file_ids": file_ids}} if file_ids else None,
    )
    
    # Store the assistant ID for future use
    # Note: In a production app, you would save this to a database or environment variable
    print(f"Assistant created with id: {assistant.id}")
    
    return assistant

if __name__ == "__main__":
    # Script to create a new assistant when run directly
    asyncio.run(create_assistant())