# ==============================================================================
# Unified Project Dash Container (Web Service & Ingestion Sync Worker)
# ==============================================================================
FROM python:3.13-slim

WORKDIR /app

# 1. Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the full project (frontend SPA, backend REST server, scripts, assets, prompts)
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH="/app"
ENV DEFAULT_PROJECTS="monaro"

EXPOSE 8080

# Default command runs the unified Python HTTP server
CMD ["python", "server.py"]
