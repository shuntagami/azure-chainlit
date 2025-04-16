FROM python:3.13-slim

WORKDIR /workspace

# Copy only necessary files first for better layer caching
COPY pyproject.toml poetry.lock ./
COPY sshd_config /etc/ssh/
COPY entrypoint.sh ./
RUN chmod u+x ./entrypoint.sh

# Install system dependencies and clean up in the same layer to reduce image size
RUN apt-get update \
  && apt-get install -y --no-install-recommends dialog openssh-server \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && echo "root:Docker!" | chpasswd

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry \
  && poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --only main --no-root \
  && pip cache purge

# Copy application code after installing dependencies
COPY . .

# Expose ports for the app and SSH
EXPOSE 8000 2222

# Set healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Use our entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
