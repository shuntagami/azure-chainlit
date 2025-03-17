import chainlit as cl
from typing import List
from database import Thread

def create_chat_history_sidebar(threads: List[Thread], current_thread_id: str = None):
    """Create a sidebar with chat history"""
    elements = []

    # Create header
    elements.append(
        cl.Text(name="history-header", content="Chat History", display="inline")
    )

    # Create new chat button
    elements.append(
        cl.Button(
            name="new-chat",
            label="New Chat",
            url="/?new=true",
            position="bottom"
        )
    )

    # Add thread items
    for thread in threads:
        thread_id = str(thread.id)
        is_current = current_thread_id and thread_id == current_thread_id

        elements.append(
            cl.Button(
                name=f"thread-{thread_id}",
                label=thread.name,
                url=f"/?thread={thread_id}",
                position="bottom",
                color="primary" if is_current else "secondary"
            )
        )

    return elements
