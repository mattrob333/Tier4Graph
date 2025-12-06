FROM python:3.11-slim

WORKDIR /app

# Copy backend only
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Railway injects PORT at runtime, default to 8000 for local
ENV PORT=${PORT:-8000}

# Start server - use sh -c to expand $PORT at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
