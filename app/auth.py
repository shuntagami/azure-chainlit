import chainlit as cl
from settings import get_db
from models import User

async def authenticate_user(email, password):
    """ユーザー認証を行い、成功した場合はUserオブジェクトを返す"""
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()

    if not user or not user.check_password(password):
        return None

    return user

def require_auth(f):
    """認証が必要なChainlit関数用のデコレータ"""
    async def wrapper(*args, **kwargs):
        if not cl.user_session.get("authenticated", False):
            return await cl.Message(content="認証が必要です。ログインしてください。").send()
        return await f(*args, **kwargs)
    return wrapper

def setup_auth_hooks():
    """認証に必要なChainlitフックを設定する"""

    @cl.password_auth_callback
    async def auth_callback(email: str, password: str):
        """パスワード認証のコールバック"""
        user = await authenticate_user(email, password)
        if not user:
            return None

        return cl.User(
            identifier=user.email,
            metadata={"user_id": str(user.id)}
        )

    @cl.on_chat_start
    async def on_chat_start():
        """チャット開始時に認証状態を確認"""
        # ユーザー情報の取得
        user_info = cl.user_session.get("user")

        if user_info:
            # 認証済みとしてマーク
            cl.user_session.set("authenticated", True)

            # 歓迎メッセージを送信
            await cl.Message(content=f"こんにちは、{user_info.identifier}さん！何かお手伝いできることはありますか？").send()
        else:
            # 未認証としてマーク
            cl.user_session.set("authenticated", False)
            await cl.Message(content="認証されていません。ログインしてください。").send()
