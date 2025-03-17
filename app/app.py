import os
import chainlit as cl
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@cl.on_chat_start
async def start():
    """チャットセッション開始時に実行される関数"""
    cl.user_session.set(
        "messages",
        [{"role": "system", "content": "あなたは親切なAIアシスタントです。"}]
    )
    await cl.Message(content="こんにちは！何かお手伝いできることはありますか？").send()

@cl.on_message
async def main(message: cl.Message):
    """ユーザーメッセージを受け取った時に実行される関数"""
    # セッションから今までのメッセージ履歴を取得
    messages = cl.user_session.get("messages")

    # ユーザーの新しいメッセージを追加
    messages.append({"role": "user", "content": message.content})

    # OpenAI APIを使用してレスポンスを生成
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )

    # アシスタントの応答をメッセージ履歴に追加
    assistant_message = response.choices[0].message
    messages.append({"role": "assistant", "content": assistant_message.content})

    # 更新したメッセージ履歴をセッションに保存
    cl.user_session.set("messages", messages)

    # 生成されたレスポンスを送信
    await cl.Message(content=assistant_message.content).send()
