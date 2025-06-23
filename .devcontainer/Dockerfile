# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:0-3.11

# 必要ライブラリ追加 ------------------------▼
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1                                 \
        libgomp1                               \
        libtbb2                                \
        && rm -rf /var/lib/apt/lists/*
#-------------------------------------------▲

WORKDIR /app

# 依存の先読み（キャッシュ用）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
