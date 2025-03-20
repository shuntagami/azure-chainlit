#!/bin/sh
set -e

# SSHサービスを開始
service ssh start

# データベースマイグレーションを実行
echo "データベースマイグレーションを実行中..."
python /app/run_migrations.py
echo "マイグレーション処理が完了しました"

# アプリケーションを起動
echo "アプリケーションを起動中..."
exec chainlit run app.py --host 0.0.0.0 --port 8000
