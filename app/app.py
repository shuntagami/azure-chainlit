import chainlit as cl

@cl.on_message
async def main(message: str):
    # 単純なエコー機能
    await cl.Message(
        content=f"あなたのメッセージ: {message}",
    ).send()
