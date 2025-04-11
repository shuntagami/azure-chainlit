import plotly
from pathlib import Path
from typing import List

import chainlit as cl
import chainlit.data as cl_data
from chainlit.config import config as cl_config
from chainlit.element import Element
from chainlit.context import local_steps

from app.config import config
from app.services import get_openai_client, setup_azure_storage, get_assistant
from app.handlers import EventHandler, process_files, auth_callback

# Initialize OpenAI client
async_openai_client = get_openai_client()

# Set up Azure Blob Storage for Chainlit
setup_azure_storage()

@cl.set_starters
async def set_starters():
    """Define conversation starters for the UI"""
    return [
        cl.Starter(
            label="Run Tesla stock analysis",
            message="Make a data analysis on the tesla-stock-price.csv file I previously uploaded.",
            icon="./public/write.svg",
        ),
        cl.Starter(
            label="Run a data analysis on my CSV",
            message="Make a data analysis on the next CSV file I will upload.",
            icon="./public/write.svg",
        ),
    ]

@cl.on_chat_start
async def start_chat():
    """Initialize the chat session with a new thread"""
    # Get or create the assistant
    assistant = await get_assistant()

    # Create a Thread
    thread = await async_openai_client.beta.threads.create()

    # Store thread ID in user session for later use
    cl.user_session.set("thread_id", thread.id)

@cl.on_stop
async def stop_chat():
    """Handle chat interruption by canceling the active run"""
    current_run_step = cl.user_session.get("run_step")
    if current_run_step:
        try:
            await async_openai_client.beta.threads.runs.cancel(
                thread_id=current_run_step.thread_id,
                run_id=current_run_step.run_id
            )
        except Exception as e:
            await cl.ErrorMessage(content=f"Error canceling run: {str(e)}").send()

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> bool:
    if (
        username in ["shuntagami23@gmail.com"]  # fmt: skip
        and password == "password123"
    ):
        return cl.User(
            identifier=username,
            metadata={"role": "admin", "provider": "credentials"},
        )
    else:
        return False  # Fixed return type issue: return False instead of None

@cl.on_message
async def main(message: cl.Message):
    """Process user messages and generate responses"""
    # Get the thread ID from the session
    thread_id = cl.user_session.get("thread_id")
    if not thread_id:
        await cl.ErrorMessage(content="Chat session not initialized properly. Please refresh.").send()
        return

    try:
        # Process any file attachments
        attachments = await process_files([el for el in message.elements if el.path])

        # Get the current assistant
        assistant = await get_assistant()

        # Add user message to the thread
        await async_openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.content,
            attachments=attachments,
        )

        # Stream the assistant's response
        async with async_openai_client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant.id,
            event_handler=EventHandler(assistant_name=assistant.name),
        ) as stream:
            await stream.until_done()

    except Exception as e:
        await cl.ErrorMessage(content=f"Error processing message: {str(e)}").send()
