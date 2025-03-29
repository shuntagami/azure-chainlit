import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.azure_blob import AzureBlobStorageClient
from openai import AsyncAzureOpenAI
from fastapi import Request, Response
from sqlalchemy import text
from settings import get_db, Config, chat_settings

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
            connection_string = connection_string.replace("EndpointSuffix=core.windows.net", "BlobEndpoint=http://azurite:10000/devstoreaccount1")
        else:
            connection_string += ";BlobEndpoint=http://azurite:10000/devstoreaccount1"

    return original_from_connection_string(connection_string, **kwargs)

# モンキーパッチ適用
BlobServiceClient.from_connection_string = patched_from_connection_string

# OpenAI クライアントの初期化
async_openai_client = AsyncAzureOpenAI(
    api_key=Config.OPENAI_API_KEY,
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    api_version=Config.OPENAI_API_VERSION,
)

storage_client = AzureBlobStorageClient(
    container_name=Config.BLOB_CONTAINER_NAME,
    storage_account=Config.AZURE_STORAGE_ACCOUNT,
    storage_key=Config.AZURE_STORAGE_KEY,
)
cl_data._data_layer = SQLAlchemyDataLayer(conninfo=Config.ASYNC_DATABASE_URL, storage_provider=storage_client)

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
        "message_history",
        [{"role": "system", "content": "あなたは親切なAIアシスタントです。"}]
    )
    await cl.Message(content="こんにちは！何かお手伝いできることはありますか？").send()

@cl.on_message
async def main(message: cl.Message):
    """ユーザーメッセージを受け取った時に実行される関数"""
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")

    stream = await async_openai_client.chat.completions.create(
        messages=message_history,
        **chat_settings()
    )

    async for part in stream:
        if part.choices and len(part.choices) > 0:
            if token := part.choices[0].delta.content or "":
                await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()

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
