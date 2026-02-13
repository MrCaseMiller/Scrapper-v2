# Production-ready Python backend deployment with full simulation engine
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install all Python dependencies
# First, copy web backend requirements
COPY web/requirements.txt ./web-requirements.txt
# Then, copy simulation engine requirements
COPY requirements.txt ./sim-requirements.txt

# Install all dependencies
RUN pip install --no-cache-dir -r web-requirements.txt && \
    pip install --no-cache-dir -r sim-requirements.txt

# Copy simulation engine source code (needed by bot_manager)
COPY src ./src

# Copy web application code
COPY web ./web

# Copy config file if exists
COPY config.yaml ./config.yaml 2>/dev/null || echo "No config.yaml found, using defaults"

# Set Python path to include both /app and /app/web for imports
ENV PYTHONPATH=/app:/app/web:$PYTHONPATH

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Start FastAPI server
CMD ["sh", "-c", "uvicorn web.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
