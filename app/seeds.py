import argparse
from settings import get_db, Base, engine
from models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """データベースの初期設定を行います"""
    try:
        # テーブルの作成（存在しない場合）
        logger.info("データベーステーブルを初期化しています...")
        Base.metadata.create_all(engine)
        logger.info("データベースの初期化が完了しました")
    except Exception as e:
        logger.error(f"データベースの初期化中にエラーが発生しました: {e}")
        raise

def seed_user(email, password):
    """
    指定されたメールアドレスとパスワードでユーザーを作成または更新します
    """
    db = next(get_db())

    try:
        # ユーザーが存在するか確認
        user = db.query(User).filter(User.email == email).first()

        if user:
            logger.info(f"既存ユーザー '{email}' を更新します")
        else:
            logger.info(f"新規ユーザー '{email}' を作成します")
            user = User(email=email)
            db.add(user)

        # パスワードの設定
        user.set_password(password)

        # 変更をコミット
        db.commit()
        logger.info(f"ユーザー '{email}' の設定が完了しました")

        return user
    except Exception as e:
        db.rollback()
        logger.error(f"ユーザー '{email}' の作成/更新中にエラーが発生しました: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='データベースのシード処理を実行します')
    parser.add_argument('--email', default="shuntagami23@gmail.com", help='ユーザーのメールアドレス')
    parser.add_argument('--password', default="password123", help='ユーザーのパスワード')

    args = parser.parse_args()

    # データベースの初期化
    setup_database()

    # デフォルトユーザーの作成
    seed_user(args.email, args.password)

    logger.info("シード処理が完了しました")

if __name__ == "__main__":
    main()
