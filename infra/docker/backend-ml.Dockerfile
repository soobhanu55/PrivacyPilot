FROM python:3.11-slim

WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir "/app/backend[ml]"

COPY backend /app/backend
COPY sample-data /app/sample-data
WORKDIR /app/backend

CMD ["celery", "-A", "app.worker.celery_app", "worker", "--loglevel=INFO", "--queues=ml"]
