FROM python:3.11-slim

WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir /app/backend

COPY backend /app/backend
COPY sample-data /app/sample-data
WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
