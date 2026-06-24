# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装系统依赖（uvicorn[standard] 编译 + curl 用于健康检查）
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 API 代码与数据（保持与本地开发一致的目录结构）
COPY apps/api/pyproject.toml apps/api/README.md ./apps/api/
COPY apps/api/app ./apps/api/app
COPY apps/api/alembic.ini ./apps/api/
COPY apps/api/alembic ./apps/api/alembic
COPY data ./data

# 安装依赖
RUN pip install ./apps/api

# 数据库持久化目录
RUN mkdir -p /app/var
VOLUME /app/var

WORKDIR /app/apps/api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# 启动前运行迁移并播种数据，然后启动 uvicorn
CMD ["sh", "-c", "alembic upgrade head && python -m app.scripts.seed_catalog && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
