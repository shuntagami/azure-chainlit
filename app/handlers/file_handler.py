from typing import List
from pathlib import Path

import chainlit as cl
from chainlit.element import Element

from app.config import config
from app.services.openai_client import get_openai_client

async def upload_files(files: List[Element]) -> List[str]:
    """
    Uploads files to OpenAI for assistant processing.
    
    Args:
        files: List of Chainlit Element objects containing files
        
    Returns:
        List of file IDs from OpenAI
    """
    file_ids = []
    client = get_openai_client()
    
    try:
        for file in files:
            uploaded_file = await client.files.create(
                file=Path(file.path), purpose="assistants"
            )
            file_ids.append(uploaded_file.id)
    except Exception as e:
        await cl.ErrorMessage(content=f"Error uploading files: {str(e)}").send()
        
    return file_ids

async def process_files(files: List[Element]) -> List[dict]:
    """
    Processes files for OpenAI assistant, determining appropriate tools for each file type.
    
    Args:
        files: List of Chainlit Element objects containing files
        
    Returns:
        List of file attachments with configured tools for the OpenAI API
    """
    # Return empty list if no files
    if not files:
        return []
    
    # Upload files and get file_ids
    file_ids = await upload_files(files)
    
    # Create attachments with appropriate tools based on file type
    attachments = []
    for file_id, file in zip(file_ids, files):
        # Determine tools based on file type
        tools = [{"type": "code_interpreter"}]
        
        # Add file_search for text-based files
        if file.mime in config.SUPPORTED_TEXT_MIME_TYPES:
            tools.append({"type": "file_search"})
            
        attachments.append({
            "file_id": file_id,
            "tools": tools
        })
    
    return attachments