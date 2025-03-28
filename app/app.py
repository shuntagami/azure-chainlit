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
    assistant = openai_client.beta.assistants.create(
        name="AIアシスタント",
        instructions="""あなたは親切なAIアシスタントです。以下の機能を提供します：
        1. コードの解析と実行
        2. ファイルの内容分析
        3. データの可視化
        4. 問題解決のサポート

        ユーザーからの質問に対して、具体的な例を示しながら説明してください。
        コードを実行する際は、実行結果も含めて説明してください。""",
        model="gpt-3.5-turbo",
        tools=[
            {"type": "code_interpreter"},
            {"type": "function", "function": {"name": "upload_file", "description": "ファイルをアップロードして分析します"}},
            {"type": "function", "function": {"name": "run_code", "description": "Pythonコードを実行します"}},
            {"type": "function", "function": {"name": "visualize", "description": "データをグラフ化します"}}
        ]
    )

    # スレッドの作成
    thread = openai_client.beta.threads.create()

    # セッションにアシスタントとスレッドの情報を保存
    cl.user_session.set("assistant", assistant)
    cl.user_session.set("thread", thread)

    # 初期メッセージの送信
    await cl.Message(
        content="""こんにちは！私は以下の機能を提供するAIアシスタントです：
        1. コードの解析と実行
        2. ファイルの内容分析
        3. データの可視化
        4. 問題解決のサポート

        どのようなお手伝いができますか？""",
        actions=[
            cl.Action(name="upload_file", value="ファイルをアップロード", description="ファイルをアップロードして分析します", payload={"action": "upload_file"}),
            cl.Action(name="run_code", value="コードを実行", description="Pythonコードを実行します", payload={"action": "run_code"}),
            cl.Action(name="visualize", value="データを可視化", description="データをグラフ化します", payload={"action": "visualize"})
        ]
    ).send()

@cl.action_callback("upload_file")
async def on_upload_file(action):
    """ファイルアップロード時の処理"""
    files = await cl.AskFileMessage(
        content="分析したいファイルをアップロードしてください。",
        accept=["text/plain", "application/json", "text/csv", "application/pdf"]
    ).send()

    if files:
        for file in files:
            # ファイルの内容を取得
            content = file.content.decode('utf-8')

            # ファイルをアシスタントにアップロード
            file_object = await openai_client.files.create(
                file=content.encode('utf-8'),
                purpose='assistants'
            )

            # アシスタントにファイルを関連付け
            assistant = cl.user_session.get("assistant")
            await openai_client.beta.assistants.files.create(
                assistant_id=assistant.id,
                file_id=file_object.id
            )

            await cl.Message(content=f"ファイル '{file.name}' をアップロードしました。内容を分析します。").send()

@cl.action_callback("run_code")
async def on_run_code(action):
    """コード実行時の処理"""
    code = await cl.AskUserMessage(
        content="実行したいPythonコードを入力してください。",
        timeout=180
    ).send()

    if code:
        # コードをスレッドに追加
        thread = cl.user_session.get("thread")
        openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"以下のPythonコードを実行してください：\n```python\n{code.content}\n```"
        )

        # アシスタントを実行
        assistant = cl.user_session.get("assistant")
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # 実行が完了するまで待機
        while True:
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            elif run.status == "failed":
                raise Exception("Assistant run failed")
            await asyncio.sleep(1)

        # 実行結果を取得
        messages = openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )

        # アシスタントの最新のメッセージを送信
        for msg in messages.data:
            if msg.role == "assistant":
                await cl.Message(content=msg.content[0].text.value).send()
                break

@cl.action_callback("visualize")
async def on_visualize(action):
    """データ可視化時の処理"""
    data = await cl.AskUserMessage(
        content="可視化したいデータを入力してください（CSV形式またはJSON形式）",
        timeout=180
    ).send()

    if data:
        # データをスレッドに追加
        thread = cl.user_session.get("thread")
        openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"以下のデータを可視化してください：\n{data.content}"
        )

        # アシスタントを実行
        assistant = cl.user_session.get("assistant")
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # 実行が完了するまで待機
        while True:
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            elif run.status == "failed":
                raise Exception("Assistant run failed")
            await asyncio.sleep(1)

        # 実行結果を取得
        messages = await openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )

        # アシスタントの最新のメッセージを送信
        for msg in messages.data:
            if msg.role == "assistant":
                await cl.Message(content=msg.content[0].text.value).send()
                break

@cl.on_message
async def main(message: cl.Message):
    """ユーザーメッセージを受け取った時に実行される関数"""
    # セッションからアシスタントとスレッドの情報を取得
    assistant = cl.user_session.get("assistant")
    thread = cl.user_session.get("thread")

    # メッセージをスレッドに追加
    openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message.content
    )

    # アシスタントを実行
    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # 実行が完了するまで待機
    while True:
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == "completed":
            break
        elif run.status == "failed":
            raise Exception("Assistant run failed")
        await asyncio.sleep(1)

    # 最新のメッセージを取得
    messages = openai_client.beta.threads.messages.list(
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
