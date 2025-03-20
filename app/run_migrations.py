#!/usr/bin/env python
import os
import sys
import logging
import time
from alembic import command
from alembic.config import Config

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """データベースマイグレーションを実行する"""
    try:
        # alembic.iniファイルのパスを取得 (Dockerコンテナ内は /app ディレクトリ)
        alembic_ini_path = "alembic.ini"  # 既にcurrent working directoryが/appになっているため

        if not os.path.exists(alembic_ini_path):
            logger.error(f"alembic.ini ファイルが見つかりません: {alembic_ini_path}")
            return False

        # AlembicのConfigオブジェクトを作成
        alembic_cfg = Config(alembic_ini_path)

        # 現在のマイグレーションの状態を表示
        logger.info("現在のマイグレーション状態を確認中...")
        try:
            command.current(alembic_cfg)
        except Exception as e:
            logger.error(f"マイグレーション状態チェック中に例外が発生: {e}")
            logger.error(f"例外の詳細: {str(e.__class__.__name__)}: {str(e)}")
            raise

        # マイグレーションを実行
        logger.info("マイグレーションを実行中...")
        command.upgrade(alembic_cfg, "head")

        logger.info("マイグレーション完了")
        return True

    except Exception as e:
        logger.error(f"マイグレーション実行中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    # DBが起動するまで少し待機
    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        logger.info(f"マイグレーション実行を試行中... ({retry_count + 1}/{max_retries})")
        if run_migrations():
            sys.exit(0)

        retry_count += 1
        logger.info(f"リトライまで10秒待機...")
        time.sleep(10)

    logger.error("マイグレーションの実行に失敗しました。最大リトライ回数に達しました。")
    sys.exit(1)
