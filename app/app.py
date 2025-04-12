import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.azure_blob import AzureBlobStorageClient
from openai import AsyncAzureOpenAI
from settings import Config, chat_settings
import json

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

# MCP接続ハンドラ
@cl.on_mcp_connect
async def on_mcp_connect(connection, session):
    """MCPサーバーとの接続が確立されたときに呼ばれる"""
    try:
        print(f"MCP接続 {connection.name} が確立されました")
        print(f"接続詳細: {connection.clientType}")

        # 利用可能なツールを取得
        print("ツール一覧を取得中...")
        try:
            result = await session.list_tools()
            print(f"取得したツール一覧: {result}")

            # ツールのメタデータを処理
            tools = [{
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            } for t in result.tools]

            # ツールを後で使用するために保存
            mcp_tools = cl.user_session.get("mcp_tools", {})
            mcp_tools[connection.name] = tools
            cl.user_session.set("mcp_tools", mcp_tools)

            # 接続が確立されたことをユーザーに通知
            await cl.Message(
                content=f"MCP接続 `{connection.name}` が確立されました。利用可能なツール: {', '.join(t['name'] for t in tools)}"
            ).send()
        except Exception as e:
            error_msg = f"ツール一覧の取得中にエラーが発生しました: {str(e)}"
            print(error_msg)
            await cl.Message(content=f"⚠️ {error_msg}").send()
            raise
    except Exception as e:
        error_msg = f"MCP接続処理中に予期しないエラーが発生しました: {str(e)}"
        print(error_msg)
        await cl.Message(content=f"⚠️ {error_msg}").send()
        raise

# MCP切断ハンドラ
@cl.on_mcp_disconnect
async def on_mcp_disconnect(name, session):
    """MCPサーバーとの接続が切断されたときに呼ばれる"""
    print(f"MCP接続 {name} が切断されました")
    await cl.Message(content=f"MCP接続 `{name}` が切断されました").send()

# ツールを実行するためのヘルパー関数
@cl.step(type="tool")
async def call_mcp_tool(tool_name, tool_input, connection_name):
    """MCPツールを実行する"""
    try:
        # MCP接続インスタンスを取得
        mcp_session, _ = cl.context.session.mcp_sessions.get(connection_name)

        # ツールを呼び出し
        result = await mcp_session.call_tool(tool_name, tool_input)

        # CallToolResultオブジェクトを辞書に変換
        if hasattr(result, '__dict__'):
            # オブジェクトを辞書に変換
            result_dict = {}
            for key in result.__dict__:
                if not key.startswith('_'):  # プライベート属性は除外
                    value = getattr(result, key)
                    if hasattr(value, 'to_dict') and callable(value.to_dict):
                        result_dict[key] = value.to_dict()
                    elif hasattr(value, '__dict__'):
                        # ネストされたオブジェクトも変換
                        nested_dict = {}
                        for nested_key in value.__dict__:
                            if not nested_key.startswith('_'):
                                nested_dict[nested_key] = getattr(value, nested_key)
                        result_dict[key] = nested_dict
                    else:
                        result_dict[key] = value
            return result_dict
        # すでに辞書型の場合はそのまま返す
        elif isinstance(result, dict):
            return result
        # 基本的な型（文字列、数値など）の場合もそのまま返す
        elif isinstance(result, (str, int, float, bool, list)) or result is None:
            return result
        # その他の場合は文字列に変換
        else:
            return str(result)
    except Exception as e:
        return {"error": str(e)}

@cl.on_chat_start
async def start():
    """チャットセッション開始時に実行される関数"""
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "あなたは親切なAIアシスタントです。MCP ツールを使用して計算や天気情報を取得することができます。"}]
    )
    await cl.Message(content="こんにちは！何かお手伝いできることはありますか？MCPツールを使って計算や天気情報の取得もできます。").send()

