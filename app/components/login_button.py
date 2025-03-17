import chainlit as cl
from chainlit.element import Element

def create_login_button():
    """Create a login button element"""
    return cl.Button(
        name="login",
        label="Login with Google",
        url="/auth/login",
        position="top-right"
    )

def create_logout_button(user_info):
    """Create a logout button element"""
    return cl.Button(
        name="logout",
        label=f"Logout ({user_info.get('name', user_info.get('email', 'User'))})",
        url="/auth/logout",
        position="top-right"
    )

def create_user_avatar(user_info):
    """Create a user avatar element"""
    if not user_info.get("picture"):
        return None

    return cl.Image(
        name="user-avatar",
        display="inline",
        size="small",
        url=user_info.get("picture"),
        position="top-right"
    )
