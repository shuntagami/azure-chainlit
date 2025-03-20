FROM python:3.13-slim

WORKDIR /app

# Copy configuration files
COPY sshd_config /etc/ssh/
COPY entrypoint.sh ./

# Install and configure SSH
RUN apt-get update \
    && apt-get install -y --no-install-recommends dialog \
    && apt-get install -y --no-install-recommends openssh-server \
    && echo "root:Docker!" | chpasswd \
    && chmod u+x ./entrypoint.sh

# Poetryのインストール
RUN pip install poetry

# Poetryの設定: 仮想環境を作成しない
RUN poetry config virtualenvs.create false

# 依存関係ファイルのコピーとインストール
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --only main --no-root

# アプリケーションファイルのコピー
COPY app/ ./

# Expose ports for the app and SSH
EXPOSE 8000 2222

# Use our entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
