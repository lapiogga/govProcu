# GovProcu MCP Server
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/app

# 의존성 먼저 (캐시 활용)
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install . && rm pyproject.toml

# 앱 코드
COPY app ./app

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
