import asyncio

# This file is now just a wrapper around the proper assistant service
from app.services.assistant import create_assistant

if __name__ == "__main__":
    asyncio.run(create_assistant())