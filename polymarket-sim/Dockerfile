# Simple Python backend deployment
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web .

# Start FastAPI server
CMD ["sh", "-c", "cd backend && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
