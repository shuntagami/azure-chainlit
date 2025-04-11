import chainlit as cl
from app.config import config

def auth_callback(username: str, password: str) -> bool | cl.User:
    """
    Authenticates users for Chainlit application.
    
    Args:
        username: User's email address
        password: User's password
        
    Returns:
        cl.User if authentication succeeds, False otherwise
    """
    if (username == config.DEFAULT_ADMIN_EMAIL and 
        password == config.DEFAULT_ADMIN_PASSWORD):
        return cl.User(
            identifier=username,
            metadata={"role": "admin", "provider": "credentials"},
        )
    
    return False