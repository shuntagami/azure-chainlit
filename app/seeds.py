import argparse
from settings import get_db, Base, engine
from models import User
import logging
from datetime import datetime

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

def seed_user(identifier):
    """
    指定されたメールアドレスとパスワードでユーザーを作成または更新します
    """
    db = next(get_db())

    try:
        # ユーザーが存在するか確認
        user = db.query(User).filter(User.identifier == identifier).first()

        # ユーザーのメタデータを設定
        metadata = {
            "name": "Default User",
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "preferences": {
                "theme": "light",
                "language": "ja"
            }
        }

        if user:
            logger.info(f"既存ユーザー '{identifier}' を更新します")
            user.metadata_ = metadata
        else:
            logger.info(f"新規ユーザー '{identifier}' を作成します")
            user = User(
                identifier=identifier,
                metadata_=metadata,
                createdAt=datetime.now().isoformat()
            )
            db.add(user)

        # 変更をコミット
        db.commit()
        logger.info(f"ユーザー '{identifier}' の設定が完了しました")

        return user
    except Exception as e:
        db.rollback()
        logger.error(f"ユーザー '{identifier}' の作成/更新中にエラーが発生しました: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='データベースのシード処理を実行します')
    parser.add_argument('--identifier', default="shuntagami23@gmail.com", help='ユーザーのメールアドレス')

    args = parser.parse_args()

    # データベースの初期化
    setup_database()

    # デフォルトユーザーの作成
    seed_user(args.identifier)

    logger.info("シード処理が完了しました")

if __name__ == "__main__":
    main()
