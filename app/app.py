import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.azure_blob import AzureBlobStorageClient
from openai import OpenAI
from fastapi import Request, Response
from sqlalchemy import text
from settings import get_db, Config
import io
from typing import Any, Dict, Union

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

# AzureBlobStorageClientのget_read_urlとupload_fileメソッドをモンキーパッチで上書き
original_get_read_url = AzureBlobStorageClient.get_read_url
original_upload_file = AzureBlobStorageClient.upload_file

async def patched_get_read_url(self, object_key: str) -> str:
    """モンキーパッチ版のURL取得メソッド - Azuriteエミュレータに対応"""
    # Azuriteエミュレータ環境の場合は直接URLを返す
    if "devstoreaccount1" in self.storage_account:
        # ローカルAzuriteエミュレータ - ブラウザからアクセス可能なURL
        return f"http://localhost:10000/{self.storage_account}/{self.container_name}/{object_key}"

    # 本番環境では元のメソッドを使用（SASトークン付きURLを生成）
    return await original_get_read_url(self, object_key)

async def patched_upload_file(
    self, object_key: str, data: Union[bytes, io.BytesIO], mime: str, overwrite: bool = False
) -> Dict[str, Any]:
    """モンキーパッチ版のアップロードメソッド - object_keyとurlを追加"""
    try:
        # 元のupload_file処理を呼び出す
        result = await original_upload_file(self, object_key, data, mime, overwrite)

        # 重要: object_keyとurlを追加
        result["object_key"] = object_key

        # 環境に応じたURLを生成
        if "devstoreaccount1" in self.storage_account:
            # 開発環境: ブラウザからアクセス可能なURL
            result["url"] = f"http://localhost:10000/{self.storage_account}/{self.container_name}/{object_key}"
        else:
            # 本番環境: get_read_urlメソッドからURLを取得
            result["url"] = await self.get_read_url(object_key)

        return result
    except Exception as e:
        # 例外をそのままraiseして元のコードと同じ振る舞いにする
        raise Exception(f"Failed to upload file to Azure Blob Storage: {e!s}")

# モンキーパッチ適用
BlobServiceClient.from_connection_string = patched_from_connection_string
AzureBlobStorageClient.get_read_url = patched_get_read_url
AzureBlobStorageClient.upload_file = patched_upload_file

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
        return False  # Fixed return type issue: return False instead of None
