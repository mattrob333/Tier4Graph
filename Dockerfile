FROM python:3.11-slim

WORKDIR /app

# Copy backend only
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Railway provides PORT env var
ENV PORT=8000
EXPOSE $PORT

# Start server (shell form to expand $PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
