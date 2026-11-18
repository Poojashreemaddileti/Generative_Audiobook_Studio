
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    FLASK_DEBUG=0 \
    HF_HOME=/data/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY . /app

RUN mkdir -p /data /app/data

EXPOSE 10000

CMD ["sh", "-c", "exec gunicorn --chdir /app/backend --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 600 app:app"]
