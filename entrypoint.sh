#!/bin/sh
set -e

# SSHサービスを開始
service ssh start

cd /workspace/app

# アプリケーションを起動
echo "アプリケーションを起動中..."
exec chainlit run app.py --host 0.0.0.0 --port 8000
