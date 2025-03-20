import os
import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.azure_blob import AzureBlobStorageClient
from openai import OpenAI
from fastapi import Request, Response
from settings import get_db
from sqlalchemy import text

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")

# モンキーパッチの適用
from azure.storage.blob.aio import BlobServiceClient
original_from_connection_string = BlobServiceClient.from_connection_string

def patched_from_connection_string(connection_string, **kwargs):
    # Azuriteエミュレーター向けに接続文字列を変更
    if "devstoreaccount1" in connection_string:
        # ここでHTTPSからHTTPに変更
        connection_string = connection_string.replace("DefaultEndpointsProtocol=https", "DefaultEndpointsProtocol=http")
        # エンドポイントを追加
        if "EndpointSuffix" in connection_string:
            connection_string = connection_string.replace("EndpointSuffix=core.windows.net", "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1")
        else:
            connection_string += ";BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1"

    return original_from_connection_string(connection_string, **kwargs)

# モンキーパッチ適用
BlobServiceClient.from_connection_string = patched_from_connection_string

DB_HOST = os.getenv("APP_DATABASE_HOST")
DB_USERNAME = os.getenv("APP_DATABASE_USERNAME")
DB_PASSWORD = os.getenv("APP_DATABASE_PASSWORD")
DB_NAME = os.getenv("APP_DATABASE_NAME")
DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# OpenAI クライアントの初期化
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
)

conn_string = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

storage_client = AzureBlobStorageClient(
    container_name=BLOB_CONTAINER_NAME,
    storage_account=AZURE_STORAGE_ACCOUNT,
    storage_key=AZURE_STORAGE_KEY,
)
cl_data._data_layer = SQLAlchemyDataLayer(conninfo=conn_string, storage_provider=storage_client, ssl_require=False)

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
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )

    assistant_message = response.choices[0].message
    messages.append({"role": "assistant", "content": assistant_message.content})

    # 更新したメッセージ履歴をセッションに保存
    cl.user_session.set("messages", messages)

    # 生成されたレスポンスを送信
    await cl.Message(content=assistant_message.content).send()

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
      return None
