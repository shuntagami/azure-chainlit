import os
import chainlit as cl
from fastapi import Request, Response
from openai import OpenAI
from settings import get_db
from sqlalchemy import text
from auth import setup_auth_hooks, require_auth
from models import User

# OpenAI クライアントの初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# chainlit.server から FastAPI アプリを取得
from chainlit.server import app

# Health check middleware
@app.middleware("http")
async def health_check_middleware(request: Request, call_next):
    if request.url.path == "/api/health":
        try:
            # Get database session
            db = next(get_db())
            # Execute simple query to check database connection
            db.execute(text("SELECT 1"))
            return Response(content='{"status": "ok", "database": "connected"}', media_type="application/json")
        except Exception as e:
            error_message = str(e)
            return Response(content=f'{{"status": "error", "database": "disconnected", "error": "{error_message}"}}',
                           media_type="application/json",
                           status_code=500)
    return await call_next(request)

# 認証フックの設定（auth.pyのon_chat_startフックも含む）
setup_auth_hooks()

# メッセージ処理のフック
@cl.on_message
@require_auth
async def main(message: cl.Message):
    """ユーザーメッセージを受け取った時に実行される関数"""
    # メッセージ履歴の初期化（初回メッセージの場合）
    if not cl.user_session.get("messages"):
        cl.user_session.set(
            "messages",
            [{"role": "system", "content": "あなたは親切なAIアシスタントです。"}]
        )

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
