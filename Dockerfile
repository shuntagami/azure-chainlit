FROM python:3.13-slim

WORKDIR /app

# Poetryのインストール
RUN pip install poetry

# Poetryの設定: 仮想環境を作成しない
RUN poetry config virtualenvs.create false

# 依存関係ファイルのコピーとインストール
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --only main --no-root

# アプリケーションファイルのコピー
COPY app/ ./

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0"]