@cl.on_message
async def main(message: cl.Message):
    """ユーザーメッセージを受け取った時に実行される関数"""
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    # MCPツールの情報を取得
    mcp_tools = cl.user_session.get("mcp_tools", {})
    all_tools = []
    for connection_name, tools in mcp_tools.items():
        for tool in tools:
            # ツールにconnection_nameを追加して、後でどのMCP接続を使うか識別できるようにする
            tool_with_connection = tool.copy()
            tool_with_connection["connection_name"] = connection_name
            all_tools.append(tool_with_connection)

    # OpenAI API呼び出し用のツール定義
    openai_tools = [{
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"]
        }
    } for tool in all_tools]

    msg = cl.Message(content="")

    # LLMにリクエストを送信（ツール情報を含む）
    stream = await async_openai_client.chat.completions.create(
        messages=message_history,
        tools=openai_tools if all_tools else None,
        **chat_settings()
    )

    # レスポンスの処理
    tool_calls = []
    response_content = ""

    # アシスタントの応答を格納するために使用
    assistant_message = {"role": "assistant", "content": "", "tool_calls": []}

    async for part in stream:
        if part.choices and len(part.choices) > 0:
            delta = part.choices[0].delta

            # ツール呼び出し情報を収集
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    if tool_call_delta.index is not None:
                        index = tool_call_delta.index

                        # 新しいツール呼び出しの場合、リストを拡張
                        while len(tool_calls) <= index:
                            tool_calls.append({
                                "name": "",
                                "arguments": "",
                                "id": tool_call_delta.id or ""
                            })
                            # 同様にassistant_messageのtool_callsも拡張
                            while len(assistant_message["tool_calls"]) <= index:
                                assistant_message["tool_calls"].append({
                                    "function": {"name": "", "arguments": ""},
                                    "id": tool_call_delta.id or "",
                                    "type": "function"
                                })

                        # 名前とパラメータを更新
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls[index]["name"] += tool_call_delta.function.name
                                assistant_message["tool_calls"][index]["function"]["name"] += tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_calls[index]["arguments"] += tool_call_delta.function.arguments
                                assistant_message["tool_calls"][index]["function"]["arguments"] += tool_call_delta.function.arguments

            # 通常のテキストトークンをストリーミング
            if token := delta.content or "":
                response_content += token
                assistant_message["content"] += token
                await msg.stream_token(token)

    # アシスタントの応答をメッセージ履歴に追加
    if response_content or tool_calls:
        message_history.append(assistant_message)

    # ツール呼び出しがある場合、それらを実行
    if tool_calls:
        for i, tool_call in enumerate(tool_calls):
            try:
                # ツール名とパラメータを取得
                tool_name = tool_call["name"]
                tool_arguments = tool_call["arguments"]

                # 引数をJSONとしてパース
                tool_input = json.loads(tool_arguments)

                # このツールに対応するMCP接続を見つける
                connection_name = None
                for tool in all_tools:
                    if tool["name"] == tool_name:
                        connection_name = tool["connection_name"]
                        break

                if connection_name:
                    # ツールを実行
                    tool_response = await call_mcp_tool(tool_name, tool_input, connection_name)

                    # ツールの実行結果を履歴に追加
                    try:
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": json.dumps(tool_response)
                        }
                        message_history.append(tool_message)

                        # ツールの実行結果をメッセージとして表示
                        await cl.Message(
                            content=f"**ツール実行結果 ({tool_name})**: ```json\n{json.dumps(tool_response, indent=2, ensure_ascii=False)}\n```"
                        ).send()
                    except TypeError as json_error:
                        error_msg = f"ツール結果のJSON変換中にエラー: {str(json_error)}"
                        print(f"デバッグ情報: ツール結果タイプ = {type(tool_response)}")
                        # エラーが発生した場合は文字列としてシンプルに表示
                        simple_result = str(tool_response)
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": simple_result
                        }
                        message_history.append(tool_message)
                        await cl.Message(content=f"**ツール実行結果 ({tool_name})**: {simple_result}").send()
            except Exception as e:
                await cl.Message(content=f"ツール実行中にエラーが発生しました: {str(e)}").send()

        # ツールの結果を受け取ったら、最終的な応答を生成
        try:
            # 最終応答用の新しいメッセージを作成
            final_msg = cl.Message(content="")
            await final_msg.send()  # 空のメッセージを先に送信

            final_response_stream = await async_openai_client.chat.completions.create(
                messages=message_history,
                **chat_settings()
            )

            # ストリームからコンテンツを取得し、リアルタイムでストリーミング
            final_content = ""
            async for chunk in final_response_stream:
                if chunk.choices and len(chunk.choices) > 0:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        final_content += token
                        await final_msg.stream_token(token)

            # ストリーミングが完了したらメッセージを更新
            await final_msg.update()

            # 最終応答をメッセージ履歴に追加
            message_history.append({"role": "assistant", "content": final_content})
        except Exception as e:
            error_msg = f"OpenAI APIエラー: {str(e)}"
            print(error_msg)
            await cl.Message(content=f"⚠️ {error_msg}").send()
    else:
        # ツール呼び出しがなかった場合は通常の応答を履歴に追加
        if not assistant_message["content"]:
            # 空の応答の場合は何もしない
            pass
        else:
            # メッセージを更新
            msg.content = assistant_message["content"]
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
