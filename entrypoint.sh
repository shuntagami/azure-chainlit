#!/bin/sh
set -e

# SSHサービスを開始
service ssh start

# データベースマイグレーションを実行
echo "データベースマイグレーションを実行中..."
# 以前: cd /workspace/app と app ディレクトリ内で実行していた
# 修正: workspace ディレクトリからモジュールとして実行
cd /workspace
python -m app.run_migrations
echo "マイグレーション処理が完了しました"

# アプリケーションを起動
echo "アプリケーションを起動中..."
exec chainlit run app.py --host 0.0.0.0 --port 8000
