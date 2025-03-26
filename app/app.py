import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.azure_blob import AzureBlobStorageClient
from openai import OpenAI
from fastapi import Request, Response
from sqlalchemy import text
from settings import get_db, Config
import asyncio

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
openai_client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
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
    # アシスタントの作成
    assistant = await openai_client.beta.assistants.create(
        name="AIアシスタント",
        instructions="あなたは親切なAIアシスタントです。",
        model="gpt-3.5-turbo",
        tools=[{"type": "code_interpreter"}]
    )

    # スレッドの作成
    thread = await openai_client.beta.threads.create()

    # セッションにアシスタントとスレッドの情報を保存
    cl.user_session.set("assistant", assistant)
    cl.user_session.set("thread", thread)

    await cl.Message(content="こんにちは！何かお手伝いできることはありますか？").send()

@cl.on_message
async def main(message: cl.Message):
    """ユーザーメッセージを受け取った時に実行される関数"""
    # セッションからアシスタントとスレッドの情報を取得
    assistant = cl.user_session.get("assistant")
    thread = cl.user_session.get("thread")

    # メッセージをスレッドに追加
    await openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message.content
    )

    # アシスタントを実行
    run = await openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # 実行が完了するまで待機
    while True:
        run = await openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == "completed":
            break
        elif run.status == "failed":
            raise Exception("Assistant run failed")
        await asyncio.sleep(1)

    # 最新のメッセージを取得
    messages = await openai_client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # アシスタントの最新のメッセージを送信
    for msg in messages.data:
        if msg.role == "assistant":
            await cl.Message(content=msg.content[0].text.value).send()
            break

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
        return False
